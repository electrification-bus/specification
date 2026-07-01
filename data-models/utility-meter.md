# Electrification Bus Utility Meter Data Model Specification

**Status:** DRAFT
**Version:** 0.2
**Date:** 2026-07-01
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

The first three capabilities (`info`, `meter`, `status`) are always present on a conformant utility-meter device — they define what the device is. The latter four (`grid`, `doe`, `demand`, `power-quality`) are populated when the meter exposes the corresponding signal or computes the corresponding quantities; a meter that does not signal a dynamic operating envelope simply omits `doe` from its `$description`.

### Device ID

The device ID is publisher-defined and opaque to consumers. Common conventions are the meter's manufacturer serial number, a UUID assigned at commissioning, or an AMI endpoint identifier. The data model places no constraint on the form. The device ID is the value of `<meter-id>` in topic paths.

### Per-phase representation

Per-phase electrical measurements use property-name suffixes — `-a`, `-b`, `-c` for the three phase positions, `-n` for the neutral position — rather than phase-as-child-device. This matches the lugs precedent in [`distribution-enclosure.md`](distribution-enclosure.md) (`l1-current`, `l2-current`). System aggregates carry no suffix (`active-power`, not `active-power-system`).

The `-a` / `-b` / `-c` letters denote the abstract phase positions of a polyphase service. Mapping to physical conductors depends on the meter form (ANSI form number, published as `info`/`meter-form`):

- A single-phase / 2-wire service populates only `-a` (no `-b`, no `-c`, neutral via `-n` if present).
- A US split-phase / 3-wire residential service (ANSI forms 2S / 12S / similar) populates `-a` and `-b` for the two 240 V-opposed hot conductors, plus `-n`. The two hots are 180° out of phase, not 120° — consumers that need to know this read `info`/`nominal-phase-angle` (typically `180`).
- A three-phase / 4-wire wye service (ANSI forms 9S / 16S / similar) populates `-a` / `-b` / `-c` for the three phase conductors and `-n` for the neutral; `nominal-phase-angle` is typically `120`.
- A three-phase / 3-wire delta service populates `-a` / `-b` / `-c` with no `-n`.

A property whose corresponding phase position is not present on this meter's service is simply not published (framework principle #3).

**Why properties-with-suffix rather than phase-as-child-device.** A utility meter is one physical instrument — one serial number, one firmware, one comm channel, one Homie `$state` lifecycle. Phases are conductors passing through the meter, not sub-entities of it. The Homie device boundary is heavyweight (its own `$description`, `$state`, lifecycle, MQTT presence); using it for phase decomposition would import that weight where it does not pay for itself, break the colocation of system aggregates with their per-phase decomposition, triple device count per meter, and diverge from the Matter, DLMS/COSEM, and DNP3 metering conventions. Full rationale (including the alternative considered and the decision rule for future revisit) is recorded as a decision in the project's bd tracker under issue `SPEC-7si`.

### Utility Meter Capabilities

#### info

Meter identity and nameplate properties. The standard Homie identity properties are reused from the eBus convention; meter-specific nameplate properties are added below them.

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `vendor-name` | string | — | MAY | Meter manufacturer (e.g., `"Landis+Gyr"`, `"Aclara"`, `"Honeywell"`). |
| `serial-number` | string | — | MAY | Meter serial number. |
| `model` | string | — | MAY | Vendor-defined model identifier. |
| `hardware-version` | string | — | MAY | Hardware revision. |
| `firmware-version` | string | — | MAY | Firmware version. |
| `data-model-version` | string | — | MAY | Version of the eBus utility-meter data model this device publishes (e.g., `"0.1"`). |
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

Instantaneous electrical measurements and cumulative energy quantities. Properties are grouped below by scope (system aggregate vs. per-phase) for readability; all are sibling properties under the same `meter` node.

**Node type:** `energy.ebus.capability.meter`

