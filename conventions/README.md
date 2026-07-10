# Conventions

Conventions for **consuming** the Electrification Bus specification: how downstream implementations (publisher and controller libraries, and the applications built on them) track, pin, and stay in sync with a specification that is still under rapid development.

These are process conventions, distinct from the normative data models and capability catalogs. They exist because the specification is a set of independently versioned artifacts changing quickly, and downstream repositories need a disciplined way to record what they built against and detect when they have fallen behind.

## Conventions

| Convention | Document | Status |
|---|---|---|
| Specification provenance (`.ebus-spec.json` lockfile) | [`spec-provenance.md`](spec-provenance.md) | DRAFT v0.1 (2026-07-10) |

## Related

- [`../CHANGELOG.md`](../CHANGELOG.md) — dated, artifact-tagged log of specification changes.
- [`../README.md`](../README.md#status) — the status table (human-readable manifest of current artifact versions); the machine-readable counterpart is `spec-manifest.json` at the repository root.
