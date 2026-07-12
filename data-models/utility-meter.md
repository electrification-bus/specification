# Electrification Bus Utility Meter Data Model Specification

**Status:** DRAFT
**Version:** 0.6
**Date:** 2026-07-11
**Authors:** Don Jackson

## Overview

This document defines an Electrification Bus (eBus for short) data model for a **utility meter** — the revenue-grade metering device installed by an electric utility at a customer's service entrance, between the utility's distribution system and the customer's premises wiring. The utility meter is the customer site's primary point of measurement for energy billing and the most authoritative observer of the utility supply that the site has.

The data model captures the ≥1 Hz instantaneous electrical measurements (voltage, current, power, frequency), the slower cumulative-energy and demand quantities used for billing, the meter's view of utility supply health, and the meter's own operational state. It is layered on Homie 5 plus eBus's HEI-specific device and capability types and is intended to be vendor-neutral: any meter OEM or proxy publisher with internal access to the underlying values can populate it.

This data model is informed by — but does not depend on or copy — the [GEISA project](https://lfenergy.org/introduction-to-geisa/)'s metering schemas. Where the property vocabulary aligns with GEISA, the alignment is deliberate; where it diverges (notably in conformance posture, in encoding decisions, and in the omission of GEISA's high-sample-rate waveform tier), the divergence is also deliberate. The two specifications are independent.

## Terminology: "utility meter"

This document uses **utility meter** for the device class being modelled. The defining characteristic is that the meter is installed by the **electric utility** at the customer's **service entrance** and is the revenue-class measurement device on which energy billing is based.

The formal industry term in standards literature is *utility electric meter* (or Matter's "Electrical Utility Meter" device type 0x0093). Within eBus the "electric" qualifier is redundant — eBus is the Electrification Bus, every measured quantity in the spec is electrical — so the prose throughout uses the shorter form. The device-type identifier `energy.ebus.device.utility-meter` reflects the same convention. Cross-references to other standards' formal names appear where relevant.

This is distinct from:

- **Sub-meters** — branch-level metering inside the premises (e.g., per-circuit metering inside a distribution enclosure, per-tenant metering in a multi-family building). These are modeled as `meter` instances on whichever eBus device the sub-meter physically attaches to (a circuit, a feedthrough lugs device, etc.), not as standalone `utility-meter` devices.
- **Panel meters / aggregate enclosure metering** — the service-entrance measurements that a distribution enclosure publishes on its own `meter`. The enclosure's measurements are at the *enclosure's* main relay; the utility meter's measurements are at the *utility's* revenue boundary. The two devices may sit a few feet apart and measure nearly the same current, but they are distinct devices, are commissioned independently, and may not even communicate with each other.
- **Power-quality analyzers and recorders** — class-A power-quality instruments and disturbance recorders. A utility meter that exposes PQ measurements via this data model's `power-quality` is doing so as a secondary function; a dedicated PQ analyzer would warrant its own data model (out of scope here).

The data model uses "utility meter" in normative prose. Vendor-specific examples may use whichever term the vendor's product literature uses ("smart meter", "AMI endpoint", "revenue meter", etc.).

## Audience and Scope

This document is the data-model specification for two audiences:

- **Publishers** — utility-meter OEMs implementing the publisher role for their own meter product, or third parties proxying on behalf of a non-eBus-native meter (an AMI head-end system republishing meter data as eBus, an integrator's adapter pulling from a meter's Modbus/DLMS interface and republishing as eBus, etc.).
- **Consumers** — developers writing controller-role API clients that read utility-meter data for energy management, demand response, DERMS coordination, customer-facing displays, billing reconciliation, or analytics.

The model covers:

- The utility-meter device itself, its identity / nameplate, and its capabilities.
- Instantaneous electrical measurements at the ≥1 Hz cadence.
- Cumulative billing energy quantities.
- Peak-demand quantities for commercial demand-charge billing.
- The meter's verdict view of utility supply health (grid-state).
- A useful subset of power-quality measurements (THD, TDD, voltage unbalance) when the meter computes them.
- The meter's own operational status (tamper, time-sync, comm health, etc.).

The model does **not** cover:

- **High-sample-rate waveform data.** Voltage and current waveform streams (per-cycle samples, oscillography records) are out of scope. Such streams are not well-suited to the eBus/Homie/MQTT publish model — they belong on a dedicated streaming transport. A meter that captures waveforms continues to be a valid utility-meter publisher; it simply does not expose the waveform data via this data model.
- **Vendor-specific configuration, provisioning, or programming.** Meter sealing, certificate provisioning, register configuration, AMI command-and-control, firmware update flows — all out of scope.
- **Tariff content and time-of-use schedules.** An eBus consumer that needs to compute tariffed charges from the meter's quantities obtains the tariff schedule out-of-band; the meter publishes raw quantities only.

## Design Principles

This data model follows the Electrification Bus design principles — the Homie devices-vs-nodes split, parent aggregation, proxying as a first-class peer to native publishing, property placement on the authoritative device, forward compatibility, and multi-instance modeling. See **[Design Principles in framework.md](../framework.md#design-principles)** for the canonical list.

One stance is worth surfacing explicitly because it shapes the property tables that follow:

**Wide conformance latitude.** This data model defines a property **vocabulary**, not a conformance gauntlet. Within each capability node, the **vast majority of properties are MAY-level**. A utility meter that publishes only `imported-energy` is a valid `energy.ebus.device.utility-meter`; so is one that publishes the full system + per-phase instantaneous matrix. Publishers populate what they have and omit what they don't (framework principle #3); consumers tolerate sparse publication. The Homie device-type discriminator (`$description.type = energy.ebus.device.utility-meter`) is what identifies a device as a utility meter — not the population of any specific property. This stance is deliberately *more lenient* than [`distribution-enclosure.md`](distribution-enclosure.md) takes; the rationale is that a distribution enclosure is a single integrated product whose vendor controls the whole stack, whereas the utility-meter model targets a long tail of meter OEMs and proxy publishers where any conformance bar above MAY will exclude most candidates. The model is more valuable when broad participation populates it partially than when a strict contract excludes most participants.

---

## Utility Meter Device

**Type:** `energy.ebus.device.utility-meter`

The utility meter device represents the meter itself. It has no eBus-modeled child devices; per-phase electrical measurements are recorded as property-name suffixes on the meter's capability nodes (see *Per-phase representation* below).

```
ebus/5/<meter-id>/                         energy.ebus.device.utility-meter
  info                          Meter identity and nameplate
  meter                         Instantaneous + cumulative electrical measurements
  status                        Meter-as-device operational state
  grid                          Meter's verdict view of utility supply health           (when published)
  doe                           Utility-signaled import/export power limits             (when published)
  demand                        Peak-average demand quantities                          (when published)
  power-quality                 Quantitative power-quality measurements                 (when published)
```

The first three capabilities (`info`, `meter`, `status`) are always present on a conformant utility-meter device — they define what the device is. The latter five (`grid`, `doe`, `price`, `demand`, `power-quality`) are populated when the meter exposes the corresponding signal or computes the corresponding quantities; a meter that does not signal a dynamic operating envelope simply omits `doe` from its `$description`.

### Device ID

The device ID is publisher-defined and opaque to consumers. Common conventions are the meter's manufacturer serial number, a UUID assigned at commissioning, or an AMI endpoint identifier. The data model places no constraint on the form. The device ID is the value of `<meter-id>` in topic paths.

### Per-phase representation

Per-phase electrical measurements use property-name suffixes: `-a`, `-b`, `-c` for the three phase positions and `-n` for the neutral position, rather than phase-as-child-device. This is the shared eBus per-conductor convention; the full property catalog and the split-phase leg mapping are in [`capabilities/meter.md`](../capabilities/meter.md). System aggregates carry no suffix (`active-power`, not `active-power-system`).

The `-a` / `-b` / `-c` letters denote the abstract phase positions of a polyphase service. Mapping to physical conductors depends on the meter form (ANSI form number, published as `info`/`meter-form`):

- A single-phase / 2-wire service populates only `-a` (no `-b`, no `-c`, neutral via `-n` if present).
- A US split-phase / 3-wire residential service (ANSI forms 2S / 12S / similar) populates `-a` and `-b` for the two 240 V-opposed hot conductors, plus `-n`. The two hots are 180° out of phase, not 120° — consumers that need to know this read `info`/`nominal-phase-angle` (typically `180`).
- A three-phase / 4-wire wye service (ANSI forms 9S / 16S / similar) populates `-a` / `-b` / `-c` for the three phase conductors and `-n` for the neutral; `nominal-phase-angle` is typically `120`.
- A three-phase / 3-wire delta service populates `-a` / `-b` / `-c` with no `-n`.

A property whose corresponding phase position is not present on this meter's service is simply not published (framework principle #3).

**Why properties-with-suffix rather than phase-as-child-device.** A utility meter is one physical instrument — one serial number, one firmware, one comm channel, one Homie `$state` lifecycle. Phases are conductors passing through the meter, not sub-entities of it. The Homie device boundary is heavyweight (its own `$description`, `$state`, lifecycle, MQTT presence); using it for phase decomposition would import that weight where it does not pay for itself, break the colocation of system aggregates with their per-phase decomposition, triple device count per meter, and diverge from the Matter, DLMS/COSEM, and DNP3 metering conventions.

### Utility Meter Capabilities

#### info

Meter identity and nameplate properties. The shared identity properties are defined in [`capabilities/info.md`](../capabilities/info.md); the meter-specific metrology and nameplate properties are added below.

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `meter-class` | string | — | MAY | Accuracy class designator (e.g., `"0.2"`, `"0.2S"`, `"0.5"`, `"0.5S"`, `"1.0"`). Free-text; the set of valid values is governed by the relevant metrology standard, not by this spec. |
| `meter-form` | string | — | MAY | ANSI meter form designation (e.g., `"2S"`, `"9S"`, `"16S"`, `"45S"`). Free-text. Determines the meter's service configuration (single-phase / split-phase / three-phase, with/without neutral, transformer-rated vs. self-contained) and therefore which `-a` / `-b` / `-c` / `-n` property positions are populated below. |
| `phases` | integer | — | MAY | Number of phase positions the meter measures (`1`, `2`, or `3`). Distinct from the *wire count* of the service — a US split-phase service is `phases = 2`, not 3. |
| `neutral-connected` | boolean | — | MAY | Is a neutral conductor connected at the meter? When `true`, the `-n` suffixed properties (e.g., `current-n`) may appear under `meter`. |
| `nominal-frequency` | float | Hz | MAY | Nominal supply frequency. Typically `50` or `60`. |
| `nominal-phase-angle` | float | ° | MAY | Nominal angle between adjacent phase positions, in degrees. `120` for three-phase, `180` for US split-phase, `0` or absent for single-phase. |
| `nominal-voltage-line-to-line` | float | V | MAY | Nominal phase-to-phase voltage of the service (e.g., `240`, `208`, `480`). Omitted when not applicable (single-phase service). |
| `nominal-voltage-line-to-neutral` | float | V | MAY | Nominal phase-to-neutral voltage of the service (e.g., `120`, `277`). Omitted when not applicable (delta service without neutral). |
| `calculation-convention` | enum | — | MAY | How the meter computes the derived quantities (reactive and apparent power, power factor, vectorial sums) reported under `meter`: `ARITHMETIC` or `VECTORIAL`. Some jurisdictions (e.g., Canada) prefer vectorial; others prefer arithmetic. Consumers that interpret the derived properties should read this to know how. When the meter exposes only direct measurements (V, I, P) and no derived quantities, this property MAY be omitted. |
| `ct-ratio` | float | — | MAY | Current-transformer ratio for transformer-rated meters (e.g., `40.0` for a 200:5 CT). Self-contained meters MAY omit this property or publish `1.0`. |
| `pt-ratio` | float | — | MAY | Potential-transformer (a.k.a. voltage-transformer) ratio for transformer-rated meters. Self-contained meters MAY omit or publish `1.0`. |
| `register-multiplier` | float | — | MAY | Multiplier applied to internal register counts to produce the engineering-unit values published under `meter`. The meter's published values are already scaled (consumers do not apply this multiplier); the property is published for reference and for billing reconciliation against utility back-office systems. |

Publishers MAY add vendor-specific informational properties to `info` as additional properties; the spec defines only the properties listed above.

#### meter

Instantaneous electrical measurements and cumulative energy. The property catalog (system-level and per-phase quantities, the `-a` / `-b` / `-c` / `-n` per-conductor convention, the sign convention, and encoding notes) is defined in [`capabilities/meter.md`](../capabilities/meter.md).

**Node type:** `energy.ebus.capability.meter`

A utility meter MAY publish any subset, from `imported-energy` alone up to the full system and per-phase instantaneous matrix; all `meter` properties are MAY here (see the wide-latitude stance above). Notes specific to a utility meter:

- **Reference direction** is the default: positive = imported from the utility, negative = exported to the utility.
- **Derived quantities** (`reactive-power`, `apparent-power`, `power-factor`) are computed per the `calculation-convention` on [`info`](#info) (arithmetic vs vectorial).
- **Nameplate and configuration** properties (accuracy class, meter form, CT / PT ratio, register multiplier, neutral-connected, nominal voltages and frequency) live on [`info`](#info) above, not on `meter`.
- The full GEISA-style 4-quadrant per-phase and system VA matrix is not defined yet; it can be added additively to `meter` when a consumer needs it, without renaming existing properties.

#### status

Meter-as-device operational state — distinct from the meter's view of the *grid* (which lives on `grid`). Reused from the eBus [`status`](../capabilities/status.md) capability (the `communication-state` core), with meter-specific diagnostics.

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `tamper-state` | enum | — | MAY | Tamper-detection result: `NORMAL`, `TAMPER_DETECTED`, `UNKNOWN`. Publishers MAY extend the value space via Homie `$format` to expose meter-specific tamper categorizations (cover open, magnetic interference, reverse-rotation, etc.). |
| `reverse-energy-flag` | boolean | — | MAY | True when the meter has detected net energy flow from customer to utility since the most recent reset or commissioning. Distinct from `exported-energy` being non-zero — this is a discrete flag many meters maintain as an anti-fraud signal. |
| `time-sync-state` | enum | — | MAY | Internal clock synchronization state: `LOCKED`, `UNLOCKED`, `NONE`, `UNKNOWN`. `LOCKED` indicates the meter's clock is currently disciplined by an authoritative time source (NTP, PTP, GPS, AMI head-end, etc.); `UNLOCKED` indicates the meter has a time source configured but is currently free-running; `NONE` indicates no time-sync mechanism. |
| `internal-temperature` | float | °C | MAY | Meter internal temperature, when sensed. |
| `communication-state` | enum | — | MAY | Meter's view of its own AMI / backhaul communication state: `OK`, `DEGRADED`, `LOST`, `UNKNOWN`. Reflects whether the meter believes it can currently report to its head-end; orthogonal to whether the eBus publisher is currently reporting to its consumers. |

#### grid

The meter's **verdict view** of utility supply health, observed at the service entrance. Published when the meter exposes any grid-sensing signal; omitted otherwise. Reused from the eBus [`grid`](../capabilities/grid.md) capability: a utility meter publishes only `grid-state` and the outage / restoration timestamps; it is not qualified for `islanding-state` or `grid-forming-entity` (MID concerns) and omits them (framework principle #7).

**Node type:** `energy.ebus.capability.grid`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `grid-state` | enum | — | MAY | Sensed condition of the utility supply: `UP`, `DOWN`, `DEGRADED`, `UNKNOWN`. A revenue-grade meter is qualified to distinguish `DEGRADED` from `UP`; populating it rather than collapsing to `UP` / `DOWN` is encouraged where the meter has the capability. |
| `last-outage-time` | datetime | — | MAY | Timestamp (ISO-8601 UTC) of the most recent transition from `UP` / `DEGRADED` to `DOWN` observed by the meter. |
| `last-restoration-time` | datetime | — | MAY | Timestamp (ISO-8601 UTC) of the most recent transition from `DOWN` to `UP` / `DEGRADED` observed by the meter. |

#### doe

The utility's **dynamic operating envelope (DOE)** for this service point: the import and export operating envelopes the utility is signaling to the meter. Published when the meter is configured to expose this signaling channel; omitted otherwise. The full property catalog — the two `json` envelope arrays, the envelope-object schema, effective-envelope selection, the scheduling safety asymmetry, and the publish-only / absence semantics — is defined in [`capabilities/doe.md`](../capabilities/doe.md).

**Node type:** `energy.ebus.capability.doe`

On a utility meter, `doe` is the **source** representation on eBus: the meter receives the envelope out of band (AMI head-end / IEEE 2030.5 / proprietary backhaul) and publishes it; subscribers (panels, EMSes, DERMS adapters) read it and act locally, and the meter grants no write access. A `source` of `GRID` (a dynamic utility grid-management action) is the case that most exercises the schedule and validity windows; static `CONTRACT` / `REGULATOR` / `EQUIPMENT` limits are typically a single open-ended envelope.

A distribution enclosure that obtains and enforces an envelope publishes its own acting-on representation on *its* `doe` (see [`distribution-enclosure.md`](distribution-enclosure.md)); the meter's `doe` (the utility's signal) and the enclosure's `doe` (what the enclosure is acting on) are distinct authoritative views of the same underlying signal, not competing publishers. For the end-to-end meter → enclosure flow (subscription topology, `pcs` enforcement composition, commissioning, failure handling), see [Integration Guide: Utility Meter ↔ Distribution Enclosure](../integration-guides/utility-meter-and-distribution-enclosure.md).

#### price

The utility's **dynamic price stream** for this service point: the time-varying import and export energy prices the utility is signaling. Published when the meter exposes a pricing channel; omitted otherwise. The full property catalog (the `import-price` / `export-price` schedules and the price-window schema) is defined in [`capabilities/price.md`](../capabilities/price.md).

**Node type:** `energy.ebus.capability.price`

On a utility meter, `price` is the **source** representation on eBus: the meter receives the price out of band (AMI head-end / IEEE 2030.5 pricing channel) and publishes it; subscribers (a panel EMS, price-aware controllers) read it and respond locally. It is the price sibling of `doe`: `doe` is a hard operating limit, `price` an economic incentive. This reports the price, not the rate structure (that is a tariff, a separate concern). Demand charges (currency per kW of peak) are a separate billing dimension and are not carried here; see [`demand`](#demand).

#### demand

Peak-average demand for commercial demand-charge billing. Published when the meter computes interval demand; omitted otherwise. The property catalog (`integration-window`, the interval and peak demand properties, and the peak-reset semantics) is defined in [`capabilities/demand.md`](../capabilities/demand.md).

**Node type:** `energy.ebus.capability.demand`

#### power-quality

Quantitative power-quality figures (harmonic distortion and unbalance). Published when the meter computes them; omitted otherwise. The property catalog (`thd-voltage-*`, `thd-current-*`, `tdd-current-*`, `voltage-unbalance`) is defined in [`capabilities/power-quality.md`](../capabilities/power-quality.md).

**Node type:** `energy.ebus.capability.power-quality`

---

## Examples

The conformance-latitude principle means that two valid utility-meter publishers can have very different published surfaces. The following illustrate the range.

### Minimal compliant meter

A simple residential single-phase meter that exposes only cumulative energy and an active-power reading:

```
ebus/5/meter-7a3f.../$description.type      = energy.ebus.device.utility-meter
ebus/5/meter-7a3f.../info/vendor-name        = "ExampleCorp"
ebus/5/meter-7a3f.../info/serial-number      = "EM-0000-7A3F"
ebus/5/meter-7a3f.../info/phases             = 1
ebus/5/meter-7a3f.../info/nominal-frequency  = 60
ebus/5/meter-7a3f.../meter/active-power      = 1842.3
ebus/5/meter-7a3f.../meter/voltage-a         = 121.8
ebus/5/meter-7a3f.../meter/current-a         = 15.12
ebus/5/meter-7a3f.../meter/imported-energy   = 24817.2
ebus/5/meter-7a3f.../meter/exported-energy   = 0
ebus/5/meter-7a3f.../status/communication-state = "OK"
```

`grid`, `demand`, and `power-quality` are omitted entirely.

### Commercial three-phase meter with demand and PQ

A transformer-rated three-phase commercial meter publishing the full per-phase instantaneous matrix, demand quantities, and basic PQ metrics:

```
ebus/5/meter-c402.../$description.type      = energy.ebus.device.utility-meter
ebus/5/meter-c402.../info/vendor-name              = "ExampleCorp"
ebus/5/meter-c402.../info/model                    = "REV-3P-9S"
ebus/5/meter-c402.../info/meter-form               = "9S"
ebus/5/meter-c402.../info/meter-class              = "0.2S"
ebus/5/meter-c402.../info/phases                   = 3
ebus/5/meter-c402.../info/neutral-connected        = true
ebus/5/meter-c402.../info/nominal-frequency        = 60
ebus/5/meter-c402.../info/nominal-phase-angle      = 120
ebus/5/meter-c402.../info/nominal-voltage-line-to-line     = 480
ebus/5/meter-c402.../info/nominal-voltage-line-to-neutral  = 277
ebus/5/meter-c402.../info/calculation-convention   = "ARITHMETIC"
ebus/5/meter-c402.../info/ct-ratio                 = 80
ebus/5/meter-c402.../info/pt-ratio                 = 1
ebus/5/meter-c402.../meter/frequency               = 59.98
ebus/5/meter-c402.../meter/active-power            = 142337.5
ebus/5/meter-c402.../meter/reactive-power          = 38420.1
ebus/5/meter-c402.../meter/apparent-power          = 147432.7
ebus/5/meter-c402.../meter/power-factor            = 0.965
ebus/5/meter-c402.../meter/voltage-a               = 277.4
ebus/5/meter-c402.../meter/voltage-b               = 277.1
ebus/5/meter-c402.../meter/voltage-c               = 276.9
ebus/5/meter-c402.../meter/current-a               = 178.2
ebus/5/meter-c402.../meter/current-b               = 174.8
ebus/5/meter-c402.../meter/current-c               = 177.5
ebus/5/meter-c402.../meter/current-n               = 4.1
ebus/5/meter-c402.../meter/imported-energy         = 18472134
ebus/5/meter-c402.../meter/exported-energy         = 0
ebus/5/meter-c402.../demand/integration-window     = 900
ebus/5/meter-c402.../demand/current-interval-demand    = 138420
ebus/5/meter-c402.../demand/previous-interval-demand   = 141200
ebus/5/meter-c402.../demand/peak-demand-this-period    = 187320
ebus/5/meter-c402.../demand/peak-demand-time           = "2026-05-22T14:30:00Z"
ebus/5/meter-c402.../demand/peak-demand-reset-time     = "2026-05-01T00:00:00Z"
ebus/5/meter-c402.../power-quality/thd-voltage-a   = 2.1
ebus/5/meter-c402.../power-quality/thd-voltage-b   = 2.0
ebus/5/meter-c402.../power-quality/thd-voltage-c   = 2.2
ebus/5/meter-c402.../power-quality/voltage-unbalance = 0.18
ebus/5/meter-c402.../grid/grid-state               = "UP"
ebus/5/meter-c402.../status/tamper-state           = "NORMAL"
ebus/5/meter-c402.../status/time-sync-state        = "LOCKED"
ebus/5/meter-c402.../status/communication-state    = "OK"
```

Both meters are valid `energy.ebus.device.utility-meter` publishers. Consumers handle the difference by reading what is published and treating absent properties as unknown.

---

## Registry impact

This data model introduces or broadens entries in [`registries/capability-types.md`](../registries/capability-types.md):

- `energy.ebus.capability.doe` — **new** capability type. Utility-signaled import / export power limits (IEEE 2030.5 / CSIP "dynamic operating envelope" terminology). Defined in the context of utility meters but publisher-agnostic — applicable to any device that authoritatively knows a utility-signaled envelope (DERMS adapters, IEEE 2030.5 / CSIP gateways, aggregator site controllers).
- `energy.ebus.capability.demand` — **new** capability type. Peak-average demand quantities; primarily used on utility-meter devices but applicable wherever interval-demand integration is computed.
- `energy.ebus.capability.power-quality` — **new** capability type. Quantitative power-quality measurements (THD, TDD, unbalance); primarily used on utility-meter devices.
- `energy.ebus.capability.grid` — **broadened source.** Currently scoped to MID devices in the registry; the registry note remains to be updated to acknowledge utility-meter as a second publisher class. The MID and the utility-meter publish disjoint subsets of the capability's vocabulary; both are conformant.

The three new capability identifiers (`doe`, `demand`, `power-quality`) are registered in [`registries/capability-types.md`](../registries/capability-types.md) with Source links pointing to this data model.

---

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus design principles](../framework.md#design-principles)
- [Electrification Bus distribution-enclosure data model](distribution-enclosure.md) — for the precedent on `meter`, `grid`, `status`, per-phase property suffixes, and the parent-of-children pattern this data model deliberately does *not* use.
- [Electrification Bus capability-type registry](../registries/capability-types.md)
- [GEISA project](https://lfenergy.org/introduction-to-geisa/) — independent LF Energy effort whose metering schemas informed the property vocabulary here. Electrification Bus and GEISA are independent specifications; alignment is deliberate where it exists, divergence is also deliberate.
- ANSI C12.20 — meter accuracy classes (for `info/meter-class`).
- ANSI C12.10 — meter form designations (for `info/meter-form`).
- IEEE 519 — harmonic limits (for `power-quality/thd-*`, `tdd-*`).
- NEMA MG-1 §14.36 — voltage unbalance definition (for `power-quality/voltage-unbalance`).
- [IEEE 2030.5 / CSIP](https://standards.ieee.org/ieee/2030.5/5897/) — Smart Energy Profile 2.0 / Common Smart Inverter Profile. Source of the "dynamic operating envelope" terminology used in `doe`.
- [UL 3141](https://www.shopulstandards.com/ProductDetail.aspx?productId=UL3141) — Power Control Systems. Source of the PIL / PEL terminology used in `doe`. NEC 2026 Article 130 incorporates PCS requirements into the National Electrical Code.
- Matter 1.5 Meter Identification cluster (0x0B06) — Cross-reference for the import side of `doe` (`PowerThreshold` / `PowerThresholdStruct`). Cluster specifications are published by the Connectivity Standards Alliance.
