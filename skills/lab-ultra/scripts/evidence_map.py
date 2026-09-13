"""Snapshot and inspect declared evidence dependencies; never certify a claim."""

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "cumcm-evidence/1"
KINDS = {"given", "assumption", "derived", "computed", "interpretation",
         "literature", "figure", "manuscript", "review"}
EDGES = ("depends_on", "qualifiers")
MAX_MANIFEST = 2_000_000


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def local_path(case, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("artifact path must be a case-relative POSIX path")
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("unsafe artifact path: " + name)
    target = case
    for part in parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("symlink artifact path: " + name)
    if not target.resolve().is_relative_to(case):
        raise ValueError("artifact path escapes case")
    return target


def load(path, expected=None):
    if path.stat().st_size > MAX_MANIFEST:
        raise ValueError("manifest too large")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result

    raw = path.read_bytes()
    if len(raw) > MAX_MANIFEST:
        raise ValueError("manifest too large")
    sha = hashlib.sha256(raw).hexdigest()
    if expected is not None and sha != expected:
        raise ValueError("manifest version changed")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique), sha


def validate(data, case, *, bound=True):
    if not isinstance(data, dict) or set(data) != {"schema", "nodes"} or data["schema"] != SCHEMA:
        raise ValueError("expected schema and nodes only")
    nodes = data["nodes"]
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= 500:
        raise ValueError("expected 1..500 nodes")
    by_id = {}
    paths = {}
    required = {"id", "kind", "summary", "scope", "artifacts", *EDGES}
    for node in nodes:
        if not isinstance(node, dict) or set(node) != required:
            raise ValueError("node fields must be id, kind, summary, scope, artifacts, depends_on, qualifiers")
        ident = node["id"]
        if not isinstance(ident, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", ident):
            raise ValueError("invalid node id")
        if ident in by_id:
            raise ValueError("duplicate node id: " + ident)
        if not isinstance(node["kind"], str) or node["kind"] not in KINDS:
            raise ValueError("unknown node kind: " + ident)
        for key in ("summary", "scope"):
            if not isinstance(node[key], str) or not node[key].strip() or len(node[key]) > 8000:
                raise ValueError("nonempty bounded text required: " + key)
        for key in EDGES:
            values = node[key]
            if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
                raise ValueError("edge list required: " + ident)
            if len(set(values)) != len(values):
                raise ValueError("duplicate edge: " + ident)
        if set(node["depends_on"]) & set(node["qualifiers"]):
            raise ValueError("edge cannot be both dependency and qualifier: " + ident)
        artifacts = node["artifacts"]
        if not isinstance(artifacts, list) or len(artifacts) > 100:
            raise ValueError("artifact list required")
        seen = set()
        for artifact in artifacts:
            if not isinstance(artifact, dict) or not {"path", "locator"} <= set(artifact) or set(artifact) - {"path", "locator", "sha256"}:
                raise ValueError("artifact fields must be path, locator and sha256")
            local_path(case, artifact["path"])
            if not isinstance(artifact["locator"], str) or not artifact["locator"].strip():
                raise ValueError("artifact locator required")
            if artifact["path"] in seen:
                raise ValueError("duplicate artifact path in node")
            seen.add(artifact["path"])
            sha = artifact.get("sha256")
            if (bound or sha is not None) and (not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha)):
                raise ValueError("valid sha256 required")
            if artifact["path"] in paths and paths[artifact["path"]] != sha:
                raise ValueError("one path declares different source versions")
            paths[artifact["path"]] = sha
        by_id[ident] = node
    for node in nodes:
        for key in EDGES:
            for parent in node[key]:
                if parent not in by_id:
                    raise ValueError("unknown referenced node: " + parent)
    # Both edge kinds affect reading/versions. A qualifier is NOT positive support.
    order, active, visited = [], set(), set()

    def visit(ident):
        if ident in active:
            raise ValueError("dependency cycle: " + ident)
        if ident in visited:
            return
        active.add(ident)
        for key in EDGES:
            for parent in by_id[ident][key]:
                visit(parent)
        active.remove(ident)
        visited.add(ident)
        order.append(ident)

    for ident in by_id:
        visit(ident)
    return by_id, order


