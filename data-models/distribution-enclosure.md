# Electrification Bus Distribution Enclosure Data Model Specification

**Status:** DRAFT
**Version:** 0.8
**Date:** 2026-07-11
**Authors:** Don Jackson

## Overview

This document defines an Electrification Bus (eBus for short) data model for an electrical **distribution enclosure** — the device that takes an incoming AC feed in on its upstream lugs, distributes power across branch circuits, and optionally integrates Distributed Energy Resources (DERs) such as battery energy storage systems (BESS), solar PV, and EV charging equipment (EVSE). The upstream feed may come from the utility service (the common case), from an upstream BESS wired between the utility and the enclosure, or from another (parent) distribution enclosure in a multi-enclosure install. The downstream side may similarly feed loads directly, feed a sub-enclosure via feedthrough lugs, or both. The model uses a parent-child device hierarchy with capability-typed nodes, layered on Homie 5 plus eBus's HEI-specific device and capability types.

The data model aspires and attempts to be vendor-neutral. Publisher implementations populate it from whatever internal data sources they have available; eBus consumers interact with it through a single, vendor-agnostic schema. SPAN is the first known implementation; SPAN-tagged examples appear throughout this document for concreteness and are clearly marked as examples — they are illustrative, not normative.

## Terminology: "distribution enclosure"

This document uses **distribution enclosure** as the canonical term for the device class being modelled. The term is borrowed from work by the CSA/Matter Energy Management Working Group, where it serves as an internationally-relevant, comprehensive term that does not privilege any one regional vocabulary. Locally-common synonyms refer to the same device class:

- electrical panel, breaker box, load center (US, residential/light-commercial)
- switchboard (US/UK, commercial)
- consumer unit (UK, residential)
- distribution board (UK / IEC)
- distribution panel (general)

Normative prose in this document uses *distribution enclosure*. Vendor-specific examples may use whichever term that vendor's product literature uses; SPAN's product is called a "panel," so SPAN-tagged examples use "panel."

## Audience and Scope

This document is the data-model specification for two audiences:

- **Publishers** — vendors implementing the publisher role for their own enclosure product, or third parties proxying on behalf of a non-eBus-native enclosure.
- **Consumers** — developers writing controller-role API clients that interact with eBus/Homie distribution enclosures and their children.

The model covers:

- The enclosure device itself and its capabilities (identity, metering, power-flows, status, PCS, shed policy, etc.).
- Child devices for circuit breakers, lugs (service entrance and feedthrough), and integrated MIDs (Microgrid Interconnect Devices).
- DER child devices (BESS, PV, EVSE) — either eBus-native or proxied by the enclosure publisher.
- Connection semantics — how the publisher records what is wired to each connection point inside the enclosure.

The model does **not** cover:

- Vendor-specific configuration mechanisms (UI flows, commissioning APIs, vendor cloud integrations).
- Non-electrical building-management concerns.

## Design Principles

