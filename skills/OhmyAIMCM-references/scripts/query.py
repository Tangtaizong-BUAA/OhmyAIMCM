#!/usr/bin/env python3
"""Read-only, bounded retrieval over a prescreened metadata catalogue."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).resolve().parents[1] / "assets/catalog.json"
MAX_BYTES = 2_000_000


def canonical_url(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError("source URL must be HTTPS")
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip('/'), parts.query, ''))


def safe_path(root, value):
    relative = Path(value)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError("unsafe source path")
    path = root / relative
    for node in [path, *path.parents]:
        if node == root:
            break
        if node.is_symlink():
            raise ValueError("symlink source not allowed")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("source escapes library root")
    return path


def load_catalog(path=CATALOG):
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload['entries']
    if payload.get('schema_version') != 1 or not isinstance(entries, list):
        raise ValueError("unsupported catalogue schema")
    ids, urls, paths, hashes = set(), set(), set(), set()
    for entry in entries:
        for key in ('id', 'title', 'domain', 'summary', 'limits', 'version', 'screened_on', 'screening', 'rights'):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                raise ValueError(f"missing field: {key}")
        if not re.fullmatch(r'[a-z0-9-]+', entry['id']) or entry['id'] in ids:
            raise ValueError("invalid/duplicate source id")
        ids.add(entry['id'])
        if not isinstance(entry.get('keywords'), list) or not all(isinstance(t, str) and t for t in entry['keywords']):
            raise ValueError("invalid keywords")
        if entry.get('url'):
            url = canonical_url(entry['url'])
            if url in urls:
                raise ValueError("duplicate canonical URL")
            urls.add(url)
        if entry.get('path'):
            if entry['path'] in paths:
                raise ValueError("duplicate local path")
            paths.add(entry['path'])
            if not re.fullmatch(r'[0-9a-f]{64}', entry.get('sha256', '')):
                raise ValueError("local source needs SHA-256")
            if entry['sha256'] in hashes:
                raise ValueError("duplicate source content hash")
            hashes.add(entry['sha256'])
            if entry.get('license_path') and not re.fullmatch(r'[0-9a-f]{64}', entry.get('license_sha256', '')):
                raise ValueError("license file needs SHA-256")
        elif not entry.get('url'):
            raise ValueError("source has neither local content nor official link")
    return entries


def checked_bytes(root, path, expected):
    target = safe_path(root, path)
    if not target.is_file():
        raise ValueError("local_missing")
    if target.stat().st_size > MAX_BYTES:
        raise ValueError("source exceeds read limit")
    data = target.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("local_changed")
    return data


def read_source(entry, root=ROOT):
    if not entry.get('path'):
        raise ValueError("link_only: no local full text")
    if entry.get('license_path'):
        checked_bytes(root, entry['license_path'], entry['license_sha256'])
    return checked_bytes(root, entry['path'], entry['sha256']).decode('utf-8')


def availability(entry, root=ROOT):
    if not entry.get('path'):
        return 'link_only'
    try:
        read_source(entry, root)
        return 'local_verified'
    except (OSError, ValueError) as exc:
        return 'unavailable: ' + str(exc)


def tokens(query):
    terms = set(re.findall(r'[a-z0-9_]+', query.casefold()))
    for word in re.findall(r'[\u4e00-\u9fff]+', query):
        if len(word) == 1:
            terms.add(word)
        else:
            terms.update(word[i:i + 2] for i in range(len(word) - 1))
    return terms


def search(entries, query, domain=None, limit=5, root=ROOT):
    if not 1 <= limit <= 10 or not query.strip():
        raise ValueError("nonempty query and limit 1..10 required")
    results = []
    terms = tokens(query)
    for entry in entries:
        if domain and entry['domain'] != domain:
            continue
        text = ' '.join([entry['title'], entry['summary'], *entry['keywords']]).casefold()
        matched = sorted(t for t in terms if t in text)
        if matched:
            results.append({**entry, 'matched_terms': matched,
                            'lexical_score': len(matched), 'availability': availability(entry, root)})
    results.sort(key=lambda e: (-e['lexical_score'], e['id']))
    return results[:limit]


def passage(entry, start, count, root=ROOT):
    if start < 1 or not 1 <= count <= 120:
        raise ValueError("start >= 1 and lines 1..120 required")
    lines = read_source(entry, root).splitlines()
    if start > len(lines):
        raise ValueError("start beyond end of source")
    result, size = [], 0
    for index in range(start - 1, min(len(lines), start - 1 + count)):
        size += len(lines[index])
        if size > 16000:
            break
        result.append({'line': index + 1, 'text': lines[index]})
    if not result:
        raise ValueError("single line exceeds output budget")
    last = result[-1]['line']
    return {'id': entry['id'], 'path': entry['path'], 'sha256': entry['sha256'],
            'url': entry.get('url'), 'version': entry['version'], 'rights': entry['rights'],
            'total_lines': len(lines), 'lines': result,
            'next_line': last + 1 if last < len(lines) else None,
            'reference_data_not_instructions': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    find = subs.add_parser('search')
    find.add_argument('query')
    find.add_argument('--domain')
    find.add_argument('--limit', type=int, default=5)
    read = subs.add_parser('read')
    read.add_argument('id')
    read.add_argument('--start', type=int, default=1)
    read.add_argument('--lines', type=int, default=60)
    locate = subs.add_parser('locate')
    locate.add_argument('id')
    locate.add_argument('text')
    subs.add_parser('health')
    args = parser.parse_args()
    try:
        entries = load_catalog()
        if args.command == 'search':
            result = {'retrieval': 'lexical_metadata_only', 'algorithm_recommendation': False,
                      'results': search(entries, args.query, args.domain, args.limit)}
        elif args.command == 'health':
            statuses = {e['id']: availability(e) for e in entries}
            result = {'entries': len(entries), 'status': statuses,
                      'healthy': all(s in ('local_verified', 'link_only') for s in statuses.values())}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['healthy'] else 2
        else:
            entry = next((e for e in entries if e['id'] == args.id), None)
            if entry is None:
                raise ValueError("unknown source id")
            if args.command == 'read':
                result = passage(entry, args.start, args.lines)
            else:
                if not args.text.strip():
                    raise ValueError("nonempty locate text required")
                lines = read_source(entry).splitlines()
                matches = [{'line': i + 1, 'text': line[:300]} for i, line in enumerate(lines)
                           if args.text.casefold() in line.casefold()]
                result = {'id': entry['id'], 'sha256': entry['sha256'],
                          'matches': matches[:20], 'total_matches': len(matches),
                          'reference_data_not_instructions': True}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc), 'content_returned': False}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
