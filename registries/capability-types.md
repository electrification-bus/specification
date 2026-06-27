# Electrification Bus Capability Type Registry

**Status:** DRAFT v0.3
**Date:** 2026-06-26
**Authors:** Don Jackson

## Purpose

This document is the canonical registry of `energy.ebus.capability.*` capability-type identifiers used across all Electrification Bus (eBus for short) data models. Data-model documents reference identifiers from this registry; new identifiers are added to this registry when a data-model document introduces them.

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
| `energy.ebus.capability.info` | Device identity and metadata. On the enclosure parent: vendor name, serial number, model, hardware/firmware version, data-model version. On circuits, lugs, and other child devices: device-specific identifiers and descriptive properties. Appears on all devices. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.config` | Settable configuration properties for a device — runtime-tunable values controlling operational behavior. Appears on BESS and EVSE (e.g., EVSE's `user-max-charge-current`). | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.status` | Device operational status. On the enclosure: main relay state, cloud connectivity, network interface state, and system configuration (postal code, time zone). On BESS and adapters: fault and operational status. Appears on enclosure, BESS, and adapter devices. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.connection` | Wiring topology — what is wired downstream of (and, where known, upstream of) this device. Properties identify the connected device by Homie ID and `$description.type`; one property carries the enclosure's view of communication-link health to the fed device. Appears on every enclosure-side device that is itself an electrical connection point: every circuit, both lugs devices, and the enclosure-integrated MID. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.meter` | Electrical measurements: active power, imported/exported energy, and per-line voltages, currents, and per-line energies. Appears on devices that report electrical measurements: enclosure (service-entrance aggregate), circuits, lugs, BESS, and dedicated meters. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.switch` | Switchable on/off control (e.g., a circuit relay). Carries current relay state and accepts `/set` commands. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.door` | Enclosure door state (e.g., `OPEN` / `CLOSED` / `UNKNOWN`). | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.grid` | Grid connection, islanding state, and grid-forming-entity identity. Carries properties like `islanding-state` (`ON_GRID` / `OFF_GRID` / …), `grid-state`, and `grid-forming-entity`. Primarily appears on MID devices. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.grid-forming` | Per-inverter grid-forming capability and current state — exposed by inverters whose vendor surfaces this detail. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.soc` | State-of-Charge and energy properties for energy storage devices (BESS, batteries). | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.pcs` | UL 3141 Power Control Systems (PCS) configuration, state, and the family of Configurable Service Limit (CSL) properties that the PCS manages. Appears on the distribution-enclosure parent device. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.power-flows` | Aggregate power flows between subsystems (grid, battery, solar, load). Typically appears on the distribution-enclosure parent device; also on an all-in-one (plug-in) BESS. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.output-island` | Device-output island (UPS) state and control for a plug-in BESS / UPS: the device forms an island of its own `outlet` children, isolated from premises wiring. Carries `state` (`PASS_THROUGH` / `ON_BATTERY` / `NO_OUTPUT`), a settable `mode` (`FOLLOW_INPUT` / `ISLAND`), and `transfer-time`. Distinct from the premises-wiring `grid` (MID) island scope, and nests inside it. (The backup-runtime forecast is not here; a plug-in BESS reuses `shed-forecast`.) | [`data-models/bess.md`](../data-models/bess.md) |
| `energy.ebus.capability.priority` | Per-circuit load-shedding policy and relay-control authority. Includes `shed-priority` (when to shed: `OFF_GRID`, `SOC_THRESHOLD`, `NEVER`, etc.), `relay-controllable` (whether the relay can be controlled at all), and PCS management metadata. Appears on circuits. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.shed` | Enclosure-wide shed-policy controls. Currently exposes a homeowner `override` (for emergencies when the sensed islanding state has become untrustworthy) and the BESS `soc-threshold` that governs SOC-triggered shedding. Published only when at least one BESS is commissioned to the enclosure. | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md) |
| `energy.ebus.capability.shed-forecast` | Computed forecast of how long backup loads will continue to be served when off-grid. Includes `total-time-remaining`, `time-to-priority-shed`, full-charge equivalents, and a confidence indicator. Computed by the distribution enclosure from aggregate BESS SOE plus per-circuit configuration and history, or by a plug-in BESS for its own outlet loads (which it authoritatively knows). | [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md), [`data-models/bess.md`](../data-models/bess.md) |
| `energy.ebus.capability.doe` | Utility-signaled dynamic operating envelope — the power-import / -export limits the utility is signaling for the site (UL 3141 PIL / PEL, Matter `PowerThresholdStruct` equivalent, IEEE 2030.5 / CSIP "DOE" terminology), with source attribution (`CONTRACT` / `REGULATOR` / `EQUIPMENT` / `GRID` / `UNKNOWN`) and per-limit validity windows. Publish-only — no `/set` topic. Appears on utility-meter devices and on any other publisher with authoritative knowledge of a utility-signaled envelope (a future IEEE 2030.5 / CSIP gateway, a DERMS adapter, an aggregator's site controller). | [`data-models/utility-meter.md`](../data-models/utility-meter.md) |
| `energy.ebus.capability.demand` | Peak-average demand quantities for commercial demand-charge billing — demand-interval length, current and previous interval demand, peak demand for the current billing period with its occurrence timestamp and reset-time. Appears on utility-meter devices and other publishers with interval-demand computation. | [`data-models/utility-meter.md`](../data-models/utility-meter.md) |
| `energy.ebus.capability.power-quality` | Quantitative power-quality measurements (THD / TDD, individual harmonics, voltage unbalance, and similar PQ metrics). Appears on utility-meter devices that compute the measurements and on dedicated power-quality analyzers. | [`data-models/utility-meter.md`](../data-models/utility-meter.md) |

## Adding new capability types

New identifiers may be added to this registry as new data-model documents are published. The process:

1. The proposed identifier follows the format rules above.
2. The proposed identifier is genuinely new — not a synonym of an existing entry. If a similar capability already exists, prefer extending the existing one over coining a new identifier.
3. A data-model document defines (or explicitly references) the capability and is the source for the registry row.
4. The proposed identifier is added to this registry with a description and a source reference.
5. This document's version is bumped.

Forward references (a data model that mentions a capability whose full semantics are not yet published) are valid registry entries; they are marked as such in the Source column and re-pointed at the full data model when it lands.

Producers and consumers SHOULD treat unknown capability identifiers as opaque — accept and persist their properties, but apply only the generic Homie / eBus framework defaults. This permits forward-compatibility: a device exposing a newer capability than the consumer knows about should still be handled gracefully.