System-level (no phase suffix):

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `frequency` | float | Hz | MAY | System line frequency. |
| `active-power` | float | W | MAY | Total active power across all phases. Sign convention: positive = imported from utility, negative = exported to utility. |
| `reactive-power` | float | VAR | MAY | Total reactive power. |
| `apparent-power` | float | VA | MAY | Total apparent power. Computed per `info`/`calculation-convention` when the meter computes both arithmetic and vectorial forms; the data model exposes only one value. |
| `power-factor` | float | — | MAY | System power factor, signed: positive = lagging (inductive), negative = leading (capacitive); range `[-1.0, 1.0]`. |
| `imported-energy` | float | Wh | MAY | Cumulative active energy delivered by the utility to the customer. Monotonically non-decreasing in normal operation. |
| `exported-energy` | float | Wh | MAY | Cumulative active energy delivered by the customer to the utility. Monotonically non-decreasing. |
| `imported-reactive-energy` | float | VARh | MAY | Cumulative reactive energy delivered. |
| `exported-reactive-energy` | float | VARh | MAY | Cumulative reactive energy received. |

Per-phase (suffix `-a` / `-b` / `-c`, plus `-n` for the neutral conductor where present):

| Property ID pattern | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `voltage-{a,b,c}` | float | V | MAY | RMS voltage on the named phase, line-to-neutral (or line-to-virtual-neutral on a delta service). |
| `current-{a,b,c,n}` | float | A | MAY | RMS current on the named conductor. Neutral current (`current-n`) may be directly measured or imputed from the phase currents; the data model does not distinguish. |
| `active-power-{a,b,c}` | float | W | MAY | Per-phase active power. Sign convention matches the system `active-power`. |
| `reactive-power-{a,b,c}` | float | VAR | MAY | Per-phase reactive power. |
| `apparent-power-{a,b,c}` | float | VA | MAY | Per-phase apparent power. |
| `power-factor-{a,b,c}` | float | — | MAY | Per-phase power factor, signed as for the system value. |
| `voltage-angle-{a,b,c}` | float | ° | MAY | Voltage angle of the named phase, measured relative to phase-A voltage. By convention `voltage-angle-a` is `0`; it MAY be published explicitly or omitted. |
| `current-angle-{a,b,c}` | float | ° | MAY | Current angle of the named phase, measured relative to the same-phase voltage. |

**Encoding notes.** Properties use the engineering-unit values listed (no scaling factor or `µ-` prefix). Cumulative energy quantities are floats in Wh / VARh — sufficient resolution for billing-grade energy from a `float64` Homie property; a publisher whose internal representation is integer micro-Wh converts at publish time. Sign conventions follow IEEE / IEC norms: imported / delivered = positive flow from utility to customer, exported / received = the reverse.

**Forward compatibility.** The full GEISA-style 4-quadrant per-phase + system VA matrix (Q1/Q2/Q3/Q4 × delivered/received × fundamental-only / +harmonics, arithmetic and vectorial flavors) is **not** defined here. The decision is deliberate: the property space above covers the common revenue-metering and energy-management use cases at a manageable surface area, and the quadrant matrix can be added additively to `meter` later when a real consumer (e.g., a commercial demand-charge calculator, a regulated vectorial-jurisdiction billing system) needs it. The vocabulary will be added without renaming existing properties.

#### status

Meter-as-device operational state — distinct from the meter's view of the *grid* (which lives on `grid`).

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `tamper-state` | enum | — | MAY | Tamper-detection result: `NORMAL`, `TAMPER_DETECTED`, `UNKNOWN`. Publishers MAY extend the value space via Homie `$format` to expose meter-specific tamper categorizations (cover open, magnetic interference, reverse-rotation, etc.). |
| `reverse-energy-flag` | boolean | — | MAY | True when the meter has detected net energy flow from customer to utility since the most recent reset or commissioning. Distinct from `exported-energy` being non-zero — this is a discrete flag many meters maintain as an anti-fraud signal. |
| `time-sync-state` | enum | — | MAY | Internal clock synchronization state: `LOCKED`, `UNLOCKED`, `NONE`, `UNKNOWN`. `LOCKED` indicates the meter's clock is currently disciplined by an authoritative time source (NTP, PTP, GPS, AMI head-end, etc.); `UNLOCKED` indicates the meter has a time source configured but is currently free-running; `NONE` indicates no time-sync mechanism. |
| `internal-temperature` | float | °C | MAY | Meter internal temperature, when sensed. |
| `communication-state` | enum | — | MAY | Meter's view of its own AMI / backhaul communication state: `OK`, `DEGRADED`, `LOST`, `UNKNOWN`. Reflects whether the meter believes it can currently report to its head-end; orthogonal to whether the eBus publisher is currently reporting to its consumers. |

