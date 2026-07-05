# Electrification Bus Capability Catalogs

This directory holds one canonical property-catalog document per cross-cutting `energy.ebus.capability.*` capability. A capability names a coherent functional aspect of a device (electrical metering, overcurrent protection, remote relay control, and so on); the same capability appears on devices of different device types. Rather than restating a capability's properties in every data model that uses it, each capability is defined once here and referenced by the data models, the way Matter defines a cluster once and references it from multiple device types.

Relationship to the other areas:

- **`registries/capability-types.md`** is the *index*: the flat list of registered `energy.ebus.capability.*` identifiers, each with a one-line description and a pointer to its canonical catalog.
- **`capabilities/`** (this area) holds the *catalogs*: the full property tables, value domains, crosswalks, and grounding for each capability.
- **`data-models/`** documents *device types*: which capabilities a device publishes and its device-specific conformance (which properties are SHOULD versus MAY on that device, and examples), referencing the catalogs here for property detail.

This area is being populated incrementally. A data model may still define a capability inline until that capability is migrated here.

## Catalogs

| Capability | Document | Status |
|---|---|---|
| `energy.ebus.capability.breaker` | [`breaker.md`](breaker.md) | DRAFT v0.1 (2026-07-05) |
| `energy.ebus.capability.switch` | [`switch.md`](switch.md) | DRAFT v0.1 (2026-07-05) |
