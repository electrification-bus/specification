# Machine-Readable Property Definitions: the property-JSON convention

**Status:** DRAFT
**Version:** 0.2
**Date:** 2026-08-05
**Authors:** Don Jackson

## Purpose

The capability catalogs and data-model documents describe, in prose and tables, the vocabulary a device can publish: for each property, its datatype, unit, value domain, and whether it is settable. This convention makes that vocabulary available as co-located JSON, so a proxy, an SDK, a simulator, or a dashboard can read it as data. The JSON is generated from the Markdown and checked against it in CI, so it does not drift.

## Descriptive, not prescriptive

These artifacts describe the spec's vocabulary and guidance. They are not a conformance contract, and they are not an exhaustive or required property set. That follows directly from the framework's Design Principles:

- **Properties are MAY by default** (principle 8). The model is a contract for the evolving ecosystem, not a transcript of any one current feature set.
- **Publish what you have, omit what you don't** (principle 3). A publisher populates the subset it can; absent means unknown or not-applicable.
- **Scalars by default, `json` as the escape hatch** (principle 10). A simple implementation stays on a scalar or enum; a richer one opts into structure, and advertises the shape it publishes in `$format`.

A device's runtime Homie 5 `$description` is the authority for what it actually publishes. Relative to this spec, a publisher **may publish a subset**, **may add a property this spec does not list**, and **may redefine a property's datatype or enum value set**, as long as it advertises the shape it publishes in its `$description` / `$format`. All of that is legal. So a `capability-catalog` here says "here is the recommended way to publish this property if you publish it," and a `device-profile` says "here are the capabilities this device type typically composes." Neither says "you must publish exactly this." A `meter` on a circuit and a `meter` on a lugs device carrying different properties, or two OEMs' circuits differing, is expected.

## Two families, mirroring the two prose families

- A **capability catalog** (`capabilities/<name>.md`) gets a **`capability-catalog`** JSON: the recommended, extensible property vocabulary for that capability, defined once and reused across device types.
- A **device model** (`devices/<name>.md`) gets a **`device-profile`** JSON: a light, advisory composition of which capabilities each device type in the model typically publishes, and the spec's capability-level Req guidance where it states one. It carries no property-level detail; how to publish each property lives in the capability catalog it references.

## File layout and naming

The JSON sibling sits next to its prose file and shares its basename:

```
capabilities/meter.md      capabilities/meter.json      (kind: capability-catalog)
capabilities/status.md     capabilities/status.json
devices/bess.md        devices/bess.json        (kind: device-profile)
devices/circuit.md     devices/circuit.json
```

The parent directory tells you the family, and the `kind` field states it explicitly. These JSON files are **generated**: do not hand-edit them, edit the prose table and regenerate. They are marked `linguist-generated=true` in `.gitattributes` so GitHub collapses them in diffs.

## Versioning

A property-JSON file **inherits its prose file's `Version:`** and never declares its own. Because it shares the prose artifact's version, that artifact's existing entry in `spec-manifest.json` (for example `capabilities/meter`) already covers both files: pinning `capabilities/meter` in a downstream [`.ebus-spec.json`](spec-provenance.md) lockfile pins the prose and its JSON together. No new pin key is introduced.

### The `schema_version` token

Separate from the artifact version is the shape of the JSON itself, defined by this document. Each JSON file stamps a `schema_version` token (currently `property-schema-v1`). The normative contract for that token is this convention, which is itself a versioned, pinnable manifest artifact (`conventions/property-json`). A change to the JSON shape (a new field, a renamed key) bumps both the token and this document's `Version:`.

## The `capability-catalog` file

The recommended, complete property vocabulary of one capability. Every property it defines, whether or not any particular device publishes it.