This data model follows the eBus design principles — the Homie devices-vs-nodes split, parent aggregation, proxying as a first-class peer to native publishing, property placement on the authoritative device, forward compatibility, and multi-instance modeling. See **[Design Principles in framework.md](../framework.md#design-principles)** for the canonical list.

---

## Enclosure Device

**Type:** `energy.ebus.device.distribution-enclosure`

The distribution enclosure device represents the enclosure itself — its system-level properties and aggregate measurements. Physical sub-components (circuits, lugs, an integrated MID) are child devices.

```
ebus/5/<enclosure-id>/                     energy.ebus.device.distribution-enclosure
  info                          Enclosure identity (vendor, serial, model, firmware)
  door                          Door state sensor (when present)
  meter                         Enclosure-level aggregate metering (when the enclosure meters its feed)
  power-flows                   Site-level power flow aggregation (when computed)
  pcs                           UL 3141 Power Control Systems (PCS) configuration and state (when the enclosure runs a PCS)
  doe                           Operating envelope the enclosure is acting on (when it obtains and enforces one)
  voltage-response              Import-current reduction when service voltage sags below a threshold (when it runs one)
  price                         Dynamic price stream the enclosure is coordinating to (when it exposes one)
  grid-event                    Grid events the enclosure is coordinating to: DR asks and grid alerts (when it receives them)
  status                        Enclosure system status (when reported)
  shed-forecast                 Off-grid time-remaining forecast (when a BESS is commissioned)
  shed                          Enclosure-wide shed-policy controls (when a BESS is commissioned)

  children:
    <enclosure-id>-lugs-up                 energy.ebus.device.lugs       (service-entrance lugs)
    <enclosure-id>-lugs-dn                 energy.ebus.device.lugs       (feedthrough lugs, when present)
    <enclosure-id>-mid                     energy.ebus.device.mid        (enclosures with an integrated MID)
    <circuit-id> × N                       energy.ebus.device.circuit
    <bess-id>                              energy.ebus.device.bess       (proxied or eBus-native)
    <pv-id>                                energy.ebus.device.pv         (proxied or eBus-native)
    <evse-id>                              energy.ebus.device.evse       (proxied or eBus-native)
```

**Conformance latitude.** Only `info` (identity) and the child circuits the enclosure hosts are intrinsic to a distribution enclosure. `meter`, `power-flows`, `pcs`, `doe`, `price`, `grid-event`, `voltage-response`, `status`, `door`, `shed`, and `shed-forecast` are optional capabilities, published when the product provides them: a smart panel publishes all of them, while a dumb load center or a proxied third-party panel may publish only `info` and its child circuits. Capability presence is itself a signal, the same stance as [`circuit.md`](circuit.md): the `$description.type` discriminator, not the population of any capability, identifies the device as a distribution enclosure.

Each enclosure-side device that *is* an electrical connection point — every circuit, both lugs devices, and the enclosure-integrated MID — also exposes a `connection` node that records what is wired to it (downstream feed) and, where the publisher knows, what feeds it (upstream). The connection records are the enclosure-side topology surface: they identify which circuit feeds which DER, where an UPSTREAM DER (e.g., a BESS wired between utility and the enclosure main lugs) sits, and how enclosures chain together in multi-enclosure installs.

### Enclosure Capabilities

#### info

**Node type:** `energy.ebus.capability.info`

The shared identity properties (`vendor-name`, `serial-number`, `model`, `hardware-version`, `firmware-version`, `data-model-version`) are defined in [`capabilities/info.md`](../capabilities/info.md). An enclosure adds no device-specific identity properties beyond them (`model` values such as `"MAIN_32"` MAY be advertised via Homie `$format`).

Publishers MAY add vendor-specific informational properties (subsystem versions, hardware-revision sub-identifiers, etc.) to `info` as additional properties; the spec mandates only the properties listed above.

#### door

A digitally-monitored access door, when the enclosure has the sensor; omitted otherwise. Defined in [`capabilities/door.md`](../capabilities/door.md) (`state`: `OPEN` / `CLOSED` / `UNKNOWN`).

**Node type:** `energy.ebus.capability.door`

#### meter

Enclosure-level aggregate metering — measurements at the enclosure's main relay (which is the service-entrance feed in single-panel installs, or the feedthrough from an upstream enclosure in multi-enclosure chains).

**Node type:** `energy.ebus.capability.meter`

Published when the enclosure meters its feed; a panel without integrated metering omits this capability. Property definitions and the `-a` / `-b` / `-c` / `-n` per-conductor convention are in [`capabilities/meter.md`](../capabilities/meter.md); `active-power` uses the default reference direction (positive = imported). On an enclosure that meters:

| Property | Req | Notes |
|---|---|---|
| `active-power` | SHOULD | Total enclosure active power. |
| `imported-energy` | SHOULD | Cumulative energy imported from grid. |
| `exported-energy` | SHOULD | Cumulative energy exported to grid. |
| `voltage-{a,b}` | SHOULD | Per-leg voltage (split-phase legs a, b). |
| `current-{a,b}` | SHOULD | Per-leg current. |
| `imported-energy-{a,b}`, `exported-energy-{a,b}` | MAY | Per-leg energy. |

#### power-flows

Site-level aggregate power flows across all energy sources, computed by the enclosure from its children and connected DER. Published when the enclosure computes them; omitted otherwise. Defined in [`capabilities/power-flows.md`](../capabilities/power-flows.md) (`grid` / `battery` / `pv` / `site`, in W).

**Node type:** `energy.ebus.capability.power-flows`

#### pcs

UL 3141 Power Control Systems (PCS) configuration, state, and the family of import-limit properties that the PCS composes and enforces. Published when the enclosure runs a PCS; a panel without a PCS omits this capability.

**The import-limit family.** The PCS enforces an upper bound on power flow into the enclosure, and that bound is multi-sourced: several independent sources can each impose a limit, so the enclosure publishes one slot per source and composes them (see below). (The enclosure's feed is the service entrance in single-panel installs; in multi-enclosure chains a downstream enclosure's feed is the feedthrough from an upstream enclosure — the limit applies at the enclosure's own feed point either way, not specifically at the utility service entrance.) The sources:

- `feed-import-limit` — the **firm** import limit: the commissioned static feed capacity, set at install time (reflects the upstream feed conductor, which may be smaller than the panel's main breaker). Always-present premises-equipment protection; the UL 3141 PCS archetype.
- `grid-import-limit` — the **dynamic** import limit when grid-tied: the enclosure's enforcement of an IEEE 2030.5 Dynamic Operating Envelope (DOE), typically utility-signaled via AMI and mirrored from a utility-meter's `doe`. Time-bounded: present only while an envelope is in effect.
- `off-grid-import-limit` — the import limit when islanded (from BESS / DER).
- `requested-import-limit` — a user- or operator-requested temporary limit (homeowner via mobile app, fleet operator via REST API).
- `undervoltage-import-limit` — the import limit imposed by the enclosure's **voltage-response** (under-voltage current reduction): a standing local setpoint with no external dependency, an always-available baseline of transformer protection beneath the time-bounded `grid-import-limit`. See the [`voltage-response`](#voltage-response) capability.

At any instant the effective limit is `min()` across all enabled import limits: each acts as a ceiling and the most restrictive wins. This composition accommodates multiple independent constraint sources without any single source needing to know about the others. Terminology is anchored on the relevant standards rather than a coined umbrella: UL 3141 (with NEC 2026 Article 130) defines the PCS and the Power Import Limit (PIL) / Power Export Limit (PEL) vocabulary, and the dynamic grid-signaled limit is an IEEE 2030.5 Dynamic Operating Envelope (DOE). The firm and dynamic limits differ in what they protect (premises equipment versus the shared grid) and in whether they are standing or time-bounded, but the enclosure composes them uniformly by `min()`.

**Node type:** `energy.ebus.capability.pcs`

Service rating and capability properties:

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `breaker-rating` | integer | A | SHOULD | Main breaker rating |
| `grid-islandable` | boolean | — | SHOULD | Enclosure can operate off-grid |

PCS state:

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `enabled` | boolean | — | SHOULD | Is the PCS enabled on this enclosure? |
| `active` | boolean | — | SHOULD | Is the PCS actively controlling one or more loads right now? |
| `import-limit` | float | A | SHOULD | The import limit currently being managed to (the active limit chosen from the import-limit family below) |

Import-limit family — each source publishes the same three-property pattern: the limit value, the enablement state (whether it's configured and can apply), and whether it's currently the active limit driving enclosure behavior.

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `feed-import-limit` | float | A | SHOULD | Commissioned static limit reflecting the actual incoming feed capacity. Set at install time. May be less than `breaker-rating` when the upstream feed conductor is smaller than the panel's main breaker (e.g., a 200 A panel wired to a 100 A service feed publishes `feed-import-limit = 100`). |
| `feed-import-limit-enablement` | enum | — | SHOULD | `UNSPECIFIED`, `UNCONFIGURED`, `DISABLED`, `ENABLED` |
| `feed-import-limit-active` | boolean | — | SHOULD | Is feed-import-limit currently being enforced? |
| `grid-import-limit` | float | A | SHOULD | Dynamic limit on grid-side import when grid-tied — typically utility-signaled (a Dynamic Operating Envelope received via AMI / IEEE 2030.5 / a utility-meter's `doe/power-import-limit`, mirrored here by the panel). The slot for "the utility's signal of what we may import right now." |
| `grid-import-limit-enablement` | enum | — | SHOULD | Same enum domain as above |
| `grid-import-limit-active` | boolean | — | SHOULD | Is grid-import-limit currently being enforced? |
| `off-grid-import-limit` | float | A | SHOULD | Maximum power imported when off-grid (from BESS / DER) |
| `off-grid-import-limit-enablement` | enum | — | SHOULD | Same enum domain |
| `off-grid-import-limit-active` | boolean | — | SHOULD | Is off-grid-import-limit currently being enforced? |
| `requested-import-limit` | float | A | SHOULD | User- or operator-requested temporary limit. Examples: a homeowner reducing import via the vendor's mobile app; a fleet operator pushing a limit via REST API. Distinct from utility-signaled limits — those go to `grid-import-limit`. |
| `requested-import-limit-enablement` | enum | — | SHOULD | Same enum domain |
| `requested-import-limit-active` | boolean | — | SHOULD | Is requested-import-limit currently being enforced? |
| `undervoltage-import-limit` | float | A | MAY | The import current limit the enclosure imposes while service voltage is below its voltage-response threshold. Composes with the other slots by `min()`; the configuration is on [`voltage-response`](#voltage-response). |
| `undervoltage-import-limit-enablement` | enum | — | MAY | Same enum domain as above |
| `undervoltage-import-limit-active` | boolean | — | MAY | Is undervoltage-import-limit currently the binding limit (the `min()` winner)? |

Grid-forming-entity identity is **not** carried here — it is published as `grid-forming-entity` on the MID device's `grid`. The property identifies what is establishing the AC voltage/frequency reference the home is synchronized to; its placement on the MID device (rather than the enclosure) keeps it on the device that authoritatively knows. Its value space is open — a Homie device ID or `"GRID"` — so multi-DER installs can identify *which* DER is grid-forming, not just *which class*.

#### doe

The operating envelope the enclosure has obtained and is acting on, published read-only. Published when the enclosure obtains and enforces an operating envelope; omitted otherwise. The property catalog (the `import-limit` / `export-limit` envelope arrays, the envelope-object schema, and the effective-envelope / scheduling / absence semantics) is defined in [`capabilities/doe.md`](../capabilities/doe.md).

**Node type:** `energy.ebus.capability.doe`

Unlike a utility meter's `doe` (the utility's signal at the service point), the enclosure's `doe` is **its** authoritative representation of the envelope it is acting on. An enclosure may be able to obtain an envelope by more than one path — subscribing to a utility meter's `doe`, an OpenADR client, a fleet / DERMS API — and which source it uses is a local policy / configuration decision; the published `doe` reflects the result. A consumer that also sees a utility meter's `doe` reconciles the two itself: they are distinct authoritative views (the utility's signal versus the enclosure's acting-on state), expected to differ transiently, not competing publishers.

**Relationship to `pcs`.** `doe` and `pcs` are distinct and complementary. `doe` carries the full envelope the enclosure is acting on (both directions, with the schedule); `pcs/grid-import-limit` carries the single effective import limit the enclosure is currently enforcing (composed by `min()` with the enclosure's other import limits, per §pcs). The import side of the effective envelope is the source of `grid-import-limit`. The **export side (`doe/export-limit`) is the enclosure's home for a utility-signaled export envelope** — enforcing an export limit is a DER-control concern (curtailing PV / BESS), not an import-limit slot, so it lives on `doe`, not as an export-side `pcs` family.

#### voltage-response

The enclosure's voltage-triggered import-current response: it reduces its import current when service voltage sags below a configured undervoltage threshold, relieving the shared distribution transformer and holding service voltage in band. Published when the enclosure runs a voltage response; omitted otherwise. The property catalog (the static-threshold configuration `nominal-voltage` / `undervoltage-threshold` / `restore-threshold` / `reduced-import-limit`, the optional proportional `response-curve`, and the semantics) is defined in [`capabilities/voltage-response.md`](../capabilities/voltage-response.md).

**Node type:** `energy.ebus.capability.voltage-response`

This capability carries the *configuration* (how the enclosure will respond); the current reduction it imposes is enforced through the `pcs` import-limit family as the `undervoltage-import-limit` slot, composing with the other limits by `min()` (see [§pcs](#pcs)). The threshold is a standing local setpoint with no upstream dependency, so it keeps protecting the transformer even when a signaled `doe` envelope is stale. It carries real-power curtailment (a current limit), distinct from reactive Volt-VAr. v0 covers the undervoltage (import-reduction) direction; an overvoltage (export-reduction) direction is a future additive sibling.

#### price

The dynamic price stream the enclosure (acting as the site EMS) is coordinating to, published read-only. Published when the enclosure exposes a price stream; omitted otherwise. The property catalog (the `import-price` / `export-price` schedules, the price-window schema, and the effective-window / scheduling semantics) is defined in [`capabilities/price.md`](../capabilities/price.md).

**Node type:** `energy.ebus.capability.price`

As with `doe`, the enclosure's `price` is its authoritative representation of the price it is coordinating to — whichever it has obtained, from a source of its choosing (a utility meter's `price`, a market feed, a price server); which source it uses is a local policy / configuration decision. A consumer that also sees a utility meter's `price` reconciles the two itself; they are distinct authoritative views, not competing publishers. The enclosure uses the price to coordinate its DER children economically (charge / discharge and flexible-load timing) — this is *implicit* demand response, distinct from the hard limits it enforces via `doe` / `pcs` and from an explicit `grid-event`.

#### grid-event

The schedule of grid events the enclosure (acting as the site EMS) has received and is coordinating to: demand-response asks (shed / load-up) and grid-condition alerts (conservation calls, critical-peak, grid emergencies), published read-only. Published when the enclosure receives a grid-event feed (an OpenADR 3 VEN, an IEEE 2030.5 DRLC client, or a price-server subscription); omitted otherwise. The property catalog (the `events` schedule, the event-object schema, the severity / voluntary / lifecycle fields, and effective-event selection) is defined in [`capabilities/grid-event.md`](../capabilities/grid-event.md).

**Node type:** `energy.ebus.capability.grid-event`

The enclosure republishes the events it receives so its DER children and site consumers can see the ask; it then decomposes each event and drives its flexible loads through their device-level `flex` control surface. This is the *explicit event* input, distinct from the economic incentive of `price` and the hard limit of `doe`; site-aggregate compliance is reported via `settlement-proof`.

#### status

Enclosure system status. Reused from the eBus [`status`](../capabilities/status.md) capability, with distribution-enclosure network, relay, and configuration diagnostics. Published when the enclosure reports system status; omitted otherwise.

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `relay` | enum | SHOULD | Main relay state (when the enclosure has a whole-panel relay): `OPEN`, `CLOSED`, `UNKNOWN` |
| `cloud-connection` | enum | SHOULD | Cloud connectivity: `CONNECTED`, `UNCONNECTED`, `UNKNOWN` |
| `ethernet` | boolean | SHOULD | Is the Ethernet network interface operational? |
| `wifi` | boolean | SHOULD | Is the Wi-Fi network interface operational? |
| `wifi-ssid` | string | MAY | SSID to which the Wi-Fi network interface is connected. |
| `postal-code` | string | MAY | Configured postal code |
| `time-zone` | string | MAY | Configured time zone |

#### shed-forecast

Computed forecast of how long backup loads stay served when the home is or becomes off-grid. Published only when at least one BESS is commissioned; omitted otherwise. The property catalog (`total-time-remaining`, `time-to-priority-shed`, the full-charge variants, `confidence`, and the enclosure-computes-from-aggregate-BESS-state semantics) is defined in [`capabilities/shed-forecast.md`](../capabilities/shed-forecast.md).

**Node type:** `energy.ebus.capability.shed-forecast`

#### shed

Enclosure-wide shed-policy controls: the consumer-asserted islanding-state for emergencies when the enclosure's own view of islanding state has become untrustworthy, and the BESS SOC threshold that governs SOC-triggered shedding. Published only when at least one BESS is commissioned; omitted otherwise (same presence rule as `shed-forecast`).

**Node type:** `energy.ebus.capability.shed`

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `asserted-islanding-state` | enum | — | MAY | yes | Consumer-asserted islanding-state, consulted only while the enclosure has lost or degraded communication with the MID/BESS. `$format = "NONE,ON_GRID,OFF_GRID"`; default `NONE`. `ON_GRID` / `OFF_GRID` assert that state as the effective islanding-state (see "Effective islanding-state" below), overriding what the enclosure last sensed; `NONE` means no assertion is in force. A consumer asserts only `ON_GRID` or `OFF_GRID`; `NONE` is enclosure-authored (it is the default, and the value the enclosure publishes when it clears an assertion on comm-restore). The Homie `$settable` attribute is statically `true`; the enclosure enforces eligibility at write time (see Runtime acceptance rule below). |
| `soc-threshold` | integer | % | MAY | (impl-defined) | BESS SOC threshold (range 0–100) below which circuits with `load-shed/priority = SOC_THRESHOLD` are auto-shed. Enclosure-wide policy parameter — the same value applies to every SOC_THRESHOLD circuit. Conforming implementations MAY publish this property with `$settable = true` to expose runtime tuning, or MAY publish it read-only with a built-in default. |

**SOC threshold semantics.** A circuit with `load-shed/priority = SOC_THRESHOLD` is shed when the enclosure's aggregate BESS SOC falls below `soc-threshold`. The `<enclosure>/shed-forecast/time-to-priority-shed` value (see §"shed-forecast") forecasts how long until this threshold is reached given current discharge rate. Asserting `asserted-islanding-state = ON_GRID` (accepted only during comm-loss) makes the effective islanding-state on-grid and thereby short-circuits all auto-shed paths, including SOC-triggered shedding.

**Extensibility — supporting additional shed triggers.** An enclosure's supported shed triggers are discoverable from the `$format` attribute on any circuit's `load-shed/priority` property — the enum values listed there are exactly the triggers this enclosure implements. The baseline `UNKNOWN` / `NEVER` / `OFF_GRID` are required of every conforming enclosure; other triggers (`SOC_THRESHOLD`, plus future spec- or vendor-defined extensions) are optional and appear in `$format` only when implemented. Each optional trigger that has a tunable parameter publishes that parameter as a sibling property under `shed`, named as the lowercase-hyphenated form of the enum value (`SOC_THRESHOLD` ↔ `soc-threshold`). When a trigger is in `$format`, its companion property SHOULD be published if the spec defines one; triggers with no tunable (e.g., `OFF_GRID`, which fires unconditionally when islanded) publish no companion. Vendors introducing new triggers should propose them upstream so the spec registry can track them and prevent name collisions.

**Effective islanding-state.** The islanding-state the enclosure acts on is derived, not simply the sensed value. While communication with the MID/BESS is healthy the effective islanding-state is the sensed `<mid>/grid/islanding-state`, and any `asserted-islanding-state` is ignored. While communication is lost or degraded the effective islanding-state is the asserted value when one is in force (`ON_GRID` or `OFF_GRID`), or the last-known sensed value when the assertion is `NONE`. This lets the consumer correct a stale or wrong sensed state precisely in the window where the enclosure can no longer trust its own sensing.

**Effective shed gate:** the enclosure auto-sheds when the effective islanding-state is not `ON_GRID`. Because the assertion already feeds the effective islanding-state, no separate override term is needed: asserting `ON_GRID` yields an effective state of `ON_GRID` and suspends the auto-shed even when the last sensed state was `OFF_GRID`, while asserting `OFF_GRID` forces shedding.

**Runtime acceptance rule.** A consumer write of `ON_GRID` or `OFF_GRID` to `asserted-islanding-state` is accepted only while the enclosure has lost or degraded communication with the MID and/or BESS (observable from `connection/feeds-device-status` or `connection/fed-by-device-status` on whichever connection-owner references the BESS/MID being `LOST` or `DEGRADED`), regardless of the sensed grid-state (`ON_GRID`, `OFF_GRID`, or `UNKNOWN`). The rationale: once comm to the MID/BESS is lost the enclosure can no longer trust its own islanding-state, so the consumer is permitted to assert either direction. Out-of-condition writes (those made while comm to the MID/BESS is healthy) are silently ignored: the published value does not change, which is how consumers detect rejection. A consumer write of `NONE` is likewise ignored: `NONE` is enclosure-authored, and a consumer does not clear an assertion; the enclosure itself returns the property to `NONE` when it reclaims authority (see below).

**Clearing and comm-restore.** The enclosure clears an active assertion by publishing `NONE` as a normal retained value; it MUST NOT retract the topic with an empty retained payload, which would delete the retained state and make the property appear absent to late subscribers. Because `NONE` is a first-class `$format` value, the topic always carries a value. On comm-restore the enclosure resumes following the sensed islanding-state and republishes `NONE`; to avoid prematurely clearing a still-needed assertion when a marginal link flaps, the enclosure SHOULD apply hysteresis to the comm-health signal before treating communication as restored.

**Why static `settable: true` rather than dynamically-toggled.** The Homie 5 `$description` mutability rule restricts `$description` changes to `$state` transitions through `init` / `disconnected` / `lost`. Toggling `$settable` based on real-time eligibility would require cycling `$state` on every transition (and during any comm flapping): heavyweight and visible to consumers. Keeping `settable: true` static and enforcing eligibility at write time avoids this churn at the cost of one specific user-visible quirk: a naive write may be silently ignored. The single `$format` (`NONE,ON_GRID,OFF_GRID`) likewise advertises `NONE` as a settable value even though only the enclosure authors it; that too is enforced at write time. Consumers compute eligibility client-side from the MID/BESS comm-status signals alone (a `LOST` or `DEGRADED` `feeds-device-status` / `fed-by-device-status` on the connection-owner referencing the BESS/MID), offer only `ON_GRID` and `OFF_GRID` as choices, and grey out the control otherwise.

**Why this is a separate capability from `shed-forecast`.** The forecast capability holds read-only computed values; the shed capability holds settable controls. Mixing read and write properties under one capability would muddle the concerns. The two capabilities are siblings on the enclosure device — `shed-forecast` (read) and `shed` (write) — and future shed-related controls (manual force-shed-now, configurable shed-aggressiveness, scheduled shed policies) can be added to `shed` additively.

---

## Child Device Types

### Circuit Device

**Type:** `energy.ebus.device.circuit` — the circuit device type and its full capability catalog (`info`, `connection`, `meter`, `switch`, `breaker`, `load-shed`, `pcs`) are defined in the [circuit data model](circuit.md). This section documents only what is specific to a circuit **hosted in a distribution enclosure**.

Each circuit breaker in the enclosure is an `energy.ebus.device.circuit` child device. The number of circuits depends on the enclosure model. **Device ID:** the circuit UUID (32-char hex), e.g., `12fc9179f236422183e1640fa3eaba59`.

A smart panel typically publishes each circuit with the full capability set (metered, a remotely-controllable `switch`, `breaker` protection, and `load-shed` / `pcs` policy participation); a simpler load center publishes fewer, per the conformance-latitude and capability-presence principles in [`circuit.md`](circuit.md).

#### Enclosure-specific: physical position

A circuit hosted in an enclosure occupies one or more physical positions ("spaces") in the panel, published as a multi-valued `info/spaces` property:

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `spaces` | string | — | SHOULD | Multi-valued (comma-separated) list of the physical panel position(s) the circuit occupies. |

For an ordinary breaker the mapping is direct, read together with `breaker/poles` (the electrical pole count):

- **Single-pole**: one space, e.g. `spaces = "5"`, `breaker/poles = 1`.
- **Two-pole (240 V)**: the two occupied spaces, e.g. `spaces = "7,9"`, `breaker/poles = 2`.

A **multi-load breaker** (a *tandem* sharing one space, or a *quad* across a two-space footprint) is modelled as described in [`circuit.md` §"Multi-load breakers"](circuit.md#multi-load-breakers-tandem-and-quad): a **feed circuit** carries the shared `meter` and `switch` and occupies the space(s), and one **load circuit per load** carries its own `breaker`, is `fed-by` the feed circuit, and has no independent meter or switch. The feed circuit publishes `info/spaces` for the shared footprint (`"3"` for a tandem, `"7,9"` for a quad); each load circuit is located by its `fed-by` reference and MAY carry a manufacturer-specific sub-position label (top / bottom / inside / outside).

"Space" is the panel slot, numbered per the manufacturer's convention (typically odd positions on the left bus and even on the right, or sequential). It is distinct from the electrical pole count (`breaker/poles`) and from the metering and switching granularity, which for a multi-load breaker is the feed circuit, not the individual load.

#### Enclosure-specific: shed-policy participation

The circuit's capabilities are defined in [`circuit.md`](circuit.md). What is specific to a circuit *inside a distribution enclosure* is how its `load-shed` and `pcs` capabilities couple to the enclosure's enclosure-wide shed and PCS policies:

- **`load-shed/priority`** is interpreted against this enclosure. The baseline values `UNKNOWN` / `NEVER` / `OFF_GRID` are supported by every enclosure; the `SOC_THRESHOLD` value (and any future triggers, advertised in the property's `$format`) defers shedding until the enclosure's aggregate BESS SOC falls below `<enclosure>/shed/soc-threshold`. See §"shed" and §"shed — Extensibility".
- When the enclosure's auto-shed logic drives a circuit's relay, the circuit publishes **`switch/relay-requester = LOAD_SHED`**. The **effective shed gate** (the condition under which the enclosure sheds a circuit) is defined in §"shed".
- **`pcs/managed`** and **`pcs/priority`** are consulted by the enclosure's PCS import-limit enforcement to decide which circuits are controlled when the active import limit is binding. See §"pcs".
- A circuit's `switch/relay` is settable only when its `switch/relay-controllable = true`; the enclosure never opens a circuit commissioned as permanently `OFF_GRID` / locked.

Every circuit also publishes `connection` (see §"Connection Capability" below), the shared topology surface used by circuits, lugs, and the MID.

### Lugs Device

**Type:** `energy.ebus.device.lugs`

Physical lug connection point. Each enclosure has upstream lugs (grid connection) and, when the enclosure supports it, downstream lugs (feedthrough for a sub-enclosure or for chaining enclosures).

**Device ID:** `{enclosure-id}-lugs-up` or `{enclosure-id}-lugs-dn`.

#### Lugs Capabilities

**info:**

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `direction` | enum | MUST | `UPSTREAM` or `DOWNSTREAM` |

The wiring relationship between a lugs device and what is wired to it is expressed as a structured `feeds-device-id` / `fed-by-device-id` reference on `connection`, which scales to N DERs and distinguishes downstream-feed from upstream-feed. See §"Connection Capability" below.

**meter:** property definitions are in [`capabilities/meter.md`](../capabilities/meter.md). On a lugs device: `active-power`, `imported-energy`, `exported-energy` are MUST; `current-{a,b}` SHOULD.

**connection:**

What is wired downstream of (or upstream of) this lugs device. See §"Connection Capability" below for the full property catalog. The downstream lugs device typically populates the `feeds-*` triplet (when it feeds a known device); the upstream lugs device typically populates the `fed-by-*` triplet (when fed by something other than the utility, such as an UPSTREAM BESS or an upstream sister enclosure in a multi-enclosure chain).

### MID Device (Enclosure-Integrated)

**Type:** `energy.ebus.device.mid`

Some enclosures have an integrated MID (Microgrid Interconnect Device) that participates in islanding decisions and identifies the grid-forming entity. Enclosures with an integrated MID publish it as a direct child of the enclosure device.

When the MID is external (e.g., shipped as part of a BESS), it is a child of that BESS device per the [Electrification Bus BESS data model](bess.md). The enclosure does not publish a separate MID in that case.

**Device ID:** `{enclosure-id}-mid`.

**Capabilities:** `info`, `grid`, and (when the enclosure-integrated MID is itself a connection point in the enclosure's wiring topology) `connection` — see §"Connection Capability" below.

#### MID Capabilities

**info:**

The shared identity properties (`vendor-name`, `serial-number`, `model`, `firmware-version`, `hardware-version`, `data-model-version`) are defined in [`capabilities/info.md`](../capabilities/info.md); the MID MAY also carry `product-name`. The enclosure-integrated MID's `vendor-name` is the enclosure vendor, and its `data-model-version` tracks the MID's own data-model spec version (independent of the enclosure's `data-model-version`).

**grid:**

Grid connection state, islanding state, and grid-forming-entity identity, published on the enclosure-integrated MID (the enclosure device itself does not publish them). The property catalog (the three properties and their semantics) is defined in [`capabilities/grid.md`](../capabilities/grid.md); the MID makes `islanding-state` MUST.

**Node type:** `energy.ebus.capability.grid`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `islanding-state` | enum | MUST | `ON_GRID`, `OFF_GRID`, `UNKNOWN` (the MID's relay position). |
| `grid-state` | enum | SHOULD | `UP`, `DOWN`, `DEGRADED`, `UNKNOWN` (sensed grid condition). |
| `grid-forming-entity` | string | SHOULD | `"GRID"` when grid-tied, or the DER parent device ID when islanded. |

Native eBus MIDs (per the in-progress MID companion specification) publish additional `grid` properties (`system-state`, `mid-relay-state`, cross-side phase angles, `sync-ready`) and per-side meter children; the three above are the minimum any MID publishes.

**connection** (when the enclosure-integrated MID is a connection point):

See §"Connection Capability" below for the full property catalog.

---

## Connection Capability

An enclosure-side device that is itself an *electrical connection point* — every circuit, both lugs devices, and the enclosure-integrated MID — publishes a `connection` node recording what is wired to it. This is the enclosure-side topology surface: it identifies which circuit feeds which DER, where an UPSTREAM DER (e.g., a BESS wired between utility and the enclosure main lugs) sits, and how enclosures chain together in multi-enclosure installs.

**Node type:** `energy.ebus.capability.connection`

The full property catalog — the `feeds-*` / `fed-by-*` device references, `count`, and the topology attributes `backed-up`, `feeds-role`, `service-rating`, and `overcurrent-protection` — and the general semantics (absence means unknown, both directions are MAY, and how the distributed edges assemble into a site graph) are defined in [`capabilities/connection.md`](../capabilities/connection.md). Within an enclosure, the `feeds-device-status` / `fed-by-device-status` link-health is the enclosure's view of a commissioned DER it polls (never a branch-circuit load); `service-rating` sits on the service-entrance `lugs`; and `backed-up` distinguishes which downstream feeders survive off-grid. The rest of this section documents enclosure-specific usage.

**Mixed-load and unsurveyed circuits.** Most residential branch circuits feed multiple unmarked loads (a "Kitchen" circuit serves several outlets, none of which is individually commissioned). For these circuits the `connection/feeds-*` properties are simply not published — the circuit child device still exists with its `info/name`, `breaker/rating`, `meter/*`, etc., but no specific commissioned downstream-device record is available. A spare breaker with nothing wired to it looks the same. The absence of `feeds-*` does not distinguish "no load wired" from "we have no record" from "multiple loads, none commissioned" — and functionally there is no need to distinguish those cases, because the enclosure has nothing further to say about the connection.

**A single BESS may connect via multiple circuits.** A multi-unit BESS whose units land on separate circuits (rather than aggregating through one gateway feed) is fed by more than one circuit. Each such circuit publishes its own `connection/feeds-*`, and more than one circuit MAY reference the same BESS: either the `bess` parent (each `feeds-device-id = {bess}`) or the specific unit child it feeds (`feeds-device-id = {bess}-battery-{n}`, with `feeds-device-type = energy.ebus.device.battery`). A consumer sums the circuits that reference one BESS (directly, or via a child's Homie `parent` / `root`) to obtain that BESS's total flow. This is distinct from `count`, which stands in for multiple physical units aggregated behind a **single** connection point; here the units are on **distinct** circuits. See [`bess.md`](bess.md) for why a coordinated multi-unit system is one `bess`.

**Connection-point class** is implicit in the publisher's `$description.type` (circuit = feeder-circuit, upstream `lugs` = main-lugs / service entrance, downstream `lugs` = feedthrough, MID = interconnect passthrough); see [`capabilities/connection.md`](../capabilities/connection.md).

**Upstream vs IN_PANEL DERs (no separate `relative-position` property).** The position of a DER relative to the enclosure is derivable from which enclosure-side connection-owner references the DER:

| DER position | Representation |
|---|---|
| IN_PANEL, landing on an enclosure breaker | A `<circuit-X>/connection/feeds-device-id` references the DER |
| IN_PANEL, via feedthrough lugs | `<enclosure>-lugs-dn/connection/feeds-device-id` references the DER |
| UPSTREAM (DER wired between utility and enclosure main lugs) | `<enclosure>-lugs-up/connection/fed-by-device-id` references the DER |
| Not commissioned to this enclosure | No connection-owner references the DER, and the DER is not in `$description.children` |

---

## Proxied DER Representation

This enclosure model proxies DER child devices (BESS, PV, EVSE) when those devices do not yet publish themselves on eBus. The general proxy model — what proxying is, how consumers disambiguate proxied from native representations, and the proxied-device ID convention — is defined in **[data-models/proxy.md](proxy.md)** and applies uniformly across all eBus data models. The remainder of this section covers the enclosure-specific proxy decisions: where enclosure-side knowledge lives, and the per-DER-class property tables.

### Enclosure-side knowledge stays on the enclosure

Per the proxy model's general rule that [proxy-side knowledge stays on the proxy](proxy.md#proxy-side-knowledge-stays-on-the-proxy), two classes of information are enclosure-side facts that the DER child itself cannot publish (because a non-proxying eBus-native publisher would not have them), and so they live on enclosure-side surfaces rather than on the DER child:

- **The wiring relationship between the DER and the enclosure** — which circuit, lugs device, or MID is physically connected to the DER. Recorded on `connection` of the enclosure-side connection-owner (see §"Connection Capability").
- **The enclosure's view of communication-link health to the DER** — whether the enclosure's internal integration is currently reaching the DER. Recorded as `feeds-device-status` / `fed-by-device-status` on the same connection record.

The DER child carries no `feed` property, no `relative-position` property, and no enclosure-↔-DER link-health property. A BESS device publishes its own `status/communication-state` property (the publisher's self-report of adapter-to-BESS communication) — that is a different signal from the enclosure-side link-health, published independently of the enclosure's view.

> **Interim placement.** The *Proxied PV Child* and *Proxied EVSE Child* subsections below are partial PV / EVSE data models, framed as "what the enclosure publishes when proxying." Rules they state are properly per-device-data-model statements, not enclosure-spec statements, and will move to `data-models/pv.md` and `data-models/evse.md` when those per-device data models land. (The BESS equivalent has already moved to [`data-models/bess.md`](bess.md); the general proxy-publication conventions live in [`data-models/proxy.md`](proxy.md).)

### Proxied BESS Child

When no eBus-native BESS publisher is available, the enclosure proxies a BESS child (`energy.ebus.device.bess`) following the [Electrification Bus BESS data model](bess.md), under the proxy-publication conventions in [`proxy.md`](proxy.md). The full device shape — including the MID-child requirement (a premises-wiring grid-forming BESS MUST include one), the synthesized-minimal-MID behavior for hardware that does not present a separable MID, and which children may be omitted — is defined in `bess.md`. The enclosure-specific facts (the DER-to-enclosure wiring and the enclosure's link-health view) are recorded per §"Enclosure-side knowledge stays on the enclosure" above.

### Proxied PV Child

**Type:** `energy.ebus.device.pv`

Published when solar is commissioned but no eBus-native PV publisher exists. The proxied PV child carries identity (vendor/product/serial/nameplate) and — when the proxier has access to per-PV meter readings via its internal integration — instantaneous production.

#### info

**Node type:** `energy.ebus.capability.info`

The shared identity properties (`vendor-name`, `serial-number`, `firmware-version`) are defined in [`capabilities/info.md`](../capabilities/info.md). PV-specific identity properties:

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `product-name` | string | — | SHOULD | Product name. |
| `nameplate-capacity` | float | W | SHOULD | Nameplate capacity. |

#### meter

**Node type:** `energy.ebus.capability.meter`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | SHOULD | Current PV production. Positive = producing. |
| `exported-energy` | float | Wh | MAY | Cumulative energy produced, when integrated metering is available. |

The proxied PV child's wiring relationship to the enclosure is recorded on the enclosure-side connection-owner that feeds it (a circuit or a lugs device) via `connection`, not on the PV child itself.

### Proxied EVSE Child

**Type:** `energy.ebus.device.evse`

Published when an EVSE is integrated with the enclosure but no eBus-native EVSE publisher exists. Some EVSEs connect to the enclosure via a vendor-specific bus (e.g., RS485) without an MQTT/eBus publication path of their own; the enclosure publishes the eBus representation on the EVSE's behalf.

The capabilities below cover the EVSE properties carried on the proxied child plus the settable `config`. A future stand-alone eBus EVSE Device Specification may extract these into a vendor-agnostic spec once the property set grows enough to justify it; for now, the EVSE child shape is defined here.

#### info

**Node type:** `energy.ebus.capability.info`

The shared identity properties (`vendor-name`, `serial-number`, `firmware-version`) are defined in [`capabilities/info.md`](../capabilities/info.md). EVSE-specific identity properties:

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `product-name` | string | SHOULD | Product name. |
| `part-number` | string | MAY | Part number. |

#### meter

**Node type:** `energy.ebus.capability.meter`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | SHOULD | Current charging power delivered to the EV. |
| `imported-energy` | float | Wh | MAY | Cumulative energy delivered to the EV, when integrated metering is available. |
| `advertised-current` | float | A | SHOULD | The current the EVSE is advertising to the EV via the J1772 pilot signal — the actual offered current, computed as the minimum of `charge-limit`'s `installer-max`, `owner-limit`, and `requested-limit`, and any active PCS import limit. |

#### switch

**Node type:** `energy.ebus.capability.switch`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `lock-state` | enum | MAY | EVSE connector lock state: `LOCKED`, `UNLOCKED`, `UNKNOWN`. |

#### status

EVSE operational state. Reused from the eBus [`status`](../capabilities/status.md) capability, with an EVSE-specific operational-state.

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `operational-state` | enum | SHOULD | EVSE operational state: `IDLE`, `CONNECTED`, `CHARGING`, `FAULTED`, `UNKNOWN`. |

#### charge-limit

The EVSE's charge-current ceiling, composed by `min()` from several sources (the installer rating, the owner's standing limit, an external controller's limit), so any source can lower charging for any reason and the lowest wins. The property catalog is defined in [`capabilities/charge-limit.md`](../capabilities/charge-limit.md); the effective offered current is `meter/advertised-current`.

**Node type:** `energy.ebus.capability.charge-limit`

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `installer-max` | integer | A | SHOULD | no | Installer-configured maximum charge current (breaker rating, J1772 derating); the immutable ceiling. |
| `owner-limit` | integer | A | MAY | yes | The owner's charge-current ceiling, held until changed. MUST be ≤ `installer-max`. |
| `requested-limit` | integer | A | MAY | yes | An external controller's (HEMS / grid) charge-current ceiling. |
| `requested-limit-cause` | enum | — | MAY | no | Why the external limit is set: `LOCAL_OPTIMIZATION`, `GRID_OPTIMIZATION`, `UNKNOWN`. |

The proxied EVSE child's wiring relationship to the enclosure — specifically, which circuit feeds the EVSE — is recorded on the enclosure-side connection-owner's `connection` (the circuit's `feeds-device-id` references the EVSE), not on the EVSE child itself.

---

## Device ID Summary

| Device | ID Pattern | Example |
|---|---|---|
| Enclosure | `{enclosure-serial}` | `ab-1234-c5d67` |
| Lugs upstream | `{enclosure-serial}-lugs-up` | `ab-1234-c5d67-lugs-up` |
| Lugs downstream | `{enclosure-serial}-lugs-dn` | `ab-1234-c5d67-lugs-dn` |
| MID (enclosure-integrated) | `{enclosure-serial}-mid` | `ab-1234-c5d67-mid` |
| Circuit | `{circuit-uuid}` | `12fc9179f236422183e1640fa3eaba59` |
| BESS (proxied) | `{proxier-id}-{bess-serial}` | `ab-1234-c5d67-TG123456789` |
| MID under proxied BESS | `{proxier-id}-{bess-serial}-mid` | `ab-1234-c5d67-TG123456789-mid` |
| PV (proxied) | `{proxier-id}-{pv-id}` (where `{pv-id}` is the vendor serial when commissioned, or a publisher-assigned identifier such as `pv-1`, `pv-2`, …) | `ab-1234-c5d67-pv-1` |
| EVSE (proxied) | `{proxier-id}-{evse-id}` (same convention as PV — vendor serial when known, otherwise a publisher-assigned identifier like `evse-1`, `evse-2`, …) | `ab-1234-c5d67-SD123456789` |

Proxied DER IDs in this model follow the general [`{proxier-id}-{proxied-id}` convention](proxy.md#proxied-device-id-convention). The proxier prefix is the enclosure's serial number; the proxied identifier is the BESS hardware serial (typically always known), the PV or EVSE vendor serial when commissioning has captured it, or a publisher-assigned identifier (`pv-1`, `pv-2`, …; `evse-1`, …) otherwise.

### Device ID Stability

| Device Class | Stable across reboot? | Stable across firmware upgrade? | Stable across factory reset? |
|---|---|---|---|
| Enclosure | Yes | Yes | Yes (hardware serial) |
| Lugs, MID, PV (proxied), EVSE (proxied) | Yes | Yes | Yes (derived from enclosure serial) |
| Circuit | Yes | Yes | Implementation-defined |
| BESS (proxied) | Yes | Yes | Yes (derived from proxier serial + BESS serial; both are stable) |

For stability across a proxy-to-native transition, see [proxy.md → ID stability across the proxy-to-native transition](proxy.md#id-stability-across-the-proxy-to-native-transition).

### Child Device Discovery

**All child device classes are identified by the `type` field in their `$description`**, not by device ID format or naming conventions. Device IDs are opaque identifiers.

Each child device's `$description` includes:

- `type` — authoritative device class (e.g., `energy.ebus.device.circuit`, `energy.ebus.device.lugs`)
- `root` — the root device ID (the enclosure serial) — required per Homie 5 for non-root devices
- `parent` — the parent device ID — required per Homie 5 when parent is not the root

The enclosure's `children` array in `$description` is authoritative for parent-child association. Child membership changes are reflected there promptly.

---

## Device Lifecycle & State Management

Device lifecycle follows the [Homie 5 Specification](https://homieiot.github.io/specification/), which is the normative reference.

### State Values

`init`, `ready`, `disconnected`, `sleeping`, `lost`

### State Cascade

The enclosure is the **root device** in the Homie tree. All child devices share the enclosure's MQTT connection. The enclosure's Last Will and Testament (LWT) sets `$state` to `lost` on ungraceful disconnect. Per the Homie spec:

> If a root-device `$state` is `"lost"` then the state of every child device in its tree is also `"lost"`.

Child `$state` topics are **not** updated by the broker on disconnect — consumers must check both the child's `$state` and the root's `$state` to determine effective state.

### Effective State Determination

| Child has `root` set? | Root `$state` | Effective child state |
|---|---|---|
| no | n/a | child's own `$state` |
| yes | not `lost` | child's own `$state` |
| yes | `lost` | `lost` (inherited from root) |

### Adding / Removing Children

Per Homie 5, adding a child device follows this protocol:

1. Publish child `$state` → `init`
2. Publish child `$description` (with `root` and `parent` fields)
3. Set child `$state` → `ready`
4. Set parent `$state` → `init`
5. Update parent `$description` (add child ID to `children` array)
6. Set parent `$state` → `ready`

Removing a child reverses this: clear the child's retained messages, then update the parent `$description`.

**Note:** Due to MQTT message ordering, consistency at any stage in this process cannot be guaranteed. Consumers must handle the race condition where a child appears in `children` before its `$description` is available.

### `$description` Mutability

A device's `$description` may only change when its `$state` is `init`, `disconnected`, or `lost`. Consumers can cache `$description` while a device is `ready`.

---

## Broker Semantics

### Retained Messages

All `$state`, `$description`, and property value topics are published as **retained messages** per the Homie 5 specification. Reconnecting clients rediscover the full topology and current state from retained messages — no need to remember previously-discovered children.

### ACLs

A single authorized client session can subscribe across the enclosure and all of its children (enclosure-derived IDs, circuit UUIDs, BESS serials). No per-child authorization is required.

### Discovery Flow

1. Subscribe to the enclosure's `$description` → receive retained `$description` with `children` array
2. Issue a single batched SUBSCRIBE covering all child topic trees → receive retained `$description` and property messages for each child

This is two rounds regardless of child count — the startup cost is a burst of retained messages, not a per-child round trip.

---

## Capability Type Registry

Standard capability types shared across enclosure, BESS, and future device specs.

**Capability types define a semantic namespace and intent, not a fixed property contract.** The same capability type (e.g., `meter`) may expose different property subsets on different device classes. The authoritative property set for any given capability node is always declared in that device's `$description`. Consumers should read the `$description` schema, not assume a fixed property set from the capability type name alone.

| Capability Type | Description | Used By |
|---|---|---|
| `energy.ebus.capability.info` | Device identity and metadata | All devices |
| `energy.ebus.capability.meter` | Power and energy metering | Enclosure, circuits, lugs, BESS, meters |
| `energy.ebus.capability.soc` | State of charge / energy | BESS, batteries |
| `energy.ebus.capability.grid` | Grid connection, islanding, and grid-forming-entity identity | MID |
| `energy.ebus.capability.grid-forming` | Per-inverter grid-forming capability and current state | Inverters (when vendor exposes the detail) |
| `energy.ebus.capability.status` | Fault and operational status | Enclosure, BESS, adapters |
| `energy.ebus.capability.charge-limit` | EVSE charge-current ceiling (`min()`-composed) | EVSE |
| `energy.ebus.capability.dispatch` | BESS external dispatch controls (setpoints, SOC limits, backup-reserve) | BESS |
| `energy.ebus.capability.switch` | Relay / switch control | Circuits |
| `energy.ebus.capability.breaker` | Overcurrent / fault protection | Circuits |
| `energy.ebus.capability.load-shed` | Load-shed participation (shed class) | Circuits |
| `energy.ebus.capability.connection` | Wiring relationship (downstream and upstream) and enclosure's view of link health | Circuits, lugs, enclosure-integrated MID |
| `energy.ebus.capability.door` | Door state sensor | Enclosure (when applicable) |
| `energy.ebus.capability.power-flows` | Site-level power aggregation | Enclosure |
| `energy.ebus.capability.pcs` | Power Control System (UL 3141); enclosure import limits, per-circuit participation | Enclosure, circuits |
| `energy.ebus.capability.shed-forecast` | Off-grid backup time-remaining forecast (read-only) | Enclosure (when a BESS is commissioned) |
| `energy.ebus.capability.shed` | Enclosure-wide shed-policy controls (consumer-asserted islanding-state, SOC threshold) | Enclosure (when a BESS is commissioned) |

---

## Examples

The examples in this section illustrate the data model using a SPAN-panel implementation as a concrete reference. SPAN is the first known implementation of this data model; the SPAN-specific values, model identifiers, and serial number formats shown below are illustrative — they are not normative requirements of the spec.

### Example 1 (SPAN panel implementation): multi-panel chain with UPSTREAM Tesla Powerwall and Enphase PV landing on a panel breaker

A three-panel SPAN install drawn from a live home. Tesla PW2 is wired upstream of the first panel; Enphase PV inverters land on a circuit in the first panel; the three panels chain via feedthrough lugs.

```
Utility ─→ Tesla PW2 ─→ xy-0001-aaaaa ─→ xy-0002-bbbbb ─→ xy-0003-ccccc
                            │
                            └── Enphase PV (IQ7+) landing on a circuit in xy-0001-aaaaa
```

Each panel is an independent Homie root device on its own MQTT broker. Each broker reports only what its panel knows. The data model accommodates the per-panel views — the wiring topology is the union of `connection` records across the three brokers.

```
─── panel 1 broker (xy-0001-aaaaa) ─────────────────────────────────
ebus/5/xy-0001-aaaaa-lugs-up/                       energy.ebus.device.lugs
  info/direction                                          UPSTREAM
  meter/...
  connection/fed-by-device-id                             "xy-0001-aaaaa-TG000000000001"
  connection/fed-by-device-type                           "energy.ebus.device.bess"
  connection/fed-by-device-status                         OK

ebus/5/xy-0001-aaaaa-lugs-dn/                     energy.ebus.device.lugs
  info/direction                                          DOWNSTREAM
  meter/...
  (no connection/feeds-* — panel 1 does not currently know it feeds panel 2; future commissioning may populate this side of the inter-panel feedthrough)

ebus/5/00000000000000000000000000000001/                  energy.ebus.device.circuit
  info/name                                               "PV"
  connection/feeds-device-id                              "xy-0001-aaaaa-pv-1"
  connection/feeds-device-type                            "energy.ebus.device.pv"
  connection/feeds-device-status                          OK

ebus/5/xy-0001-aaaaa-pv-1/                                  energy.ebus.device.pv  (proxied)
  info/vendor-name                                        "Enphase Energy"
  info/product-name                                       "IQ7PLUS-72-x-US-&"
  info/nameplate-capacity                                 6000
  meter/...

ebus/5/xy-0001-aaaaa-TG000000000001/                      energy.ebus.device.bess  (proxied)
  info/vendor-name                                        "Tesla"
  info/product-name                                       "Powerwall 2 AC"
  info/serial-number                                      "TG000000000001"
  info/nameplate-capacity                                 81
  info/data-model-version                                 "1.0"
  soc/soc                                                 100.0
  soc/soe                                                 81.0
  status/communication-state                                    OK

ebus/5/xy-0001-aaaaa-TG000000000001-mid/                  energy.ebus.device.mid  (proxied; synthetic — Tesla does not expose its MID separately)
  info/serial-number                                      "TG000000000001-mid"
  grid/islanding-state                                    ON_GRID
  grid/grid-state                                         UP
  grid/grid-forming-entity                                "GRID"

─── panel 2 broker (xy-0002-bbbbb) ─────────────────────────────────
ebus/5/xy-0002-bbbbb-lugs-up/                       energy.ebus.device.lugs
  connection/fed-by-device-id                             "xy-0001-aaaaa"
  connection/fed-by-device-type                           "energy.ebus.device.distribution-enclosure"
  connection/fed-by-device-status                         OK

ebus/5/xy-0002-bbbbb-lugs-dn/                     energy.ebus.device.lugs
  (no connection/feeds-* — panel 2 does not currently know it feeds panel 3)

ebus/5/xy-0002-bbbbb-TG000000000001/                      energy.ebus.device.bess  (proxied — panel 2's view from its own integration)
  info/serial-number                                      "TG000000000001"
  soc/soc                                                 100.0
  status/communication-state                                    OK
  ⟶ no panel-2 connection-owner references this BESS — BESS is not directly wired to panel 2

ebus/5/xy-0002-bbbbb-pv-1/                                energy.ebus.device.pv  (proxied — panel 2's view; same physical PV as panel 1's)
  info/...
  ⟶ no panel-2 connection-owner references this PV — PV is wired to a circuit in panel 1

─── panel 3 broker (xy-0003-ccccc) ─────────────────────────────────
ebus/5/xy-0003-ccccc-lugs-up/                       energy.ebus.device.lugs
  connection/fed-by-device-id                             "xy-0002-bbbbb"
  connection/fed-by-device-type                           "energy.ebus.device.distribution-enclosure"
  connection/fed-by-device-status                         OK

ebus/5/xy-0003-ccccc-lugs-dn/                     energy.ebus.device.lugs
  (no connection/feeds-* — terminus, nothing downstream)

ebus/5/xy-0003-ccccc-TG000000000001/                      energy.ebus.device.bess  (proxied — panel 3's view)
  info/serial-number                                      "TG000000000001"

ebus/5/xy-0003-ccccc-pv-1/                                energy.ebus.device.pv  (proxied — panel 3's view)
```

Note the proxied-device ID convention: each panel's proxy of the same physical Tesla PW gets a panel-specific device ID (`xy-0001-aaaaa-TG000000000001`, `xy-0002-bbbbb-TG000000000001`, `xy-0003-ccccc-TG000000000001`). All three share the same `info/serial-number = "TG000000000001"` — consumers correlate the proxies by serial number, not by device ID.

This install illustrates several aspects of the data model working together:

- **UPSTREAM DER**: the Tesla PW is wired upstream of panel 1's main lugs. Panel 1's `lugs-up` device carries `connection/fed-by-device-id = "xy-0001-aaaaa-TG000000000001"` and `fed-by-device-type = energy.ebus.device.bess` — the only place in the enclosure tree where the BESS-as-upstream wiring is captured.
- **IN_PANEL DER on a circuit**: the Enphase PV lands on a circuit in panel 1; that circuit's `connection/feeds-device-id = "xy-0001-aaaaa-pv-1"` records the link.
- **Inter-panel chain via `lugs-dn` → `lugs-up`**: today, only the receiving end (each panel's `lugs-up/connection/fed-by-device-id`) records the inter-panel link. The downstream-side `feeds-*` triplet is not populated by current SPAN firmware; future commissioning may capture it. The chain is fully traversable from either end of any link.
- **Same physical DER proxied by multiple enclosures**: each panel publishes its own view of the Tesla PW (from its own internal integration), under a distinct enclosure-prefixed device ID. The three proxies share the same `info/serial-number`. A consumer aggregating across brokers dedupes by serial number, not device ID. All three proxies are identifiable as proxies because their `root` is a `distribution-enclosure` device (not the BESS itself) — see [proxy.md → Disambiguating proxied from native publishers](proxy.md#disambiguating-proxied-from-native-publishers).
- **Wiring authority lives on the enclosure that owns the wiring**: only panel 1 has `connection` records referencing the BESS and PV (because panel 1 is the enclosure physically wired to them). Panels 2 and 3 carry proxy children for those DERs but no `connection` records — that combination conveys "these enclosures know about the DERs but are not directly wired to them."

### Example 2 (SPAN panel implementation): single panel with Tesla Powerwall on a panel breaker

A simpler single-enclosure scenario for contrast with Example 1. A SPAN MAIN 32 panel with a Tesla Powerwall commissioned to a 100 A dipole panel breaker (circuit 7) and an EVSE landing on a 60 A dipole panel breaker (circuit 5). System is grid-tied at the moment of capture.

```
ebus/5/ab-1234-c5d67/                          energy.ebus.device.distribution-enclosure
  info/vendor-name                              "SPAN"
  info/serial-number                            "ab-1234-c5d67"
  info/model                                    "MAIN_32"
  info/firmware-version                         "26.10.0"
  info/data-model-version                       "1.0"
  door/state                                    CLOSED
  meter/active-power                            2145.6
  meter/voltage-a                               121.3
  meter/voltage-b                               121.1
  power-flows/grid                              -2750.0
  power-flows/battery                           0.0
  power-flows/pv                                5530.0
  power-flows/site                              2740.0
  pcs/breaker-rating                            200
  pcs/grid-islandable                           true
  status/relay                                  CLOSED
  status/cloud-connection                       CONNECTED
  shed-forecast/total-time-remaining            720
  shed-forecast/time-to-priority-shed           480
  shed-forecast/full-charge-total-time-remaining 720
  shed-forecast/full-charge-time-to-priority-shed 480
  shed-forecast/confidence                      HIGH
  shed/asserted-islanding-state                 NONE
  shed/soc-threshold                            50

ebus/5/ab-1234-c5d67-lugs-up/             energy.ebus.device.lugs
  info/direction                                UPSTREAM
  meter/active-power                            2145.6
  meter/imported-energy                         99828300.0
  meter/exported-energy                         5990700.0
  (no connection/fed-by-* — upstream is the utility, not modeled)

ebus/5/ab-1234-c5d67-lugs-dn/           energy.ebus.device.lugs
  info/direction                                DOWNSTREAM
  meter/active-power                            382.2
  meter/imported-energy                         8905683.0
  meter/exported-energy                         6600577.0
  (no connection/feeds-* — no feedthrough feed)

ebus/5/<circuit-7-id>/                          energy.ebus.device.circuit
  info/name                                     "Powerwall"
  info/spaces                               "7,9"
  breaker/poles                                 2
  breaker/rating                                100
  meter/active-power                            0.0
  switch/relay                                  CLOSED
  load-shed/priority                        NEVER
  switch/relay-controllable                     true
  connection/feeds-device-id                    "ab-1234-c5d67-TG123456789"
  connection/feeds-device-type                  "energy.ebus.device.bess"
  connection/feeds-device-status                OK

ebus/5/<circuit-5-id>/                          energy.ebus.device.circuit
  info/name                                     "EV Charger"
  info/spaces                               "3,5"
  breaker/poles                                 2
  breaker/rating                                60
  info/tags                                     "EVSE"
  meter/active-power                            5350.0
  switch/relay                                  CLOSED
  load-shed/priority                        SOC_THRESHOLD
  switch/relay-controllable                     true
  connection/feeds-device-id                    "ab-1234-c5d67-SD123456789"
  connection/feeds-device-type                  "energy.ebus.device.evse"
  connection/feeds-device-status                OK

ebus/5/<circuit-1-id>/                          energy.ebus.device.circuit
  info/name                                     "Kitchen"
  info/spaces                               "1"
  breaker/poles                                 1
  breaker/rating                                20
  meter/active-power                            245.3
  switch/relay                                  CLOSED
  load-shed/priority                        NEVER
  switch/relay-controllable                     true
  (no connection/feeds-* — mixed-load circuit, no specific commissioned downstream device)

  ... (more circuits, most without connection/feeds-* records)

ebus/5/ab-1234-c5d67-TG123456789/               energy.ebus.device.bess  (proxied)
  info/vendor-name                              "Tesla"
  info/serial-number                            "TG123456789"
  info/data-model-version                       "1.0"
  soc/soc                                       98.5
  soc/soe                                       80.1
  status/communication-state                          OK

ebus/5/ab-1234-c5d67-TG123456789-mid/           energy.ebus.device.mid  (proxied; synthetic)
  info/serial-number                            "TG123456789-mid"
  grid/islanding-state                          ON_GRID
  grid/grid-state                               UP
  grid/grid-forming-entity                      "GRID"

ebus/5/ab-1234-c5d67-SD123456789/                energy.ebus.device.evse  (proxied)
  info/vendor-name                              "SPAN"
  info/product-name                             "SPAN Drive"
  info/serial-number                            "SD123456789"
  meter/active-power                            5350.0
  charge-limit/installer-max                    48
  charge-limit/owner-limit                      40
```

Consumer derivation: a scan of enclosure-side connection records finds `<circuit-7-id>/connection/feeds-device-type == energy.ebus.device.bess` → the BESS is IN_PANEL on circuit 7. Same scan finds `<circuit-5-id>/connection/feeds-device-type == energy.ebus.device.evse` → the EVSE is IN_PANEL on circuit 5. Wiring relationships are recorded once, on the connection-owner that physically owns the wiring; no per-DER-class "feed" or "relative-position" property is needed on the DER children.

---

## References

- [eBus — ebus.energy](https://ebus.energy/) — eBus specification home
- [Homie 5 Specification](https://homieiot.github.io/specification/) — the underlying IoT convention this data model builds on
- [Homie Convention Discussion #338](https://github.com/homieiot/convention/discussions/338) — parent-child device model rationale
- [Electrification Bus BESS data model](bess.md) — companion data-model spec covering the BESS device shape (proxied or natively published).
- [SPAN-API-Client-Docs (public)](https://github.com/spanio/SPAN-API-Client-Docs) — public API documentation for the SPAN-panel implementation of this data model
- [Connectivity Standards Alliance (CSA)](https://csa-iot.org/) — home of the Matter Energy Management Working Group, source of the "distribution enclosure" terminology used in this document
- [UL 3141](https://www.shopulstandards.com/ProductDetail.aspx?productId=UL3141) — Standard for Power Control Systems (referenced by `pcs`)
