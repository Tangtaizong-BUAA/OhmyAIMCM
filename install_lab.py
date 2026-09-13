"""Build, verify and install a complete namespaced local suite without overwriting skills."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

LAB = Path(__file__).resolve().parents[1]
SOURCE = LAB / 'candidate/skills'
IGNORE = {'__pycache__', '.DS_Store', '.pytest_cache', '.ruff_cache'}
TEXT = {'.md', '.py', '.json', '.yaml', '.yml'}
NAMESPACES = ('cumcm-lab', 'lab-pro', 'lab-ultra')
DISPLAY_NAMES = {'lab-pro': 'lab-Pro', 'lab-ultra': 'Lab-ultra'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def files(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if any(part in IGNORE for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError(f'symlink not allowed: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def names(namespace='cumcm-lab'):
    if namespace not in NAMESPACES:
        raise ValueError('unsupported suite namespace')
    old = ('cumcm cumcm-intake cumcm-modeling cumcm-compute cumcm-writing cumcm-review '
           'cumcm-references cumcm-sciverse cumcm-typesetter scientific-figure-maker '
           'academic-plotting agent-figure-gallery draw-io evaluate-diagram figure-generation '
           'figure-spec generate-diagram generate-plot scientific-visualization scipilot-figure-skill').split()
    return {n: namespace + (n[5:] if n.startswith('cumcm') else '-' + n) for n in old}


def transform(text, mapping):
    pattern = re.compile(r'(?<![A-Za-z0-9_-])(' + '|'.join(map(re.escape, sorted(mapping, key=len, reverse=True))) + r')(?![A-Za-z0-9_-])')
    # Upstream URLs identify original sources, not installed module names.
    return ''.join(s if re.match(r'https?://', s) else pattern.sub(lambda m: mapping[m[0]], s)
                   for s in re.split(r'(https?://[^\s<>\]\)"\x27]+)', text))


def build(output, namespace='cumcm-lab'):
    mapping = names(namespace)
    source = files(SOURCE)
    catalog_key = 'cumcm-references/assets/catalog.json'
    original_catalog = json.loads(source[catalog_key])
    for entry in original_catalog['entries']:
        for field, hash_field in [('path', 'sha256'), ('license_path', 'license_sha256')]:
            if field in entry and digest(source[entry[field]]) != entry[hash_field]:
                raise ValueError(f'source reference drift: {entry["id"]}')
    payload = {}
    for key, data in source.items():
        module, relative = key.split('/', 1)
        if module not in mapping:
            raise ValueError(f'undeclared module: {module}')
        if Path(key).suffix in TEXT:
            data = transform(data.decode('utf-8'), mapping).encode('utf-8')
        if relative == 'SKILL.md':
            content = data.decode('utf-8')
            content = content.replace('description: ', 'description: Experimental CUMCM lab suite. ', 1)
            front, body = content.split('\n---\n', 1)
            content = front + f'\n---\n\nThis is the isolated `{namespace}` edition. Use only the sibling `{namespace}-*`\nmodules linked here; do not substitute stable or vendor skills.\n' + body
            data = content.encode('utf-8')
        if relative == 'agents/openai.yaml':
            if namespace in DISPLAY_NAMES:
                content = data.decode('utf-8')
                label = DISPLAY_NAMES[namespace]
                display = label if module == 'cumcm' else '[' + label + '] ' + module
                content = re.sub(r'(?m)^(\s*display_name:) .*$',
                                 lambda m: m[1] + ' ' + json.dumps(display), content, count=1)
                data = content.encode('utf-8')
            else:
                data = data.replace(b'display_name: "', b'display_name: "[LAB] ', 1)
        payload[mapping[module] + '/' + relative] = data
    catalog_path = mapping['cumcm-references'] + '/assets/catalog.json'
    catalog = json.loads(payload[catalog_path])
    for entry in catalog['entries']:
        for field, hash_field in [('path', 'sha256'), ('license_path', 'license_sha256')]:
            if field in entry:
                entry[hash_field] = digest(payload[entry[field]])
    payload[catalog_path] = (json.dumps(catalog, ensure_ascii=False, indent=2) + '\n').encode()
    source_hashes = {k: digest(v) for k, v in source.items()}
    source_tree_sha256 = digest(json.dumps(source_hashes, sort_keys=True,
                                          separators=(',', ':')).encode('utf-8'))
    manifest = {'schema': 'cumcm-lab-install/1', 'namespace': namespace,
                'candidate_revision': 'source-sha256:' + source_tree_sha256,
                'source_tree_sha256': source_tree_sha256,
                'mapping': mapping, 'source_files': source_hashes,
                'files': {k: digest(v) for k, v in payload.items()},
                'builder_sha256': digest(Path(__file__).read_bytes()),
                'scope': 'Complete skill resources; external runtimes and MCP credentials not bundled'}
    output.mkdir(parents=True, exist_ok=False)
    for key, data in payload.items():
        path = output / 'skills' / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod((SOURCE / next(k for k in source if k.split('/', 1)[1] == key.split('/', 1)[1] and mapping[k.split('/', 1)[0]] == key.split('/', 1)[0])).stat().st_mode & 0o777)
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    verify(output, output / 'skills')
    return manifest


def verify(bundle, destination):
    manifest = json.loads((bundle / 'manifest.json').read_text())
    mapping = manifest['mapping']
    if mapping != names(manifest.get('namespace', 'cumcm-lab')):
        raise ValueError('incomplete or unexpected module mapping')
    actual = {}
    for module in mapping.values():
        if (destination / module).is_symlink():
            raise ValueError('module symlink not allowed')
        actual.update({module + '/' + k: digest(v) for k, v in files(destination / module).items()})
    if actual != manifest['files']:
        raise ValueError('installed file set or hashes differ from bundle')
    return manifest


def install(bundle, destination):
    manifest = verify(bundle, bundle / 'skills')
    modules = list(manifest['mapping'].values())
    if any((destination / n).exists() or (destination / n).is_symlink() for n in modules):
        raise ValueError('destination exists; refuse merge/overwrite; verify an existing installation instead')
    destination.mkdir(parents=True, exist_ok=True)
    # Stage outside the discovery tree; validate before publishing any module.
    with tempfile.TemporaryDirectory(prefix='cumcm-lab-stage-', dir=destination.parent) as tmp:
        stage = Path(tmp)
        for module in modules:
            shutil.copytree(bundle / 'skills' / module, stage / module)
        verify(bundle, stage)
        for module in modules:
            if (destination / module).exists() or (destination / module).is_symlink():
                raise ValueError('destination changed during installation')
            (stage / module).rename(destination / module)
    verify(bundle, destination)
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['build', 'install', 'verify'])
    p.add_argument('--bundle', required=True, type=Path)
    p.add_argument('--dest', type=Path)
    p.add_argument('--namespace', choices=NAMESPACES, default='cumcm-lab',
                   help='Build namespace; install/verify use the bound manifest namespace')
    args = p.parse_args()
    if args.command != 'build' and args.dest is None:
        p.error('--dest is required')
    result = build(args.bundle, args.namespace) if args.command == 'build' else (install if args.command == 'install' else verify)(args.bundle, args.dest)
    print(json.dumps({'ok': True, 'command': args.command, 'modules': len(result['mapping']),
                      'files': len(result['files']), 'bundle': str(args.bundle), 'dest': str(args.dest)}))


if __name__ == '__main__':
    main()