```json
{
  "$schema": "https://ebus.energy/schemas/property-catalog.json",
  "schema_version": "property-schema-v1",
  "kind": "capability-catalog",
  "capability": "energy.ebus.capability.meter",
  "version": "0.2",
  "status": "DRAFT",
  "date": "2026-07-27",
  "properties": {
    "active-power":    { "datatype": "float", "unit": "W", "req": "MAY", "description": "Total active power. Sign per the reference-direction rule below." },
    "power-factor":    { "datatype": "float", "req": "MAY", "format": "-1.0:1.0", "description": "System power factor, signed; range [-1.0, 1.0]." },
    "imported-energy": { "datatype": "float", "unit": "Wh", "req": "MAY", "description": "Cumulative active energy imported. Monotonically non-decreasing." }
  },
  "property_patterns": {
    "voltage-{a,b,c}":   { "datatype": "float", "unit": "V", "req": "MAY", "expand": ["a", "b", "c"] },
    "current-{a,b,c,n}": { "datatype": "float", "unit": "A", "req": "MAY", "expand": ["a", "b", "c", "n"] }
  }
}
```

- **`properties`** maps each property identifier to its definition:
  - **`datatype`** (required): the **recommended** Homie 5 datatype (`integer`, `float`, `boolean`, `string`, `enum`, `color`, `datetime`, `duration`, `json`). A publisher may widen it (an open `string` in place of an `enum`, `json` in place of a scalar, per principle 10) and advertise the datatype it publishes in `$format`.
  - **`req`**: the property's conformance from the catalog table (MAY by default). This is the spec's guidance, not a per-device requirement.
  - **`unit`**: a numeric property's unit. Omitted for non-numeric properties and for a dimensionless numeric (a power factor has no unit). Usually a concrete unit (`W`, `kWh`, `A`, `%`, `°C`). A few properties instead carry an **abstract unit token**, which names a *dimension* rather than a unit: see below.
  - **`format`**: the **recommended core** value domain: for an `enum` a comma-separated token list (`OK,FAULT,UNKNOWN`), for a bounded numeric a `min:max` range. A publisher may extend or redefine the set and advertise its own in `$format` (open vocabularies, principle 8).
  - **`settable`**: present and `true` only for settable properties.
  - **`description`**: the prose from the table's Description column.
  - **`name`**: a short human name, when the source table carries a Name column (catalog tables usually do not).
- **`property_patterns`** holds per-conductor / per-phase families. The pattern key carries the suffix set inline in braces, matching the prose, and `expand` lists the tokens: `voltage-{a,b,c}` with `["a","b","c"]` expands to `voltage-a`, `voltage-b`, `voltage-c`.

### Abstract unit tokens

A property whose unit legitimately varies by device carries an **abstract unit token** in place of a concrete unit. The token names the dimension; the publisher chooses the unit.

| Token | Dimension | Why it is not concrete |
|---|---|---|
| `energy` | Energy | A reservoir's stored-energy magnitudes are reported in the device's native energy unit: a BESS in electrical `kWh`, a water heater in thermal `Wh`. They are neither the same unit nor summable across reservoir kinds, so the catalog cannot name one. |

The token appears on `soc`'s `soe`, `total-energy-storage` and `loadup-headroom`, and on `info`'s `nameplate-capacity`.

Two rules follow, and they matter to anyone reading these files as data:

- **A publisher MUST substitute a concrete unit** in the property's runtime `$unit` / `$description`. `energy` is never published on the wire.
- **A consumer MUST read the unit from the runtime `$description`, never from the catalog**, for any property carrying an abstract token. A consumer that maps units to presentation metadata (a Home Assistant bridge deriving `unit_of_measurement`, a dashboard axis label) would otherwise render the literal string `energy`. Reading the runtime unit is the correct habit for *every* property, since a publisher may report in any unit of the right dimension; an abstract token merely makes it unavoidable.

Abstract tokens are deliberately rare. Adding one is a spec change: it belongs in the table above, and in `ABSTRACT_UNITS` in [`tools/check-property-catalogs.py`](../tools/check-property-catalogs.py), which advises on any unit that is neither a known concrete unit nor a declared token (so a typo such as `enrgy` surfaces rather than passing silently as an opaque string).

## The `device-profile` file

