#!/usr/bin/env python3
"""Report specification drift for downstream implementations.

Compares each downstream repository's `.ebus-spec.json` provenance lockfile (see
conventions/spec-provenance.md) against the specification's current
`spec-manifest.json`, and reports where the downstream has fallen behind:
  - artifact axis: `implements` versions vs the manifest's current versions;
  - framework axis: the pinned `framework` version vs the manifest's;
  - feature axis: declared `supports` vs the framework's current feature list.

This tool is generic and hardcodes NO repository list. You provide the fleet to
check at invocation, so nothing about your repositories lives in the public spec
repo. The `.ebus-spec.json` files themselves live in the downstream repos.

Usage:
    # scan one or more roots for .ebus-spec.json files (typical local-dev use):
    python3 tools/drift-report.py --scan ~/projects/eBus/repo ~/projects/span.io/repo

    # explicit lockfile paths:
    python3 tools/drift-report.py path/to/.ebus-spec.json ...

    # a private roots/paths file kept OUTSIDE this repo (one path or scan:DIR per line):
    python3 tools/drift-report.py --config ~/my-ebus-fleet.txt

    # options:
    #   --manifest PATH   spec-manifest.json to check against (default: alongside this tool)
    #   --format json     machine-readable output
"""
import io, json, os, sys, argparse

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dolt", "embeddeddolt", "backup"}


def vkey(v):
    parts = []
    for p in str(v).split("."):
        m = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(m) if m else 0)
    return tuple(parts)


def vcmp(a, b):
    ka, kb = vkey(a), vkey(b)
    n = max(len(ka), len(kb))
    ka += (0,) * (n - len(ka))
    kb += (0,) * (n - len(kb))
    return (ka > kb) - (ka < kb)


def find_lockfiles(roots):
    found = []
    for root in roots:
        root = os.path.expanduser(root)
        if os.path.isfile(root):
            found.append(root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            if ".ebus-spec.json" in filenames:
                found.append(os.path.join(dirpath, ".ebus-spec.json"))
    return sorted(set(found))


def manifest_versions(manifest):
    """{'capabilities/flex': '0.1', 'framework': '0.5', ...} + framework feature set."""
    cur = {}
    for area, entries in manifest.get("artifacts", {}).items():
        for name, meta in entries.items():
            cur[f"{area}/{name}"] = meta["version"]
    fw = manifest.get("artifacts", {}).get("framework", {}).get("framework", {}).get("version")
    return cur, fw, set(manifest.get("framework_features", {}))


def check(lock, cur, fw_version, fw_features):
    findings = []  # (severity, message); severity in {behind, unknown, ahead}
    # framework axis
    if lock.get("framework") and fw_version:
        c = vcmp(lock["framework"], fw_version)
        if c < 0:
            findings.append(("behind", f"framework: pinned {lock['framework']}, current {fw_version}"))
        elif c > 0:
            findings.append(("ahead", f"framework: pinned {lock['framework']} is AHEAD of manifest {fw_version}"))
    # feature axis
    if "supports" in lock:
        declared = set(lock["supports"])
        missing = sorted(fw_features - declared)
        unknown = sorted(declared - fw_features)
        if missing:
            findings.append(("behind", f"framework features not yet supported: {', '.join(missing)}"))
        if unknown:
            findings.append(("unknown", f"declared features unknown to the framework (stale/typo): {', '.join(unknown)}"))
    # artifact axis
    for area, entries in (lock.get("implements") or {}).items():
        for name, ver in entries.items():
            key = f"{area}/{name}"
            if key not in cur:
                findings.append(("unknown", f"{key}: implements {ver}, not in manifest (renamed/removed?)"))
                continue
            c = vcmp(ver, cur[key])
            if c < 0:
                findings.append(("behind", f"{key}: pinned {ver}, current {cur[key]}"))
            elif c > 0:
                findings.append(("ahead", f"{key}: pinned {ver} is AHEAD of manifest {cur[key]}"))
    return findings


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Report eBus specification drift for downstream repos.")
    ap.add_argument("paths", nargs="*", help="explicit .ebus-spec.json paths")
    ap.add_argument("--scan", nargs="+", default=[], metavar="DIR", help="roots to scan for .ebus-spec.json")
    ap.add_argument("--config", metavar="FILE", help="file of paths or 'scan:DIR' lines (keep this outside the spec repo)")
    ap.add_argument("--manifest", default=os.path.join(os.path.dirname(here), "spec-manifest.json"))
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args()

    roots, scans = list(args.paths), list(args.scan)
    if args.config:
        for line in io.open(os.path.expanduser(args.config), encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            (scans if line.startswith("scan:") else roots).append(line[5:].strip() if line.startswith("scan:") else line)
    lockfiles = find_lockfiles(roots + scans)
    if not lockfiles:
        print("No .ebus-spec.json lockfiles found. Provide paths, --scan DIR, or --config FILE.", file=sys.stderr)
        sys.exit(2)

    manifest = json.load(io.open(os.path.expanduser(args.manifest), encoding="utf-8"))
    cur, fw_version, fw_features = manifest_versions(manifest)

    results = []
    for lf in lockfiles:
        try:
            lock = json.load(io.open(lf, encoding="utf-8"))
        except Exception as e:
            results.append({"lockfile": lf, "error": str(e)})
            continue
        findings = check(lock, cur, fw_version, fw_features)
        results.append({"lockfile": lf, "repo": lock.get("spec_repo"), "role": lock.get("role"),
                        "synced_commit": lock.get("synced_commit"), "synced_date": lock.get("synced_date"),
                        "findings": [{"severity": s, "message": m} for s, m in findings]})

    if args.format == "json":
        print(json.dumps({"manifest_framework": fw_version, "results": results}, indent=2))
        return

    behind_total = 0
    for r in results:
        rel = r["lockfile"].replace(os.path.expanduser("~"), "~")
        if "error" in r:
            print(f"\n! {rel}\n    invalid lockfile: {r['error']}")
            continue
        head = f"\n{rel}  [role={r.get('role') or '?'}, synced={r.get('synced_commit') or '?'} {r.get('synced_date') or ''}]"
        print(head.rstrip())
        if not r["findings"]:
            print("    up to date")
            continue
        for f in r["findings"]:
            mark = {"behind": "BEHIND", "unknown": "?????", "ahead": "AHEAD "}.get(f["severity"], "     ")
            print(f"    {mark}  {f['message']}")
            if f["severity"] == "behind":
                behind_total += 1
    print(f"\n{len(results)} lockfile(s) checked; {behind_total} behind finding(s). Manifest framework {fw_version}.")
    sys.exit(1 if behind_total else 0)


if __name__ == "__main__":
    main()
