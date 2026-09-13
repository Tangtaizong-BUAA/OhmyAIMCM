"""Build, install and verify the complete OhmyAIMCM Skill suite."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'skills'
NAMESPACE = 'OhmyAIMCM'
IGNORE = {'__pycache__', '.DS_Store', '.pytest_cache', '.ruff_cache'}
SUFFIXES = ('', '-intake', '-modeling', '-compute', '-writing', '-review',
            '-references', '-sciverse', '-typesetter', '-scientific-figure-maker',
            '-academic-plotting', '-agent-figure-gallery', '-draw-io',
            '-evaluate-diagram', '-figure-generation', '-figure-spec',
            '-generate-diagram', '-generate-plot', '-scientific-visualization',
            '-scipilot-figure-skill')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def names():
    return {NAMESPACE + suffix: NAMESPACE + suffix for suffix in SUFFIXES}


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


def verify(bundle, destination):
    manifest = json.loads((bundle / 'manifest.json').read_text())
    if manifest.get('namespace') != NAMESPACE or manifest.get('mapping') != names():
        raise ValueError('incomplete or unexpected module mapping')
    if digest((bundle / 'install.py').read_bytes()) != manifest['builder_sha256']:
        raise ValueError('installer hash differs from manifest')
    actual = {}
    for module in names():
        target = destination / module
        if target.is_symlink() or not target.is_dir():
            raise ValueError(f'module missing or symlink not allowed: {module}')
        actual.update({module + '/' + key: digest(data)
                       for key, data in files(target).items()})
    if actual != manifest['files']:
        raise ValueError('installed file set or hashes differ from bundle')
    return manifest


def build(output):
    """Copy the current, manifest-verified resource set into a new bundle."""
    manifest = verify(ROOT, SOURCE)
    output.mkdir(parents=True, exist_ok=False)
    for module in names():
        shutil.copytree(SOURCE / module, output / 'skills' / module,
                        ignore=shutil.ignore_patterns(*IGNORE))
    shutil.copy2(ROOT / 'install.py', output / 'install.py')
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    verify(output, output / 'skills')
    return manifest


def install(bundle, destination):
    manifest = verify(bundle, bundle / 'skills')
    modules = list(names())
    if any((destination / n).exists() or (destination / n).is_symlink() for n in modules):
        raise ValueError('destination exists; refuse merge/overwrite; verify an existing installation instead')
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='OhmyAIMCM-stage-', dir=destination.parent) as tmp:
        stage = Path(tmp)
        for module in modules:
            shutil.copytree(bundle / 'skills' / module, stage / module,
                            ignore=shutil.ignore_patterns(*IGNORE))
        verify(bundle, stage)
        for module in modules:
            if (destination / module).exists() or (destination / module).is_symlink():
                raise ValueError('destination changed during installation')
            (stage / module).rename(destination / module)
    verify(bundle, destination)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'install', 'verify'])
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--dest', type=Path)
    args = parser.parse_args()
    if args.command != 'build' and args.dest is None:
        parser.error('--dest is required')
    result = (build(args.bundle) if args.command == 'build' else
              (install if args.command == 'install' else verify)(args.bundle, args.dest))
    print(json.dumps({'ok': True, 'command': args.command, 'namespace': NAMESPACE,
                      'modules': len(result['mapping']), 'files': len(result['files'])}))


if __name__ == '__main__':
    main()