A light, advisory composition. It records which capabilities each device type in the model composes, and the model's capability-level Req guidance where it states one. It carries no property-level detail: the recommended way to publish each property is in the capability catalog, and what a device actually publishes is authoritative in its runtime `$description`.

```json
{
  "$schema": "https://ebus.energy/schemas/device-profile.json",
  "schema_version": "property-schema-v1",
  "kind": "device-profile",
  "device": "energy.ebus.device.bess",
  "version": "0.14",
  "status": "DRAFT",
  "date": "2026-07-27",
  "device_types": {
    "energy.ebus.device.bess": {
      "role": "parent",
      "capabilities": {
        "info":   { "catalog": "energy.ebus.capability.info",   "catalog_version": "0.1", "req": "MUST" },
        "soc":    { "catalog": "energy.ebus.capability.soc",    "catalog_version": "0.1", "req": "MUST" },
        "meter":  { "catalog": "energy.ebus.capability.meter",  "catalog_version": "0.2", "req": "MUST" },
        "status": { "catalog": "energy.ebus.capability.status", "catalog_version": "0.1", "req": "MUST" }
      }
    },
    "energy.ebus.device.mid": {
      "role": "child",
      "capabilities": {
        "info": { "catalog": "energy.ebus.capability.info", "catalog_version": "0.1", "req": "MUST" },
        "grid": { "catalog": "energy.ebus.capability.grid", "catalog_version": "0.1", "req": "MUST" }
      }
    }
  }
}
```

- **`device_types`** maps each device type in the model to how it composes capabilities:
  - **`role`** (optional): `parent` or `child` in the device hierarchy (omitted for a single-device model).
  - **`capabilities`** maps a capability node id to a reference:
    - **`catalog`** (required): the `energy.ebus.capability.*` type this node implements, whose catalog carries the property vocabulary.
    - **`catalog_version`**: the catalog version the model was authored against.
    - **`req`**: the model's capability-level conformance guidance for this device type, where it states one; absent means it does not (the default is MAY). A model that documents its capabilities in prose rather than a `| Capability | Required |` table simply omits `req`, which is expected: presence-without-Req is the permissive default, not an omission to fix.

## Generated, checked, not enforced

The JSON is produced and verified by [`../tools/check-property-catalogs.py`](../tools/README.md), which follows the same two-mode contract as `gen-spec-manifest.py`:

- default: regenerate each JSON from its prose and write it;
- `--check`: regenerate in memory and fail if any committed JSON is stale or structurally invalid against the JSON Schemas.

CI runs `--check`, so a prose edit not reflected in the JSON, or a hand-edit of the JSON, fails the build. The tool **does not** force the prose to be exhaustively tabulated: illustrative prose examples (a capability's device-specific diagnostics, an enclosure's per-child notes) stay prose, consistent with the permissive model. Beyond generate-and-verify it emits only **advisory notes** (never fatal): an unregistered capability type, a unit on a non-numeric datatype, an `enum` with no recommended value set in prose. These flag likely inconsistencies in the recommended vocabulary; none constrains what a conformant publisher may do.

## JSON Schemas

The structure of both families is defined by JSON Schemas (draft 2020-12):

- [`schemas/property-catalog.schema.json`](schemas/property-catalog.schema.json), published as `https://ebus.energy/schemas/property-catalog.json`.
- [`schemas/device-profile.schema.json`](schemas/device-profile.schema.json), published as `https://ebus.energy/schemas/device-profile.json`.

Each JSON file names its schema in `$schema`. The schemas constrain the JSON's own structure (field names, datatypes, identifier patterns); they say nothing about what a device must publish.

## Relationship to the other conventions

- [`spec-provenance.md`](spec-provenance.md) defines the `.ebus-spec.json` lockfile whose `implements` pins cover a property-JSON file through its prose artifact's version, and whose `conventions/property-json` pin lets a downstream declare which property-JSON shape it consumes.
- [`../README.md`](../README.md#status) and `spec-manifest.json` list the current artifact versions; the JSON inherits those versions rather than adding to them.
