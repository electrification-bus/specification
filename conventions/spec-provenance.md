# Specification Provenance: the `.ebus-spec.json` lockfile

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-10
**Authors:** Don Jackson

## Purpose

The Electrification Bus specification is a set of **independently versioned artifacts** (each capability catalog, data model, and registry carries its own `Version:`), and it changes rapidly. Downstream implementations, publisher and controller libraries (for example the Python and ESP32 SDKs) and the applications built on them (proxies, adapters, gateways), depend on **specific versions of specific artifacts**, not on "the spec" as a whole.

`.ebus-spec.json` is a small **provenance lockfile** a downstream repository carries to record, in a machine-readable way:

1. **which spec commit** it was last reconciled against (the exact anchor), and
2. **which artifacts and framework features, at which versions**, it depends on (the semantic dependency).

This is the eBus analogue of a dependency lockfile (`package-lock.json`, `Cargo.lock`). It answers three questions that git history alone cannot: *what spec state was this build made against?*, *is this repository current?*, and *which repositories are affected when an artifact changes?*

It pairs with two upstream artifacts published by the specification repository:

- the **[`CHANGELOG.md`](../CHANGELOG.md)** — what changed, and when;
- the **`spec-manifest.json`** (repo root) — the current version of every artifact, generated from the document headers (the same data the [README status table](../README.md#status) renders for humans). A downstream's `implements` map (and its `framework` / `supports`) is checked against this manifest to compute drift.

## Where it lives

Place `.ebus-spec.json` at the **root of the downstream implementation repository** (the real repo, not a shadow / tooling repo): it is a real dependency fact about the software, like a lockfile, and belongs with the code it describes. One file per repository.

## Schema

`.ebus-spec.json` is a JSON object.

| Field | Type | Required | Description |
|---|---|---|---|
| `spec_repo` | string | yes | URL (or `org/repo`) of the eBus specification repository this downstream tracks. |
| `synced_commit` | string | yes | The spec **commit SHA** this repository was last reconciled against (7-40 hex chars). The exact, unambiguous anchor. |
| `synced_date` | string (date) | yes | ISO-8601 date (`YYYY-MM-DD`) of the last reconciliation. |
| `framework` | string | no | The `framework.md` **version** this repository targets (for example `"0.5"`). The primary dependency for a library / SDK; also pinned by applications, which build on the framework. |
| `supports` | array of string | no | The framework **feature** identifiers this repository implements (see [framework.md Framework Features](../framework.md#framework-features)). The library / SDK axis: an SDK provides the mechanisms (the parent-child model, the `json` datatype, `$format` JSONSchema, settable properties, discovery, mTLS) rather than specific device or capability data models. |
| `implements` | object | no | The spec artifacts this repository implements, grouped by area, each pinned to the artifact **version** it was built against. |
| `implements.capabilities` | object | no | Map of capability name (for example `flex`) → version string (for example `"0.1"`). |
| `implements.data-models` | object | no | Map of data-model name (for example `utility-meter`) → version string. |
| `implements.registries` | object | no | Map of registry name (for example `capability-types`) → version string. |
| `role` | string | no | What this downstream is relative to the spec: `publisher`, `controller`, `library`, or `mixed`. Helps drift tooling and human readers. |
| `notes` | string | no | Free-form context (open items, partial implementations, pending dependencies). |
| `$schema` | string | no | Pointer to the JSON Schema below, for editor / CI validation. |

### Two dependency axes

A downstream declares its dependency on the specification along whichever of two axes fits its nature (a repository MAY use both):

- **`framework` + `supports`** (the *mechanism* axis) is what a **library / SDK** depends on: the framework version, and the framework **features** it implements (the parent-child device model, the `json` datatype, `$format` JSONSchema, settable properties, discovery, mTLS, and so on). An SDK provides the substrate that lets anyone publish or consume any capability; it does not itself implement specific device types.
- **`implements`** (the *artifact* axis) is what a **publisher or controller application** depends on: the concrete, independently versioned capability catalogs and data models it implements (for example `water-heater` 0.2, `flex` 0.1). An application also pins the `framework` version it builds on, but rarely populates `supports`.

**Both granularities are recorded on purpose:** `synced_commit` is the exact, reproducible anchor; the `framework` / `supports` / `implements` fields are the semantic dependency that enables per-feature and per-artifact drift detection. Populate an artifact in `implements` (or a feature in `supports`) only if the repository actually implements it. An `implements` entry's version is the one in that artifact's `Version:` header (or the [README status table](../README.md#status)) at the synced commit; `supports` values come from the [framework.md Framework Features](../framework.md#framework-features) list.

### JSON Schema

A downstream MAY validate its lockfile against this schema (the specification repository may also publish it as a standalone file at the `$id` URL):

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ebus.energy/schemas/ebus-spec.json",
  "title": "eBus specification provenance lockfile",
  "type": "object",
  "required": ["spec_repo", "synced_commit", "synced_date"],
  "additionalProperties": false,
  "properties": {
    "$schema": { "type": "string" },
    "spec_repo": { "type": "string" },
    "synced_commit": { "type": "string", "pattern": "^[0-9a-f]{7,40}$" },
    "synced_date": { "type": "string", "format": "date" },
    "framework": { "type": "string" },
    "supports": { "type": "array", "items": { "type": "string" } },
    "role": { "type": "string", "enum": ["publisher", "controller", "library", "mixed"] },
    "implements": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "capabilities": { "type": "object", "additionalProperties": { "type": "string" } },
        "data-models": { "type": "object", "additionalProperties": { "type": "string" } },
        "registries": { "type": "object", "additionalProperties": { "type": "string" } }
      }
    },
    "notes": { "type": "string" }
  }
}
```

## Examples

### Library / SDK (mechanism implementer)

An SDK provides the framework machinery, not specific device models, so it leans on `framework` + `supports`:

```json
{
  "$schema": "https://ebus.energy/schemas/ebus-spec.json",
  "spec_repo": "https://github.com/electrification-bus/specification",
  "synced_commit": "1a90e4a",
  "synced_date": "2026-07-10",
  "role": "library",
  "framework": "0.5",
  "supports": [
    "parent-child-model", "node-capability-structure",
    "json-datatype", "jsonschema-format", "settable-properties",
    "empty-string-encoding", "mdns-discovery", "mtls-client-auth", "proxy-publishers"
  ],
  "notes": "Generic SDK. json-datatype + jsonschema-format validation is an open item."
}
```

### Application (publisher)

A publisher implements specific device types and capabilities, so it leans on `implements` (and pins the `framework` it builds on):

```json
{
  "$schema": "https://ebus.energy/schemas/ebus-spec.json",
  "spec_repo": "https://github.com/electrification-bus/specification",
  "synced_commit": "1a90e4a",
  "synced_date": "2026-07-10",
  "role": "publisher",
  "framework": "0.5",
  "implements": {
    "capabilities": { "info": "0.1", "meter": "0.1", "status": "0.1", "flex": "0.1" },
    "data-models": { "water-heater": "0.2" }
  },
  "notes": "CTA-2045 UCM -> eBus water-heater bridge."
}
```

### Minimal

```json
{
  "spec_repo": "https://github.com/electrification-bus/specification",
  "synced_commit": "1a90e4a",
  "synced_date": "2026-07-10",
  "implements": { "capabilities": { "info": "0.1", "meter": "0.1" }, "data-models": { "utility-meter": "0.3" } }
}
```

## Adoption workflow

1. **Create** `.ebus-spec.json` at the root of your implementation repository.
2. **Anchor it:** set `spec_repo`, `synced_commit` to the spec SHA you built / reconciled against, and `synced_date`.
3. **Pin what you implement:** for each capability, data model, and registry your code depends on, add an entry under `implements` with the version from that artifact's `Version:` header (or the README status table) at `synced_commit`.
4. **Commit it** alongside the code, in the same change that reconciles to that spec state.
5. **On every sync:** after reconciling to a newer spec commit, bump `synced_commit` / `synced_date`, update any `implements` versions that changed, and record the reconciliation in your repository's own changelog or issue tracker. The specification [`CHANGELOG.md`](../CHANGELOG.md) tells you what moved between your old and new `synced_commit`.
6. **Check drift:** run the spec repo's [`tools/drift-report.py`](../tools/drift-report.py) against your lockfile(s), for example `python3 tools/drift-report.py --scan <your-repo-roots>`. It compares your `implements` versions, `framework` version, and `supports` features against the current `spec-manifest.json` and reports what you are behind on. The tool hardcodes no repository list: your fleet is a runtime argument (scan roots or a private config file), so it stays out of the public spec repo.

## Relationship to spec versioning

- The **source of truth** for an artifact's version is the `Version:` header in that artifact's document.
- **`spec-manifest.json`** (spec repo root) and the **README status table** are both generated from those headers, so they cannot drift from the source or from each other. The manifest is the machine-readable form a drift check consumes; the table is the human-readable form.
- A downstream's `.ebus-spec.json` `implements` versions are a **copy**, taken at sync time, of the manifest entries the downstream depends on. Drift is the difference between that copy and the current manifest.

## References

- [`CHANGELOG.md`](../CHANGELOG.md) — dated, artifact-tagged record of specification changes.
- [README status table](../README.md#status) — the human-readable manifest of current artifact versions.
- [`conventions/README.md`](README.md) — the index of specification-consumption conventions.