#### grid

The meter's **verdict view** of utility supply health, observed at the service entrance. Published when the meter exposes any grid-sensing signal; omitted otherwise.

**Node type:** `energy.ebus.capability.grid`

This is the same capability node type used on MID devices in [`distribution-enclosure.md`](distribution-enclosure.md) — re-used here because a utility meter and a MID are publishing the same conceptual signal (verdict on the state of the AC supply they observe). The property subset each publishes differs: the meter is qualified to publish `grid-state` and grid-event timestamps; it is **not** qualified to publish `islanding-state` (that property describes whether the customer site is currently islanded, which is a MID concern) or `grid-forming-entity` (which describes which device is establishing the AC reference, again a MID concern). Per framework principle #7 (properties belong on the device that authoritatively knows them), the utility-meter omits those properties.

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `grid-state` | enum | — | MAY | Sensed condition of the utility supply: `UP`, `DOWN`, `DEGRADED`, `UNKNOWN`. A revenue-grade utility meter is qualified to distinguish `DEGRADED` (voltage / frequency outside the band for `UP` but not yet a declared outage) from `UP` based on its measurement gear — populating `DEGRADED` rather than collapsing to `UP` / `DOWN` is encouraged where the meter has the underlying capability. |
| `last-outage-time` | datetime | — | MAY | Timestamp of the most recent transition from `UP` (or `DEGRADED`) to `DOWN` observed by the meter. ISO-8601 UTC. |
| `last-restoration-time` | datetime | — | MAY | Timestamp of the most recent transition from `DOWN` to `UP` (or `DEGRADED`) observed by the meter. ISO-8601 UTC. |

#### doe

The utility's **dynamic operating envelope (DOE)** for this service point: the import and export operating envelopes the utility is signaling. Each envelope is a power limit with its source and (where defined) its validity window, optionally delivered as a schedule of upcoming envelopes. Published when the meter is configured to expose this signaling channel; omitted otherwise.

**Node type:** `energy.ebus.capability.doe`

