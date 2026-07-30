# Tools

Small Python utilities for maintaining the specification and for downstream implementations to check their currency against it. Most are standard-library only; `check-property-catalogs.py` needs `jsonschema` (see [`requirements.txt`](requirements.txt)). The maintenance checks run in CI (see [`../.github/workflows/spec-checks.yml`](../.github/workflows/spec-checks.yml)).

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

## `check-capability-catalogs.py`

Enforces two capability-registry invariants: every capability actually used (declared as a `**Node type:**` in a data model) is registered in `registries/capability-types.md`, and every registered capability has a standalone versioned catalog under `capabilities/` (except the allowlisted device-defining capabilities). Its output is the remaining canonicalization backlog.

```bash
python3 tools/check-capability-catalogs.py   # non-zero if a capability is unregistered or uncatalogued
```

## `check-property-catalogs.py`

Generates, and verifies, the machine-readable property-definition JSON siblings of the prose (see [`../conventions/property-json.md`](../conventions/property-json.md)): a `capabilities/<name>.json` for each capability catalog and a `devices/<name>.json` for each supported device model. These are **descriptive**, not a conformance contract: a catalog is the recommended, extensible property vocabulary; a device profile is a light, advisory composition of the capabilities each device type publishes.

```bash
python3 tools/check-property-catalogs.py          # regenerate the JSON from the prose
python3 tools/check-property-catalogs.py --check  # non-zero if any JSON is stale or structurally invalid
```

Needs `jsonschema` (validates the generated JSON against `conventions/schemas/`). The Markdown is the single source of truth; do not hand-edit the generated JSON. `--check` never forces intentionally-illustrative prose into tables; it only fails on stale or malformed JSON, and otherwise emits advisory notes.

## Continuous integration

[`../.github/workflows/spec-checks.yml`](../.github/workflows/spec-checks.yml) runs `gen-spec-manifest.py --check`, `check-capability-catalogs.py`, and `check-property-catalogs.py --check` on every push to `main` and every pull request, so the manifest, the registry invariants, and the property JSON stay consistent with the prose. `drift-report.py` is not in CI: it checks downstream repositories, which live outside this repo.
