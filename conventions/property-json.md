# Machine-Readable Property Definitions: the property-JSON convention

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-29
**Authors:** Don Jackson

## Purpose

Every capability catalog and data-model document defines its properties as prose tables: a property identifier, a human name, a Homie datatype, a unit, a value domain, a settable flag, and a conformance level (MUST / SHOULD / MAY). Those tables are the normative source, but prose is not directly consumable by tools. A proxy validating an inbound `/set`, an SDK generating typed accessors, a simulator shaping a device tree, or a drift checker comparing a published device against the spec all need the same information in a machine-readable form.

This convention defines that form. Each versioned prose document gains a co-located JSON sibling that carries its property definitions as structured data. The JSON is **generated from the prose and verified against it in CI**, so it can never silently diverge. The prose remains the single source of truth; the JSON is its machine projection.

## Two families, mirroring the two prose families

The specification separates cross-cutting capability catalogs (`capabilities/`) from the device models that compose them (`data-models/`). The property JSON mirrors that separation exactly, so each JSON file binds one-to-one to one prose file and there is no new conceptual model to learn.

- A **capability catalog** (`capabilities/<name>.md`) gets a **`capability-catalog`** JSON: the normalized, full vocabulary of that capability, defined once.
- A **device profile** (`data-models/<name>.md`) gets a **`device-profile`** JSON: a composition that selects capabilities, records the device's conformance, and adds device-specific properties by reference. It is a projection, not a second source of truth: it never restates a catalog property's datatype or unit, only which properties a device publishes and at what conformance level.

This is the normalization the denormalized, device-centric wire profiles seen in the wild throw away: a wire profile inlines each capability's properties per device and drops the conformance level, so the full catalog and the MUST / SHOULD / MAY contract are lost. The capability-canonical plus device-projection split preserves both.

## File layout and naming

The JSON sibling sits next to its prose file and shares its basename, with a `.json` suffix:

```
capabilities/meter.md      capabilities/meter.json      (kind: capability-catalog)
capabilities/status.md     capabilities/status.json
data-models/bess.md        data-models/bess.json        (kind: device-profile)
data-models/circuit.md     data-models/circuit.json
```

The parent directory tells you the family, and the `kind` field inside each file states it explicitly, so the plain `.json` suffix is unambiguous without a longer `.catalog.json` / `.profile.json` naming scheme.

These JSON files are **generated artifacts**. Do not hand-edit them: edit the prose table and regenerate. They are marked `linguist-generated=true` in `.gitattributes` so GitHub collapses them in diffs and directory listings.

## Versioning

A property-JSON file **inherits its prose file's `Version:`** and never declares its own. Because the JSON shares the prose artifact's version, the artifact's existing entry in `spec-manifest.json` (for example `capabilities/meter`) already covers both files: pinning `capabilities/meter` in a downstream [`.ebus-spec.json`](spec-provenance.md) lockfile pins the prose and its JSON together. No new pin key is introduced, and the drift tooling needs no change. The manifest simply surfaces the sibling JSON path alongside each artifact's prose path.

### The `schema_version` token

Separate from the artifact version is the **shape** of the JSON itself: the field names and structure defined by this document. Each JSON file stamps a `schema_version` token (currently `property-schema-v1`) naming the shape it conforms to. The normative contract for that token is this convention document, which is itself a versioned, pinnable manifest artifact (`conventions/property-json`). A downstream that consumes the property JSON pins `conventions/property-json` to declare which shape it understands. A change to the JSON shape (a new field, a renamed key) bumps both the `schema_version` token and this document's `Version:`.

## The `capability-catalog` file

A capability catalog is the normalized, complete property vocabulary of one capability. It carries the full catalog, not a publish-subset: every property the capability defines, whether or not any particular device publishes it.