The term *dynamic operating envelope* is from [IEEE 2030.5 / CSIP](https://standards.ieee.org/ieee/2030.5/5897/), where it names the utility-issued operating constraints a customer site agrees to remain within. In Matter 1.5 terminology, the import side of this capability corresponds to the Meter Identification cluster's `PowerThreshold` attribute (Section 9.10 of the Matter 1.5 Application Cluster Specification); the export side has no Matter 1.5 equivalent and is proposed for a future Matter release. In [UL 3141](https://www.shopulstandards.com/ProductDetail.aspx?productId=UL3141) / NEC 2026 Article 130 terms, the import and export limits are PIL (Power Import Limit) and PEL (Power Export Limit) respectively.

The envelope is carried as two `json` properties, one per direction (`import-limit` and `export-limit`), rather than as a family of parallel scalar properties. This follows [framework principle #10](../framework.md#design-principles) (`json` only for atomic compounds): a limit, its source, and its validity window are one envelope that must be read as a unit. Spread across separately-retained scalar topics, a subscriber cannot tell whether the validity window it reads belongs to the limit it reads, or when each was published; one retained object per direction makes each envelope update a single atomic transaction.

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `import-limit` | json | — | MAY | no | The import-side operating envelope: a JSON array of one or more envelope objects (schema below), ordered by `start-time`. Absent when the utility signals no import limit. |
| `export-limit` | json | — | MAY | no | The export-side operating envelope, same schema. Absent when the utility signals no export limit. |

**Envelope object schema.** Each property's value is a JSON **array** of envelope objects (the property carries a `$format` JSONSchema constraining it). A single current envelope is an array of one; a schedule of upcoming envelopes is a longer array. Each object:

```json
{
  "power-limit":          3400,                    // integer W, real-power limit; non-negative
  "apparent-power-limit": 3600,                    // integer VA, optional (Matter apparentPowerThreshold)
  "source":               "GRID",                  // optional enum; absent = UNKNOWN
  "start-time":           "2026-07-01T16:00:00Z",  // optional ISO-8601 UTC; absent = effective now
  "end-time":             "2026-07-01T20:00:00Z"   // optional ISO-8601 UTC; absent = until superseded
}
```

- **At least one** of `power-limit` / `apparent-power-limit` MUST be present; an envelope with neither is meaningless. Both are non-negative integers (a utility-signaled envelope is a setpoint, not a measurement, and is practically delivered at watt-or-VA-or-greater granularity). `power-limit` is UL 3141 PIL / PEL and Matter `PowerThresholdStruct.powerThreshold`; `apparent-power-limit` is Matter `apparentPowerThreshold`.
- **Reactive power is not carried here.** In IEEE 2030.5 / CSIP, reactive-power limits and controls (volt-var, fixed power factor, fixed / max VAr) are per-DER grid-support functions applied at the inverter, not connection-point envelope limits; they belong to a forthcoming `der-control` capability, not `doe`. A `power-limit` (W) together with an `apparent-power-limit` (VA) already bound reactive power at the connection point (`|VAr| <= sqrt(VA^2 - W^2)`).
- `source`: the limit's origin. `CONTRACT` (service contract / customer agreement), `REGULATOR` (permanent regulatory mandate), `EQUIPMENT` (equipment / conductor rating), `GRID` (dynamic utility grid-management action: distribution-transformer protection, DR event, congestion management), `UNKNOWN`. Absent means `UNKNOWN`. `GRID` distinguishes a temporary utility action from a permanent `REGULATOR` mandate, closing a gap in [Matter 1.5's `PowerThresholdSourceEnum`](https://csa-iot.org/all-solutions/matter/).
- `start-time` / `end-time`: ISO-8601 UTC. `start-time` absent means effective immediately; `end-time` absent means in force until superseded by a later publish (typical for static / contract limits).

**Selecting the effective envelope.** The retained array is the utility's complete current schedule for that direction, and each publish replaces it atomically. A subscriber determines the **effective** envelope as the array element whose `[start-time, end-time)` window contains the current time. If two windows overlap, the element with the latest `start-time` wins. If no element's window contains the current time (a gap in the schedule), there is no meter-signaled limit for that direction, and the subscriber falls back to its local equipment / static rating. Time-based selection needs a synced clock; the meter reports its own on `status`/`time-sync-state`.

**Scheduling and the safety asymmetry.** Elements with a future `start-time` are pre-announced upcoming envelopes; a scheduling subscriber applies each as its window becomes current. Because mis-timing a limit is not symmetric, a subscriber that does not implement scheduling MUST behave conservatively: it MAY apply an upcoming **stricter** (lower) limit early, but MUST NOT apply an upcoming **looser** (higher) limit before its `start-time`. Publishers SHOULD prune elements whose `end-time` is already in the past.

**Publish-only.** This capability is publish-only; no `/set` topic is defined. The utility configures the meter's envelope through whatever out-of-band channel the meter and utility have (typically AMI head-end / IEEE 2030.5 / proprietary backhaul). The meter publishes the resulting values to the eBus broker. Subscribers (panels, EMSes, DERMS adapters) cannot tell the meter what envelope to publish; they read the published values and act locally. This separation — utility owns the source of the envelope, meter owns publication, subscribers own enforcement — keeps authorization simple: no subscriber needs write permission to any property on the meter.

**Absence semantics.** Absence of `import-limit` (respectively `export-limit`) means the utility signals no limit in that direction; a subscriber falls back to its local equipment / static rating. An empty array is equivalent to absence. Absence of the `doe` capability node entirely means the meter does not signal an operating envelope at all.

**Why a new capability rather than extending `meter` or `grid`.** A utility-signaled envelope is neither a measurement (meter is for what the meter measures) nor a verdict on grid health (grid). It is a third class of signal — a control input the utility is communicating downstream — and it has a distinct audience (PCS subscribers, EMS panels, DERMS coordinators) and lifecycle (utility-driven, possibly time-bounded). Giving it its own capability keeps the three streams separable on the subscriber side.

**Interaction with the distribution-enclosure's `pcs`.** The `power-limit` of the meter's effective `import-limit` envelope and the panel's `grid-import-limit` are distinct properties on distinct devices: the meter publishes "what the utility is signaling"; the panel publishes "what the panel is currently enforcing from the grid-source CSL slot." For the end-to-end composition (subscription topology, CSL math, commissioning, failure handling), see [Integration Guide: Utility Meter ↔ Distribution Enclosure](../integration-guides/utility-meter-and-distribution-enclosure.md).

**Publishers other than utility meters.** Although this data model defines `doe` in the context of utility meters, the capability itself is publisher-agnostic. Any device that authoritatively knows a utility-signaled operating envelope — a future IEEE 2030.5 / CSIP gateway, a DERMS adapter, an aggregator's site controller — MAY publish this capability per framework principle #7. The property contracts above apply unchanged to any conformant publisher.

#### demand

Peak-average demand quantities for commercial demand-charge billing. Published when the meter computes interval demand; omitted otherwise.

**Node type:** `energy.ebus.capability.demand`

Demand is the time-averaged active power over a fixed integration window (the *demand interval*). Each closed interval yields a single number; the peak across some longer billing period (typically a calendar month) is the basis for a demand charge in many commercial tariffs.

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `integration-window` | integer | s | MAY | Demand integration interval length, in seconds. Common values: `900` (15 min), `1800` (30 min), `3600` (1 hour). |
| `current-interval-demand` | float | W | MAY | Running average over the *currently-open* demand interval. Updates as the interval fills; resets at each interval boundary. |
| `previous-interval-demand` | float | W | MAY | Closed value of the most-recently-completed demand interval. |
| `peak-demand-this-period` | float | W | MAY | The highest `previous-interval-demand` observed since the most recent peak reset. |
| `peak-demand-time` | datetime | — | MAY | Timestamp of the interval that produced `peak-demand-this-period`. ISO-8601 UTC. |
| `peak-demand-reset-time` | datetime | — | MAY | When `peak-demand-this-period` was last reset (typically the start of the current billing period). ISO-8601 UTC. |

The peak-reset semantics — billing-month vs. rolling-30-day vs. since-last-utility-read — are determined by the meter's configuration and are not constrained by this data model. Consumers reading `peak-demand-this-period` should also read `peak-demand-reset-time` to know what window the value covers.

Reactive and apparent demand variants are not included in this v0; they will be added additively if a real consumer requires them.

#### power-quality

Quantitative power-quality measurements. Published when the meter computes them; omitted otherwise.

**Node type:** `energy.ebus.capability.power-quality`

| Property ID pattern | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `thd-voltage-{a,b,c}` | float | % | MAY | Total Harmonic Distortion of voltage on the named phase, as a percentage of the fundamental component. |
| `thd-current-{a,b,c}` | float | % | MAY | Total Harmonic Distortion of current on the named phase, as a percentage of the fundamental. |
| `tdd-current-{a,b,c}` | float | % | MAY | Total Demand Distortion of current on the named phase — like THD-current but normalized to the demand interval's peak current rather than to the instantaneous fundamental. |
| `voltage-unbalance` | float | % | MAY | Voltage unbalance across phases (typically the NEMA definition: max deviation from the average, divided by the average). |

Higher-order harmonic spectra, individual harmonic magnitudes, and disturbance event records (sags, swells, transient captures) are out of scope for v0. They begin to straddle the boundary into the high-rate waveform tier this data model explicitly excludes.

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
