# eBus Capability Type Registry

**Status:** DRAFT v0.1
**Date:** 2026-05-22
**Authors:** Don Jackson

## Purpose

This document is the canonical registry of `energy.ebus.capability.*` capability-type identifiers used across all eBus data models. Data-model documents reference identifiers from this registry; new identifiers are added to this registry when a data-model document introduces them.

In the eBus Homie model, child devices group their properties under capability-typed nodes. A capability-type identifier names a coherent functional aspect of a device — for example, electrical metering, grid-tie status, load-shed control, state-of-charge reporting. A single device may expose multiple capabilities; the same capability identifier appears on devices of different device types (e.g., `energy.ebus.capability.meter` appears on circuits, feed points, and BESS devices alike).

This registry is descriptive, not exhaustive: it lists what is currently registered. Consumers MUST tolerate unknown capability identifiers (e.g., accept and persist their properties; apply only generic Homie handling).

## Format rules

- Identifiers are of the form `energy.ebus.capability.<name>`.
- The `<name>` portion is lowercase kebab-case ASCII: lowercase letters, digits, and hyphens only.
- No leading or trailing hyphens; no consecutive hyphens.
- Identifiers are case-sensitive.

## Registered capability types

The **Source** column references the data-model document where the identifier currently appears.

| Identifier | Description | Source |
|---|---|---|
| `energy.ebus.capability.info` | Static informational properties for a device: name, tags, external IDs, breaker rating, dedicated-circuit flag, and similar. Read-mostly metadata that rarely changes during normal operation. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.config` | Settable configuration properties for a device — values controlling operational policy (e.g., shed thresholds, dispatch parameters). | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.status` | Overall device operational status (e.g., `OK` / `DEGRADED` / `LOST`). Coarse-grained health signal. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.connection` | Communication / link state between the publisher and an upstream subsystem (e.g., inverter link, cloud link). | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.meter` | Electrical measurements: active power, apparent power, energy (imported/exported), voltage, current, frequency, and similar. The most commonly-implemented capability. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.switch` | Switchable on/off control (e.g., a circuit relay). Carries current relay state and accepts `/set` commands. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.door` | Enclosure door state (e.g., `OPEN` / `CLOSED` / `UNKNOWN`). | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.grid` | Grid-tie status: whether the device is currently `ON_GRID` or `OFF_GRID`, and related state information. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.grid-forming` | Grid-forming-inverter behavior (used by BESS that can island the site). Reports grid-forming state and related parameters. *Full semantics pending the BESS data model.* | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) (forward reference) |
| `energy.ebus.capability.soc` | State-of-Charge for energy storage devices. *Full semantics pending the BESS data model.* | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) (forward reference) |
| `energy.ebus.capability.pcs` | Power Conversion System properties — inverter-specific operational data on BESS and PV devices. *Full semantics pending the BESS / PV data models.* | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) (forward reference) |
| `energy.ebus.capability.power-flows` | Aggregate power flows between subsystems (grid, battery, solar, load). Typically appears on the distribution-enclosure parent device. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.priority` | Per-circuit priority for load-shed decisions — controls the order in which circuits drop when shedding is needed. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.shed` | Load-shed control: shed-trigger configuration, shed state, and shed reason. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.shed-forecast` | Forecast of upcoming load-shed events — when shedding is expected to begin or end. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |

## Adding new capability types

New identifiers may be added to this registry as new data-model documents are published. The process:

1. The proposed identifier follows the format rules above.
2. The proposed identifier is genuinely new — not a synonym of an existing entry. If a similar capability already exists, prefer extending the existing one over coining a new identifier.
3. A data-model document defines (or explicitly references) the capability and is the source for the registry row.
4. The proposed identifier is added to this registry with a description and a source reference.
5. This document's version is bumped.

Forward references (a data model that mentions a capability whose full semantics are not yet published) are valid registry entries; they are marked as such in the Source column and re-pointed at the full data model when it lands.

Producers and consumers SHOULD treat unknown capability identifiers as opaque — accept and persist their properties, but apply only the generic Homie / eBus framework defaults. This permits forward-compatibility: a device exposing a newer capability than the consumer knows about should still be handled gracefully.