```json
{
  "$schema": "https://ebus.energy/schemas/property-catalog.json",
  "schema_version": "property-schema-v1",
  "kind": "capability-catalog",
  "capability": "energy.ebus.capability.meter",
  "version": "0.2",
  "status": "DRAFT",
  "date": "2026-07-27",
  "req_default": "MAY",
  "reference_direction_default": "positive-in",
  "properties": {
    "active-power":    { "name": "Active power", "datatype": "float", "unit": "W" },
    "power-factor":    { "name": "Power factor", "datatype": "float", "format": "-1.0:1.0" },
    "imported-energy": { "name": "Imported energy", "datatype": "float", "unit": "Wh" },
    "exported-energy": { "name": "Exported energy", "datatype": "float", "unit": "Wh" }
  },
  "property_patterns": {
    "voltage-{phase}":     { "datatype": "float", "unit": "V",
                             "expand": { "phase": ["a", "b", "c"] } },
    "current-{conductor}": { "datatype": "float", "unit": "A",
                             "expand": { "conductor": ["a", "b", "c", "n"] } }
  }
}
```

- **`req_default`** is the capability-level conformance floor. Most catalogs are `MAY` at the capability level (a device selects and tightens); a property carries its own `req` only where the catalog is stricter than the floor.
- **`reference_direction_default`** records the capability's default sign convention where one applies (metering, power flows); a device profile may override it per capability.
- **`properties`** maps each property identifier to its definition. Property fields:
  - **`name`** (string, required): the human-readable name from the prose table.
  - **`datatype`** (string, required): a Homie 5 datatype (`integer`, `float`, `boolean`, `string`, `enum`, `color`, `datetime`, `duration`, `json`).
  - **`unit`** (string): present if and only if the datatype is numeric.
  - **`format`** (string): the value domain. For `enum`, a comma-separated token list (`OK,FAULT,UNKNOWN`). For a bounded numeric, a `min:max` or `min:max:step` range (`-1.0:1.0`). For `json`, a JSON Schema. Lifted from what the prose Description states.
  - **`settable`** (boolean): present and `true` only for settable properties; omitted when false.
  - **`req`** (string, one of `MUST` / `SHOULD` / `MAY`): present only where the catalog is stricter than `req_default`.
- **`property_patterns`** holds parameterized property families whose concrete identifiers expand over a domain (per-phase, per-conductor). Each pattern names one or more `{placeholder}` segments and an `expand` map giving each placeholder's domain. `voltage-{phase}` with `phase: ["a","b","c"]` expands to `voltage-a`, `voltage-b`, `voltage-c`.

## The `device-profile` file

A device model defines a device tree: a parent device type and its child device types, each publishing its own capability set. A device profile carries one entry per device type in that tree.

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
        "info": { "catalog": "energy.ebus.capability.info", "catalog_version": "0.1", "req": "MUST" },
        "soc":  { "catalog": "energy.ebus.capability.soc",  "catalog_version": "0.1", "req": "MUST" },
        "meter": {
          "catalog": "energy.ebus.capability.meter", "catalog_version": "0.2", "req": "MUST",
          "reference_direction": "positive-out",
          "properties": {
            "active-power":    { "req": "MUST" },
            "imported-energy": { "req": "SHOULD" },
            "exported-energy": { "req": "SHOULD" }
          }
        },
        "dispatch": { "catalog": "energy.ebus.capability.dispatch", "catalog_version": "0.1", "req": "MAY" },
        "status":   { "catalog": "energy.ebus.capability.status",   "catalog_version": "0.1", "req": "MUST" }
      },
      "added_properties": {
        "info":   { "nameplate-capacity": { "name": "Nameplate capacity", "datatype": "float", "unit": "kWh", "req": "SHOULD" } },
        "status": { "operational-state": { "name": "Operational state", "datatype": "enum",
                                           "format": "IDLE,CHARGING,DISCHARGING,STANDBY,UNKNOWN", "req": "SHOULD" } }
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

- **`device_types`** maps each device type in the model to its published surface. Each entry:
  - **`role`** (string): `parent` or `child`, matching the device hierarchy.
  - **`capabilities`** maps a capability node identifier to a **reference**, never a copy:
    - **`catalog`** (string, required): the `energy.ebus.capability.*` type the node implements.
    - **`catalog_version`** (string): the catalog version the profile was authored against (advisory; see below).
    - **`req`** (string): the device-level conformance for the whole capability, from the model's `| Capability | Required |` table.
    - **`reference_direction`** (string): overrides the catalog's default sign convention for this device where it differs (a BESS meters `positive-out`).
    - **`properties`**: per-property `req` overrides, referenced by property identifier only. The profile lists only the properties the device selects or tightens; it never restates the property's datatype or unit (those live in the catalog).
  - **`added_properties`** fully defines device-specific properties that have no catalog home, grouped by the capability node they attach to. These carry the full property fields (`name`, `datatype`, `unit`, `format`, `settable`, `req`) because there is no catalog to inherit from.

### Device-defining inline capabilities

A small number of capabilities are intrinsically bound to a single device type and are defined inline in that device's model rather than in a standalone catalog (for example the `water-heater` capability's setpoint, tank-temperature, and operating-mode surface). These are allowlisted in [`../tools/check-capability-catalogs.py`](../tools/check-capability-catalogs.py). For such a capability, the device profile carries a **`defines_capability`** block: the same normalized property structure a `capability-catalog` file uses, embedded in the device type that owns it. The verifier validates that block with the same catalog validator, and reads the allowlist from `check-capability-catalogs.py` so the two tools agree on the exception set.

