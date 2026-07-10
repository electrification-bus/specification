#!/usr/bin/env python3
"""Generate spec-manifest.json AND the README status table from the
Version:/Date:/Status: headers of the specification's versioned documents,
plus the Framework Features list from framework.md.

The document headers (and the framework.md Framework Features table) are the
single source of truth. This script aggregates them into (1) a machine-readable
manifest that downstream drift checks consume, and (2) the human-readable README
status table, so the two can never drift from the headers or from each other.
Run it after any version bump; `--check` fails if either output is stale.

Usage:
    python3 tools/gen-spec-manifest.py            # write spec-manifest.json + README table
    python3 tools/gen-spec-manifest.py --check    # exit 1 if either would change
"""
import io, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_REPO = "https://github.com/electrification-bus/specification"

AREAS = ["data-models", "capabilities", "registries", "integration-guides",
         "extensions", "conventions"]
TABLE_SECTIONS = [("Framework", "framework"), ("Data Models", "data-models"),
                  ("Registries", "registries"), ("Capabilities", "capabilities"),
                  ("Integration Guides", "integration-guides"),
                  ("Extensions", "extensions"), ("Conventions", "conventions")]
PLACEHOLDERS = {
    "data-models": [("data-models/mid.md",
        "Planned (see the standalone-MID note in [`data-models/bess.md`](data-models/bess.md) §Device Hierarchy)")],
}
BEGIN = "<!-- BEGIN generated status table (run: python3 tools/gen-spec-manifest.py) -->"
END = "<!-- END generated status table -->"

VERSION_RE = re.compile(r"^\*\*Version:\*\*\s*(\S+)", re.M)
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(\w+)(?:\s+v(\S+))?", re.M)
DATE_RE = re.compile(r"^\*\*Date:\*\*\s*(\S+)", re.M)
# A Framework Features table row: | Name | `feature-id` | since | Description |
FEATURE_RE = re.compile(r"^\|[^|]*\|\s*`([a-z0-9-]+)`\s*\|\s*([0-9][0-9.]*)\s*\|", re.M)


def parse(path):
    head = io.open(path, encoding="utf-8").read()[:1200]
    sm, vm, dm = STATUS_RE.search(head), VERSION_RE.search(head), DATE_RE.search(head)
    version = vm.group(1) if vm else (sm.group(2) if sm and sm.group(2) else None)
    if not version:
        return None
    return {"version": version, "date": dm.group(1) if dm else None,
            "status": sm.group(1) if sm else None, "path": os.path.relpath(path, REPO)}


def scan():
    artifacts = {}
    fw = parse(os.path.join(REPO, "framework.md"))
    if fw:
        artifacts["framework"] = {"framework": fw}
    for area in AREAS:
        d = os.path.join(REPO, area)
        if not os.path.isdir(d):
            continue
        entries = {}
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".md") or fn.upper() == "README.MD":
                continue
            meta = parse(os.path.join(d, fn))
            if meta:
                entries[fn[:-3]] = meta
        if entries:
            artifacts[area] = entries
    return artifacts


def framework_features():
    """{feature-id: since-version} parsed from framework.md's Framework Features table."""
    text = io.open(os.path.join(REPO, "framework.md"), encoding="utf-8").read()
    return {m.group(1): m.group(2) for m in FEATURE_RE.finditer(text)}


def manifest_json(artifacts, features):
    return json.dumps({"spec_repo": SPEC_REPO,
        "note": "Generated from document headers + framework.md Framework Features by tools/gen-spec-manifest.py. Do not edit by hand.",
        "framework_features": dict(sorted(features.items())),
        "artifacts": artifacts}, indent=2) + "\n"


def status_table(artifacts):
    rows = ["| Document | Status |", "|---|---|"]
    for label, area in TABLE_SECTIONS:
        rows.append(f"| **{label}** | |")
        for name in sorted(artifacts.get(area, {})):
            m = artifacts[area][name]
            ver = f"{m['status']} v{m['version']}" + (f" ({m['date']})" if m["date"] else "")
            rows.append(f"| [`{m['path']}`]({m['path']}) | {ver} |")
        for path, note in PLACEHOLDERS.get(area, []):
            rows.append(f"| `{path}` | {note} |")
    return "\n".join(rows)


def readme_with_table(table):
    p = os.path.join(REPO, "README.md")
    t = io.open(p, encoding="utf-8").read()
    i, j = t.index(BEGIN) + len(BEGIN), t.index(END)
    return p, t[:i] + "\n" + table + "\n" + t[j:]


def main():
    artifacts = scan()
    new_manifest = manifest_json(artifacts, framework_features())
    manifest_path = os.path.join(REPO, "spec-manifest.json")
    readme_path, new_readme = readme_with_table(status_table(artifacts))
    if "--check" in sys.argv:
        stale = []
        if not os.path.exists(manifest_path) or io.open(manifest_path, encoding="utf-8").read() != new_manifest:
            stale.append("spec-manifest.json")
        if io.open(readme_path, encoding="utf-8").read() != new_readme:
            stale.append("README.md status table")
        if stale:
            print("STALE (run tools/gen-spec-manifest.py): " + ", ".join(stale), file=sys.stderr)
            sys.exit(1)
        print("spec-manifest.json and README status table are up to date")
        return
    io.open(manifest_path, "w", encoding="utf-8").write(new_manifest)
    io.open(readme_path, "w", encoding="utf-8").write(new_readme)
    print("wrote spec-manifest.json and updated README status table")


if __name__ == "__main__":
    main()
