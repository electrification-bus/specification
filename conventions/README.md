# Conventions

Process and engineering conventions shared across the Electrification Bus repositories. These are distinct from the normative data models and capability catalogs; they are the disciplines that keep a fast-moving, multi-repo project consistent. They fall into two groups:

**Consuming the specification:** how downstream implementations (publisher and controller libraries, and the applications built on them) track, pin, and stay in sync with a specification that is still under rapid development. The specification is a set of independently versioned artifacts changing quickly, and downstream repositories need a disciplined way to record what they built against and detect when they have fallen behind.

**Building and releasing the repositories:** packaging, versioning, and release disciplines that every eBus Python repository follows so that builds and published artifacts stay consistent and reproducible.

## Conventions

| Convention | Document | Status |
|---|---|---|
| Specification provenance (`.ebus-spec.json` lockfile) | [`spec-provenance.md`](spec-provenance.md) | DRAFT v0.1 (2026-07-10) |
| Version single source of truth (Python packaging + release) | [`version-single-source.md`](version-single-source.md) | DRAFT v0.1 (2026-07-11) |

## Related

- [`../CHANGELOG.md`](../CHANGELOG.md) — dated, artifact-tagged log of specification changes.
- [`../README.md`](../README.md#status) — the status table (human-readable manifest of current artifact versions); the machine-readable counterpart is `spec-manifest.json` at the repository root.