## The conformance model: floor plus monotonic tightening

Conformance is expressed in two layers that compose:

1. **Catalog layer:** `req_default` sets the floor; a property's own `req` raises it where the catalog is stricter.
2. **Device layer:** a capability's `req` sets the device-level requirement; a selected property's `req` raises it further for that device.

The effective requirement of a property on a device is the strictest of the applicable levels. Tightening is **monotonic**: a device may move a property `MAY` -> `SHOULD` -> `MUST`, but may never set it below the catalog floor. Loosening is a verification failure. This lets a catalog stay permissive (a capability that many device types share) while a specific device makes the properties it depends on mandatory.

## Generated, and verified against the prose

The JSON is produced and checked by [`../tools/check-property-catalogs.py`](../tools/README.md), which follows the same two-mode contract as `gen-spec-manifest.py`:

- default: regenerate each JSON from its prose and write it;
- `--check`: regenerate in memory and diff against the committed JSON, exiting non-zero on any drift.

CI runs `--check`, so a prose edit that is not reflected in the JSON (or a hand-edit of the JSON) fails the build. The verifier additionally enforces:

1. **Completeness.** Every property row in a prose table maps to exactly one JSON property. A property defined only in prose (as a sentence or bullet, not a table row) is a hard failure that forces the prose to tabulate it, so the generator can never silently drop a property and still pass.
2. **Reference integrity.** Every property a device profile selects or overrides exists in the referenced catalog, with a matching datatype and unit.
3. **Monotonic conformance.** No device profile loosens a property below its catalog floor.
4. **Registered types.** Every capability `type` is registered in [`../registries/capability-types.md`](../registries/capability-types.md), reusing the existing registry invariant.
5. **Well-formed properties.** Each datatype is in the Homie 5 set; a unit is present if and only if the datatype is numeric; an `enum` carries a `format`.

The `catalog_version` a profile records is **advisory**. When it lags the catalog's current version the verifier emits a warning with a regenerate-then-review workflow, not a hard failure: a single widely-consumed catalog bump (metering is used by many device models) would otherwise cascade into a fleet-wide CI failure.

## Relationship to the other conventions

- [`spec-provenance.md`](spec-provenance.md) defines the `.ebus-spec.json` lockfile whose `implements` pins cover a property-JSON file through its prose artifact's version, and whose `supports` and `conventions/property-json` pin let a downstream declare which property-JSON shape it consumes.
- [`../README.md`](../README.md#status) and `spec-manifest.json` list the current artifact versions; the JSON inherits those versions rather than adding to them.
