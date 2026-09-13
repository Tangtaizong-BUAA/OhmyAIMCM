"""Record authorized local computations; verify file bindings, not scientific truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'cumcm-execution/0.1'


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def local_path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip() or '\\' in value:
        raise ValueError('Expected a nonempty case-relative path')
    relative = Path(value)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError(f'Unsafe relative path: {value!r}')
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f'Symlink is not a bound local artifact: {value}')
    current.resolve().relative_to(root.resolve())
    return current


def artifact(root: Path, value: str, *, nonempty: bool = False) -> dict:
    path = local_path(root, value)
    if not path.is_file():
        raise ValueError(f'Missing regular file: {value}')
    size = path.stat().st_size
    if nonempty and size == 0:
        raise ValueError(f'Empty result file: {value}')
    return {'path': path.relative_to(root).as_posix(), 'bytes': size, 'sha256': digest(path)}


def run_directory(case: Path, run_id: str) -> Path:
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', run_id):
        raise ValueError('run_id must be a simple 1-64 character identifier')
    return local_path(case, f'runs/{run_id}')


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record(case: Path, run_id: str, argv: list[str], code: list[str], inputs: list[str],
           outputs: list[str], *, data_kind: str = 'synthetic', timeout: float = 30,
           no_input_reason: str = '') -> dict:
    case = case.resolve()
    if not case.is_dir():
        raise ValueError('case must be an existing directory')
    if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
        raise ValueError('An explicit nonempty argv is required; shell strings are not accepted')
    if not code or not outputs:
        raise ValueError('Declare code and at least one expected computed result')
    if not inputs and not no_input_reason.strip():
        raise ValueError('A no-input calculation requires an explicit reason')
    if data_kind not in {'synthetic', 'user-provided', 'official'}:
        raise ValueError('Unknown data_kind')
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be a positive finite number')
    roles = code + inputs + outputs
    canonical = [local_path(case, value).resolve() for value in roles]
    if len(set(canonical)) != len(canonical):
        raise ValueError('Code, input and output paths must be distinct')
    for value in roles:
        if Path(value).parts[0] == 'runs':
            raise ValueError('runs/ is reserved for execution records')
    code_before = [artifact(case, value) for value in code]
    inputs_before = [artifact(case, value) for value in inputs]
    for value in outputs:
        path = local_path(case, value)
        if path.exists():
            raise ValueError(f'Refusing to reuse or overwrite output: {value}')
    directory = run_directory(case, run_id)
    directory.mkdir(parents=True, exist_ok=False)
    errors = []
    returncode = None
    timed_out = False
    started = now()
    start_clock = time.monotonic()
    stdout = directory / 'stdout.log'
    stderr = directory / 'stderr.log'
    with stdout.open('xb') as out, stderr.open('xb') as err:
        try:
            completed = subprocess.run(argv, cwd=case, stdout=out, stderr=err,
                                       timeout=timeout, check=False, shell=False,
                                       env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
            returncode = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            errors.append('Command timed out; numerical result is not accepted')
        except OSError as exc:
            errors.append(f'Command could not start: {exc}')
    if returncode != 0:
        errors.append(f'Command did not exit successfully: {returncode}')
    for item in code_before + inputs_before:
        try:
            if artifact(case, item['path']) != item:
                errors.append(f'Declared source changed during execution: {item["path"]}')
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    actual_outputs = []
    for value in outputs:
        try:
            actual_outputs.append(artifact(case, value, nonempty=True))
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    receipt = {
        'schema_version': VERSION, 'run_id': run_id,
        'status': 'executed' if not errors else 'failed',
        'argv': argv, 'started_at': started, 'finished_at': now(),
        'elapsed_seconds': time.monotonic() - start_clock,
        'environment': {'python': sys.version, 'platform': platform.platform()},
        'data_kind': data_kind, 'no_input_reason': no_input_reason,
        'returncode': returncode, 'timed_out': timed_out, 'timeout_seconds': timeout,
        'code': code_before, 'inputs': inputs_before,
        'expected_outputs': [local_path(case, v).relative_to(case).as_posix() for v in outputs],
        'outputs': actual_outputs,
        'logs': [artifact(case, p.relative_to(case).as_posix()) for p in (stdout, stderr)],
        'errors': errors, 'scientific_review': 'not_checked',
    }
    with (directory / 'receipt.json').open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return receipt


def verify(case: Path, run_id: str) -> dict:
    case = case.resolve()
    errors = []
    try:
        directory = run_directory(case, run_id)
        receipt = json.loads((directory / 'receipt.json').read_text(encoding='utf-8'))
        if not isinstance(receipt, dict):
            raise ValueError('Receipt root must be an object')
        if receipt.get('schema_version') != VERSION or receipt.get('run_id') != run_id:
            raise ValueError('Unsupported or mismatched execution record')
    except (OSError, ValueError) as exc:
        return {'execution_binding': 'failed', 'errors': [str(exc)], 'scientific_review': 'not_checked'}
    if receipt.get('status') != 'executed':
        errors.append('Run was not recorded as executed successfully')
    if type(receipt.get('returncode')) is not int or receipt['returncode'] != 0:
        errors.append('Expected integer returncode 0')
    if receipt.get('timed_out') is not False or receipt.get('errors') != []:
        errors.append('Timeout or recorded execution errors remain')
    if receipt.get('scientific_review') != 'not_checked':
        errors.append('Execution receipt must not self-certify scientific review')
    if receipt.get('data_kind') not in {'synthetic', 'user-provided', 'official'}:
        errors.append('Unknown data provenance category')
    argv = receipt.get('argv')
    if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
        errors.append('Missing actual command argv')
    for field in ('started_at', 'finished_at'):
        try:
            stamp = datetime.fromisoformat(receipt[field])
            if stamp.tzinfo is None:
                raise ValueError('Timezone is required')
        except (KeyError, TypeError, ValueError):
            errors.append(f'Invalid {field}')
    environment = receipt.get('environment')
    if not isinstance(environment, dict) or not all(isinstance(environment.get(k), str) and environment[k]
                                                    for k in ('python', 'platform')):
        errors.append('Missing environment record')
    for field in ('elapsed_seconds', 'timeout_seconds'):
        value = receipt.get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or (field == 'timeout_seconds' and value == 0):
            errors.append(f'Invalid {field}')
    paths_by_role = {}
    all_paths = set()
    for role in ('code', 'inputs', 'outputs', 'logs'):
        collection = receipt.get(role)
        if not isinstance(collection, list) or (role != 'inputs' and not collection):
            errors.append(f'Missing/non-list {role}')
            continue
        paths_by_role[role] = set()
        if role == 'inputs' and not collection:
            if not isinstance(receipt.get('no_input_reason'), str) or not receipt['no_input_reason'].strip():
                errors.append('Empty inputs require an explanation')
        for item in collection:
            try:
                if not isinstance(item, dict):
                    raise ValueError(f'{role} item is not an object')
                size = item.get('bytes')
                if type(size) is not int or size < 0:
                    raise ValueError(f'{role} item has invalid byte count')
                if not isinstance(item.get('sha256'), str) or not re.fullmatch(r'[a-f0-9]{64}', item['sha256']):
                    raise ValueError(f'{role} item has invalid SHA-256')
                current = artifact(case, item.get('path'), nonempty=role == 'outputs')
                key = current['path']
                if key in all_paths:
                    raise ValueError(f'Duplicate/overlapping artifact: {key}')
                all_paths.add(key)
                paths_by_role[role].add(key)
                if current != item:
                    raise ValueError(f'Stale or changed {role} artifact: {key}')
            except (OSError, ValueError, TypeError) as exc:
                errors.append(str(exc))
    expected = receipt.get('expected_outputs')
    if not isinstance(expected, list) or not expected or not all(isinstance(v, str) and v for v in expected):
        errors.append('Missing expected result list')
    else:
        try:
            expected_paths = [local_path(case, v).relative_to(case).as_posix() for v in expected]
            if len(set(expected_paths)) != len(expected_paths) or set(expected_paths) != paths_by_role.get('outputs'):
                errors.append('Expected outputs do not match bound outputs')
        except (ValueError, OSError) as exc:
            errors.append(str(exc))
    wanted_logs = {f'runs/{run_id}/stdout.log', f'runs/{run_id}/stderr.log'}
    if paths_by_role.get('logs') != wanted_logs:
        errors.append('Captured stdout/stderr logs are missing or mismatched')
    return {'execution_binding': 'valid' if not errors else 'failed', 'errors': errors,
            'scientific_review': 'not_checked', 'data_kind': receipt.get('data_kind')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    capture = sub.add_parser('record')
    check = sub.add_parser('verify')
    for command in (capture, check):
        command.add_argument('--case', type=Path, required=True)
        command.add_argument('--run-id', required=True)
    capture.add_argument('--code', action='append', required=True)
    capture.add_argument('--input', action='append', default=[])
    capture.add_argument('--output', action='append', required=True)
    capture.add_argument('--no-input-reason', default='')
    capture.add_argument('--data-kind', choices=['synthetic', 'user-provided', 'official'], default='synthetic')
    capture.add_argument('--timeout', type=float, default=30)
    capture.add_argument('argv', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.mode == 'record':
            argv = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
            result = record(args.case, args.run_id, argv, args.code, args.input, args.output,
                            data_kind=args.data_kind, timeout=args.timeout, no_input_reason=args.no_input_reason)
            print(json.dumps({'status': result['status'], 'errors': result['errors'],
                              'scientific_review': 'not_checked'}, ensure_ascii=False, indent=2))
            return 0 if result['status'] == 'executed' else 2
        result = verify(args.case, args.run_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['execution_binding'] == 'valid' else 2
    except (OSError, ValueError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
