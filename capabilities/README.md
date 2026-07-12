# Electrification Bus Capability Catalogs

This directory holds one canonical property-catalog document per cross-cutting `energy.ebus.capability.*` capability. A capability names a coherent functional aspect of a device (electrical metering, overcurrent protection, remote relay control, and so on); the same capability appears on devices of different device types. Rather than restating a capability's properties in every data model that uses it, each capability is defined once here and referenced by the data models, the way Matter defines a cluster once and references it from multiple device types.

Relationship to the other areas:

- **`registries/capability-types.md`** is the *index*: the flat list of registered `energy.ebus.capability.*` identifiers, each with a one-line description and a pointer to its canonical catalog.
- **`capabilities/`** (this area) holds the *catalogs*: the full property tables, value domains, crosswalks, and grounding for each capability.
- **`data-models/`** documents *device types*: which capabilities a device publishes and its device-specific conformance (which properties are SHOULD versus MAY on that device, and examples), referencing the catalogs here for property detail.

## Every capability has a catalog

A capability is a coherent functional aspect that can appear on devices of different types, so **every capability is potentially cross-cutting** and has its own standalone versioned catalog here: its single authoritative versioned home. That is what lets a capability be pinned in a downstream [`.ebus-spec.json`](../conventions/spec-provenance.md) lockfile and tracked for drift. A capability defined only inline in a data model carries no version of its own, so when its shared semantics change no single data-model version reliably reflects it and the drift can be silently missed.

The one exception is a **device-defining** capability, intrinsically bound to a single device type (it defines what that device fundamentally is, for example the `water-heater` capability's setpoint / tank-temperature / operating-mode surface). It has a permanent, reliable home in its device model and may remain inline; such capabilities are allowlisted in [`tools/check-capability-catalogs.py`](../tools/check-capability-catalogs.py), which fails if any other registered capability lacks a catalog.

This area is still being populated: [`tools/check-capability-catalogs.py`](../tools/check-capability-catalogs.py) lists the capabilities not yet migrated to a catalog.

## Catalogs

| Capability | Document | Status |
|---|---|---|
| `energy.ebus.capability.breaker` | [`breaker.md`](breaker.md) | DRAFT v0.1 (2026-07-05) |
| `energy.ebus.capability.connection` | [`connection.md`](connection.md) | DRAFT v0.1 (2026-07-05) |
| `energy.ebus.capability.demand` | [`demand.md`](demand.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.doe` | [`doe.md`](doe.md) | DRAFT v0.1 (2026-07-09) |
| `energy.ebus.capability.door` | [`door.md`](door.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.flex` | [`flex.md`](flex.md) | DRAFT v0.1 (2026-07-10) |
| `energy.ebus.capability.grid` | [`grid.md`](grid.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.grid-event` | [`grid-event.md`](grid-event.md) | DRAFT v0.1 (2026-07-10) |
| `energy.ebus.capability.grid-forming` | [`grid-forming.md`](grid-forming.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.info` | [`info.md`](info.md) | DRAFT v0.1 (2026-07-05) |
| `energy.ebus.capability.meter` | [`meter.md`](meter.md) | DRAFT v0.1 (2026-07-05) |
| `energy.ebus.capability.output-island` | [`output-island.md`](output-island.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.power-flows` | [`power-flows.md`](power-flows.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.power-quality` | [`power-quality.md`](power-quality.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.price` | [`price.md`](price.md) | DRAFT v0.1 (2026-07-10) |
| `energy.ebus.capability.shed-forecast` | [`shed-forecast.md`](shed-forecast.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.soc` | [`soc.md`](soc.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.status` | [`status.md`](status.md) | DRAFT v0.1 (2026-07-11) |
| `energy.ebus.capability.switch` | [`switch.md`](switch.md) | DRAFT v0.1 (2026-07-05) |
| `energy.ebus.capability.voltage-response` | [`voltage-response.md`](voltage-response.md) | DRAFT v0.1 (2026-07-10) |