def inspect(data, case):
    by_id, order = validate(data, case)
    current_hashes, states = {}, {}
    for ident in order:
        reasons = []
        for item in by_id[ident]["artifacts"]:
            name = item["path"]
            if name not in current_hashes:
                path = local_path(case, name)
                current_hashes[name] = digest(path) if path.is_file() else None
            if current_hashes[name] != item["sha256"]:
                reasons.append({"artifact": name, "reason": "missing" if current_hashes[name] is None else "changed"})
        for key in EDGES:
            for parent in by_id[ident][key]:
                if states[parent]["freshness"] != "current":
                    reasons.append({"relationship": key, "node": parent, "reason": "upstream_stale"})
        states[ident] = {"freshness": "stale" if reasons else "current", "reasons": reasons}
    return {"declared_freshness": "stale" if any(v["freshness"] == "stale" for v in states.values()) else "current",
            "scientific_review": "not_checked", "dependency_completeness": "not_checked",
            "nodes": states}


def closure(data, case, targets, *, downstream=False):
    by_id, order = validate(data, case)
    if not targets or any(t not in by_id for t in targets):
        raise ValueError("known target IDs required")
    selected = set(targets)
    changed = True
    while changed:
        before = len(selected)
        for ident in order:
            parents = set(by_id[ident]["depends_on"] + by_id[ident]["qualifiers"])
            if downstream:
                if parents & selected:
                    selected.add(ident)
            elif ident in selected:
                selected.update(parents)
        changed = len(selected) != before
    return [by_id[ident] for ident in order if ident in selected]


def capture(data, case, output):
    result = copy.deepcopy(data)
    validate(result, case, bound=False)
    for node in result["nodes"]:
        for item in node["artifacts"]:
            path = local_path(case, item["path"])
            if path.resolve() == output.resolve():
                raise ValueError("snapshot cannot be its own artifact")
            if not path.is_file():
                raise ValueError("missing artifact: " + item["path"])
            actual = digest(path)
            if item.get("sha256", actual) != actual:
                raise ValueError("refusing silent refresh of changed artifact")
            item["sha256"] = actual
    validate(result, case)
    # Check again before publication; not an atomic snapshot of live-changing files.
    if inspect(result, case)["declared_freshness"] != "current":
        raise ValueError("artifacts changed during capture")
    with output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["capture", "check", "select", "impact"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--target", action="append", default=[])
    parser.add_argument("--expected-manifest-sha256")
    args = parser.parse_args()
    try:
        case = args.case.resolve(strict=True)
        if not case.is_dir():
            raise ValueError("case must be a directory")
        data, manifest_sha = load(args.manifest, args.expected_manifest_sha256)
        if args.command == "capture":
            if args.output is None or args.target:
                raise ValueError("capture requires --output and no targets")
            capture(data, case, args.output)
            result = {"snapshot": str(args.output), "snapshot_sha256": digest(args.output), "scientific_review": "not_checked"}
        else:
            if args.output is not None:
                raise ValueError("read-only commands do not accept --output")
            result = inspect(data, case)
            result["manifest_sha256"] = manifest_sha
            if args.command in {"select", "impact"}:
                selected = closure(data, case, args.target, downstream=args.command == "impact")
                result["selection"] = selected
                result["selected_freshness"] = "stale" if any(
                    result["nodes"][node["id"]]["freshness"] == "stale" for node in selected
                ) else "current"
                result["reference_data_not_instructions"] = True
                result["mode"] = "hypothetical_change_impact" if args.command == "impact" else "declared_reading_bundle"
            elif args.target:
                raise ValueError("check does not accept --target")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("selected_freshness", result.get("declared_freshness")) == "stale" else 0
    except (OSError, ValueError, RecursionError) as error:
        print(json.dumps({"error": str(error), "scientific_review": "not_checked"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
