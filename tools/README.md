# Tools

Small, dependency-free Python utilities (standard library only) for maintaining the specification and for downstream implementations to check their currency against it.

## `gen-spec-manifest.py`

Generates, from the single source of truth (the `Version:` / `Date:` / `Status:` headers of the versioned documents, plus the `Framework Features` table in `framework.md`):

- `spec-manifest.json` (repo root) — the machine-readable manifest of every artifact's current version, and the framework feature list;
- the README status table (between its generated-content markers).

```bash
python3 tools/gen-spec-manifest.py          # regenerate both from the headers
python3 tools/gen-spec-manifest.py --check  # non-zero if either is stale (use in CI / before push)
```

Run it after any version bump. Do not hand-edit `spec-manifest.json` or the README status table. See [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## `drift-report.py`

Reports where downstream implementations have fallen behind the specification, by comparing each repository's [`.ebus-spec.json`](../conventions/spec-provenance.md) lockfile against `spec-manifest.json` on all three axes (artifact `implements` versions, the `framework` version, and declared `supports` features).

**This tool is generic and hardcodes no repository list.** You provide the fleet to check at invocation, so nothing about your repositories lives in this public repo. The `.ebus-spec.json` files live in the downstream repos; keep any persistent list of *where those repos are* outside this repo (for example a private roots file in your own tooling).

```bash
# scan roots for .ebus-spec.json files (typical local-dev use):
python3 tools/drift-report.py --scan ~/projects/eBus/repo ~/projects/span.io/repo

# explicit lockfile paths:
python3 tools/drift-report.py ../some-downstream/.ebus-spec.json

# a private roots/paths file kept OUTSIDE this repo (one path or 'scan:DIR' per line):
python3 tools/drift-report.py --config ~/my-ebus-fleet.txt

# options: --manifest PATH (default: ../spec-manifest.json), --format json
```

Exit code is non-zero when any downstream is behind, so it can gate a fleet-wide check.
