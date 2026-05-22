# eBus Device Type Registry

**Status:** DRAFT v0.1
**Date:** 2026-05-22
**Authors:** Don Jackson

## Purpose

This document is the canonical registry of `energy.ebus.device.*` device-type identifiers used across all eBus data models. Data-model documents reference identifiers from this registry; new identifiers are added to this registry when a data-model document introduces them.

In the eBus Homie model, every device participating in the bus declares its device type via the `$type` attribute drawn from this namespace. A device-type identifier names a category of physical or logical device — for example, a distribution enclosure, a battery energy storage system, an electric vehicle supply equipment unit — and constrains what device structure (child devices, capabilities) the parent of that type is expected to expose.

This registry is descriptive, not exhaustive: it lists what is currently registered. Consumers MUST tolerate unknown `$type` values (e.g., accept and persist them; apply only generic Homie handling).

## Format rules

- Identifiers are of the form `energy.ebus.device.<name>`.
- The `<name>` portion is lowercase kebab-case ASCII: lowercase letters, digits, and hyphens only.
- No leading or trailing hyphens; no consecutive hyphens.
- Identifiers are case-sensitive.

## Registered device types

The **Source** column references the data-model document where the identifier currently appears. For identifiers that appear only as forward references (the full data model has not yet been published), the source is the document that introduced the reference.

| Identifier | Description | Source |
|---|---|---|
| `energy.ebus.device.distribution-enclosure` | Parent device for an electrical distribution enclosure (panel / load center / consumer unit / switchboard). Hosts child devices for circuits, feed points, and (in some installations) integrated DERs. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.device.circuit` | Child device representing one branch circuit within a distribution enclosure. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.device.lugs` | Child device representing a feed point (upstream or downstream lugs) on a distribution enclosure. Carries the meter for that feed. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.device.bess` | Battery Energy Storage System. Parent device for a BESS connected to the bus. *Full data model pending — currently referenced from the distribution-enclosure data model.* | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) (forward reference) |
| `energy.ebus.device.pv` | Photovoltaic inverter. Parent device for a PV inverter on the bus. *Full data model pending — currently referenced from the distribution-enclosure data model.* | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) (forward reference) |
| `energy.ebus.device.evse` | Electric Vehicle Supply Equipment. Parent device for an EVSE on the bus. *Full data model pending — currently referenced from the distribution-enclosure data model.* | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) (forward reference) |
| `energy.ebus.device.mid` | Microgrid Interconnect Device. Parent device for a MID — the grid-relay + per-side meters + controller subsystem that handles islanding for a grid-forming-capable site. *Full data model pending — currently referenced from the distribution-enclosure data model.* | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) (forward reference) |

## Adding new device types

New identifiers may be added to this registry as new data-model documents are published. The process:

1. The proposed identifier follows the format rules above.
2. The proposed identifier is genuinely new — not a synonym of an existing entry.
3. A data-model document defines (or explicitly references) the device and is the source for the registry row.
4. The proposed identifier is added to this registry with a description and a source reference.
5. This document's version is bumped.

Forward references (a data model that mentions a device type whose full model isn't published yet) are valid registry entries; they are marked as such in the Source column and re-pointed at the full data model when it lands.

Producers and consumers SHOULD treat unknown `$type` values as opaque — accept and persist them, but apply only the generic Homie / eBus framework defaults. This permits forward-compatibility: a device using a newer type identifier than the consumer knows about should still be handled gracefully.
