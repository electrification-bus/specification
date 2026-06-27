# Electrification Bus Distribution Enclosure Data Model Specification

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-05-17
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
  door                          Door state sensor (when applicable)
  meter                         Enclosure-level aggregate metering
  power-flows                   Site-level power flow aggregation
  pcs                           UL 3141 Power Control Systems (PCS) configuration and state
  status                        Enclosure system status
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

Each enclosure-side device that *is* an electrical connection point — every circuit, both lugs devices, and the enclosure-integrated MID — also exposes a `connection` node that records what is wired to it (downstream feed) and, where the publisher knows, what feeds it (upstream). The connection records are the enclosure-side topology surface: they identify which circuit feeds which DER, where an UPSTREAM DER (e.g., a BESS wired between utility and the enclosure main lugs) sits, and how enclosures chain together in multi-enclosure installs.

### Enclosure Capabilities

#### info

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `vendor-name` | string | MUST | Enclosure manufacturer (e.g., "SPAN"). |
| `serial-number` | string | MUST | Enclosure serial number. |
| `model` | string | MUST | Vendor-defined model identifier (e.g., "MAIN_32"). The set of valid values is publisher-defined and may be advertised via Homie `$format` on this property. |
| `hardware-version` | string | SHOULD | Hardware revision. |
| `firmware-version` | string | MUST | Firmware version. |
| `data-model-version` | string | SHOULD | Version of the eBus distribution-enclosure data model this device publishes (e.g., `"1.0"`). |

Publishers MAY add vendor-specific informational properties (subsystem versions, hardware-revision sub-identifiers, etc.) to `info` as additional properties; the spec mandates only the properties listed above.

#### door

Some distribution enclosures expose a digitally-monitored door (for access to breakers, terminals, etc.). Enclosures with such a sensor publish this capability; enclosures without one omit it.

**Node type:** `energy.ebus.capability.door`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `state` | enum | MUST | Door state: `OPEN`, `CLOSED`, `UNKNOWN`. |

#### meter

Enclosure-level aggregate metering — measurements at the enclosure's main relay (which is the service-entrance feed in single-panel installs, or the feedthrough from an upstream enclosure in multi-enclosure chains).

**Node type:** `energy.ebus.capability.meter`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | MUST | Total enclosure active power |
| `imported-energy` | float | Wh | MUST | Cumulative energy imported from grid |
| `exported-energy` | float | Wh | MUST | Cumulative energy exported to grid |
| `l1-voltage` | float | V | SHOULD | Line 1 voltage |
| `l2-voltage` | float | V | SHOULD | Line 2 voltage |
| `l1-current` | float | A | SHOULD | Line 1 current |
| `l2-current` | float | A | SHOULD | Line 2 current |
| `l1-imported-energy` | float | Wh | MAY | Line 1 imported energy |
| `l2-imported-energy` | float | Wh | MAY | Line 2 imported energy |
| `l1-exported-energy` | float | Wh | MAY | Line 1 exported energy |
| `l2-exported-energy` | float | Wh | MAY | Line 2 exported energy |

#### power-flows

Site-level aggregate power flows across all energy sources. The enclosure computes these from its children and connected DER devices.

**Node type:** `energy.ebus.capability.power-flows`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `grid` | float | W | MUST | Grid power flow (positive = importing from grid) |
| `battery` | float | W | SHOULD | Battery power flow (positive = discharging) |
| `pv` | float | W | SHOULD | Solar PV power flow (positive = producing) |
| `site` | float | W | MUST | Total site power consumption |

#### pcs

UL 3141 Power Control Systems (PCS) configuration, state, and the family of Configurable Service Limit (CSL) properties that the PCS manages.

**What a CSL is.** A *Configurable Service Limit* is a per-source upper bound on power flow into the enclosure that the PCS enforces. (The enclosure's feed is the service entrance in single-panel installs; in multi-enclosure chains a downstream enclosure's feed is the feedthrough from an upstream enclosure — the CSL applies at the enclosure's own feed point either way, not specifically at the utility service entrance.) The enclosure publishes one CSL slot per logical source of constraint:

- `feed-import-limit` — the commissioned static feed capacity (set at install time; reflects the upstream feed conductor, which may be smaller than the panel's main breaker).
- `grid-import-limit` — the dynamic grid-tied limit when on-grid (typically utility-signaled — the panel mirrors a Dynamic Operating Envelope received via AMI / IEEE 2030.5 / a utility-meter's `doe`).
- `off-grid-import-limit` — the import limit when islanded (from BESS / DER).
- `requested-import-limit` — a user- or operator-requested temporary limit (homeowner via mobile app, fleet operator via REST API).

At any instant the effective limit is `min()` across all enabled CSLs: each CSL acts as a ceiling and the most restrictive wins. This composition accommodates multiple independent constraint sources without any single source needing to know about the others. The term *Configurable Service Limit* is Electrification Bus vocabulary, not UL 3141 standard terminology — UL 3141 defines the PCS itself; the CSL family is the eBus convention for how a PCS exposes its multi-source constraint state.

**Node type:** `energy.ebus.capability.pcs`

Service rating and capability properties:

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `breaker-rating` | integer | A | MUST | Main breaker rating |
| `grid-islandable` | boolean | — | MUST | Enclosure can operate off-grid |

PCS state:

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `enabled` | boolean | — | SHOULD | Is the PCS enabled on this enclosure? |
| `active` | boolean | — | SHOULD | Is the PCS actively controlling one or more loads right now? |
| `import-limit` | float | A | SHOULD | The import limit currently being managed to (the active limit chosen from the CSL family below) |

CSL family — each CSL publishes the same three-property pattern: the limit value, the enablement state (whether it's configured and can apply), and whether it's currently the active limit driving enclosure behavior.

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

Grid-forming-entity identity is **not** carried here — it is published as `grid-forming-entity` on the MID device's `grid`. The property identifies what is establishing the AC voltage/frequency reference the home is synchronized to; its placement on the MID device (rather than the enclosure) keeps it on the device that authoritatively knows. Its value space is open — a Homie device ID or `"GRID"` — so multi-DER installs can identify *which* DER is grid-forming, not just *which class*.

#### status

Enclosure system status.

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `relay` | enum | MUST | Main relay state: `OPEN`, `CLOSED`, `UNKNOWN` |
| `cloud-connection` | enum | SHOULD | Cloud connectivity: `CONNECTED`, `UNCONNECTED`, `UNKNOWN` |
| `ethernet` | boolean | SHOULD | Is the Ethernet network interface operational? |
| `wifi` | boolean | SHOULD | Is the Wi-Fi network interface operational? |
| `wifi-ssid` | string | MAY | SSID to which the Wi-Fi network interface is connected. |
| `postal-code` | string | MAY | Configured postal code |
| `time-zone` | string | MAY | Configured time zone |

#### shed-forecast

Computed forecast of how long backup loads will continue to be served when the home is or becomes off-grid. Published only when at least one BESS is commissioned to the enclosure; omitted entirely otherwise.

**Node type:** `energy.ebus.capability.shed-forecast`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `total-time-remaining` | integer | min | SHOULD | At current SOE (aggregate across all commissioned BESSs), total time before the enclosure goes dark — all backed-up circuits unpowered. |
| `time-to-priority-shed` | integer | min | SHOULD | At current SOE, time until circuits with `shed-priority = SOC_THRESHOLD` are auto-shed. |
| `full-charge-total-time-remaining` | integer | min | SHOULD | At 100% SOE, total backup duration capability. |
| `full-charge-time-to-priority-shed` | integer | min | SHOULD | At 100% SOE, capability time until the SOC_THRESHOLD shed event. |
| `confidence` | enum | — | SHOULD | Algorithm's self-assessed confidence in the forecast: `LOW`, `MEDIUM`, `HIGH`. Reflects accumulated usage history. |

The forecast is **enclosure-knowledge** — it is computed by the enclosure from the aggregate BESS SOE across all commissioned BESS children, the per-circuit `shed-priority` configuration, and the per-circuit consumption history. It cannot be computed by a BESS in isolation; this is why the forecast lives on the enclosure rather than on the BESS child.

**Multi-BESS:** when the enclosure has more than one commissioned BESS, the forecast values are computed against the aggregate SOE across all of them. The published surface is a single set of values; per-BESS forecast detail is not currently exposed (and is not needed for the consumer-visible "how long do my loads stay up?" question).

**No-BESS case:** when no BESS is commissioned, the enclosure omits `shed-forecast` from its `$description` entirely. Presence of the capability ⇔ at least one BESS is commissioned.

#### shed

Enclosure-wide shed-policy controls — the homeowner override for emergencies when the enclosure's view of islanding state has become untrustworthy, and the BESS SOC threshold that governs SOC-triggered shedding. Published only when at least one BESS is commissioned; omitted otherwise (same presence rule as `shed-forecast`).

**Node type:** `energy.ebus.capability.shed`

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `override` | boolean | — | MAY | yes | Homeowner-asserted override. When `true`, the enclosure treats the home as on-grid for load-shedding purposes regardless of the sensed `<mid>/grid/islanding-state`. Default `false`. The Homie `$settable` attribute is statically `true`; the enclosure enforces eligibility at write time (see Runtime acceptance rule below). |
| `soc-threshold` | integer | % | MAY | (impl-defined) | BESS SOC threshold (range 0–100) below which circuits with `priority/shed-priority = SOC_THRESHOLD` are auto-shed. Enclosure-wide policy parameter — the same value applies to every SOC_THRESHOLD circuit. Conforming implementations MAY publish this property with `$settable = true` to expose runtime tuning, or MAY publish it read-only with a built-in default. |

**SOC threshold semantics.** A circuit with `priority/shed-priority = SOC_THRESHOLD` is shed when the enclosure's aggregate BESS SOC falls below `soc-threshold`. The `<enclosure>/shed-forecast/time-to-priority-shed` value (see §"shed-forecast") forecasts how long until this threshold is reached given current discharge rate. Setting `override = true` short-circuits all auto-shed paths including SOC-triggered shedding.

**Extensibility — supporting additional shed triggers.** An enclosure's supported shed triggers are discoverable from the `$format` attribute on any circuit's `priority/shed-priority` property — the enum values listed there are exactly the triggers this enclosure implements. The baseline `UNKNOWN` / `NEVER` / `OFF_GRID` are required of every conforming enclosure; other triggers (`SOC_THRESHOLD`, plus future spec- or vendor-defined extensions) are optional and appear in `$format` only when implemented. Each optional trigger that has a tunable parameter publishes that parameter as a sibling property under `shed`, named as the lowercase-hyphenated form of the enum value (`SOC_THRESHOLD` ↔ `soc-threshold`). When a trigger is in `$format`, its companion property SHOULD be published if the spec defines one; triggers with no tunable (e.g., `OFF_GRID`, which fires unconditionally when islanded) publish no companion. Vendors introducing new triggers should propose them upstream so the spec registry can track them and prevent name collisions.

**Effective shed gate:** the enclosure auto-sheds when `<mid>/grid/islanding-state != ON_GRID` AND `<enclosure>/shed/override != true`. Setting `override = true` short-circuits the auto-shed even when the sensed state is `OFF_GRID`.

**Runtime acceptance rule.** A write of `true` to `override` is accepted only when both conditions hold: (a) the MID's `<mid>/grid/islanding-state` is `OFF_GRID`, AND (b) the enclosure has lost or degraded communication with the MID and/or BESS (observable from `connection/feeds-device-status` or `connection/fed-by-device-status` on whichever connection-owner references the BESS/MID being `LOST` or `DEGRADED`). Out-of-condition writes of `true` are silently ignored — the published `override` value does not change, which is how consumers detect rejection. A write of `false` (clearing an active override) is unconditionally accepted; clearing one's own override does not require the comm-loss condition.

**Why static `settable: true` rather than dynamically-toggled.** The Homie 5 `$description` mutability rule restricts `$description` changes to `$state` transitions through `init` / `disconnected` / `lost`. Toggling `$settable` based on real-time eligibility would require cycling `$state` on every transition (and during any comm flapping) — heavyweight and visible to consumers. Keeping `settable: true` static and enforcing eligibility at write time avoids this churn at the cost of one specific user-visible quirk: a naive write may be silently ignored. Consumers compute eligibility client-side from `islanding-state` plus the MID/BESS comm-status signals and grey out the UI accordingly.

**Why this is a separate capability from `shed-forecast`.** The forecast capability holds read-only computed values; the shed capability holds settable controls. Mixing read and write properties under one capability would muddle the concerns. The two capabilities are siblings on the enclosure device — `shed-forecast` (read) and `shed` (write) — and future shed-related controls (manual force-shed-now, configurable shed-aggressiveness, scheduled shed policies) can be added to `shed` additively.

---

## Child Device Types

### Circuit Device

**Type:** `energy.ebus.device.circuit`

Each circuit breaker in the enclosure is a child device. The number of circuits depends on the enclosure model.

**Device ID:** The circuit UUID (32-char hex), e.g., `12fc9179f236422183e1640fa3eaba59`.

#### Circuit Capabilities

**info:**

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `name` | string | — | MUST | yes | User-assigned circuit name (e.g., "Kitchen", "Dryer"). Free-text. |
| `tab-number` | integer | — | MUST | no | Physical tab position in the enclosure. |
| `dipole` | boolean | — | MUST | no | Is this a 240V double-pole circuit? |
| `breaker-rating` | integer | A | SHOULD | no | Breaker amperage rating. |
| `dedicated` | boolean | — | MAY | no | True when commissioning has explicitly marked this circuit as serving a single load; false when explicitly marked as a mixed-load circuit; omitted when no determination has been recorded. Absence is *not* equivalent to false. |
| `tags` | string | — | MAY | no | Controlled vocabulary of circuit-load type tags identifying the load(s) physically connected to the circuit (e.g., `WATER_HEATER`, `AC_CONDENSER`, `RANGE`, `EVSE`, `DRYER`, `PUMP`). Multi-valued: a comma-separated list of tags from the vocabulary. Single-tag for a dedicated-load circuit; multi-tag for a mixed-load circuit. See [`registries/circuit-tags.md`](../registries/circuit-tags.md) for the full vocabulary, naming conventions, and multi-tag semantics. |
| `external-ids` | string | — | MAY | no | Multi-valued list of opaque identifiers from external systems that reference the load(s) on this circuit. Each item is of the form `<scheme>:<identifier>` where the scheme prefix names the foreign system that issued the identifier (e.g., `matter:0x123ABC`, `zigbee:00:11:22:33:44:55:66:77`, `vendor:tesla:wall-connector-42`). Multi-valued: a comma-separated list. See [`registries/external-id-schemes.md`](../registries/external-id-schemes.md) for currently-defined scheme prefixes and per-scheme identifier formats. |

**meter:**

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | MUST | Circuit active power |
| `imported-energy` | float | Wh | MUST | Cumulative energy imported |
| `exported-energy` | float | Wh | MUST | Cumulative energy exported |
| `current` | float | A | SHOULD | RMS current |

**switch:**

Circuit relay control.

**Node type:** `energy.ebus.capability.switch`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `relay` | enum | MUST | Relay state: `OPEN`, `CLOSED`, `UNKNOWN`. Settable when the circuit's `priority/relay-controllable = true`; not settable when `relay-controllable = false`. |
| `relay-requester` | enum | SHOULD | Source attribution — who or what last drove the relay state. Canonical values: `USER` (a user request via API, mobile app, etc.); `LOAD_SHED` (load-shedding logic, informed by the circuit's `shed-priority` and the enclosure's grid/SOC state); `PCS` (UL 3141 PCS power-control/management); `CONFIGURATION` (installer commissioning or user configuration — a deliberate setting, typically long-lived); `FAULT` (a fault condition such as overcurrent); `NONE` (no actor has driven the relay; it is in its natural/default state); `UNKNOWN` (the publisher cannot determine). Vendors MAY extend the enum via Homie `$format` with implementation-specific values for finer-grained attribution. |

**priority:**

Load shedding policy and relay control authority for the circuit.

**Node type:** `energy.ebus.capability.priority`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `shed-priority` | enum | MUST | Shedding priority. Baseline values (required of every conforming enclosure): `UNKNOWN`, `OFF_GRID`, `NEVER`. Optional values (advertised in this property's `$format` when the enclosure implements them): `SOC_THRESHOLD` and any future spec- or vendor-defined extensions. The `SOC_THRESHOLD` value defers shedding until the BESS aggregate SOC falls below the enclosure-wide threshold published at `<enclosure>/shed/soc-threshold`. See §"shed — Extensibility" for the convention linking optional trigger values to their tunable parameters. Settable on user-configurable circuits; locked (Homie `$settable = false`) on circuits commissioned as permanently OFF_GRID. |
| `relay-controllable` | boolean | MUST | True = the circuit's relay can be controlled (by the enclosure's auto-shed logic *or* by direct user-set). False = the relay is locked closed and cannot be opened by any path; the `switch/relay` property's `$settable` attribute is also `false` in that case. |
| `pcs-managed` | boolean | MAY | Is this circuit managed by the enclosure's PCS? |
| `pcs-priority` | integer | MAY | PCS priority ranking for this circuit. Used by the PCS import-limit-enforcement logic to decide which circuits get controlled when the active CSL is binding. |

**connection:**

What is wired downstream of (and, where the publisher knows, upstream of) this circuit. See §"Connection Capability" below for the full property catalog — the same capability is published by every enclosure-side device that *is* an electrical connection point (every circuit, both lugs devices, the enclosure-integrated MID).

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

**meter:**

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | MUST | Active power at this lug connection |
| `imported-energy` | float | Wh | MUST | Cumulative energy imported |
| `exported-energy` | float | Wh | MUST | Cumulative energy exported |
| `l1-current` | float | A | SHOULD | Line 1 current |
| `l2-current` | float | A | SHOULD | Line 2 current |

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

Standard identity properties (`vendor-name`, `serial-number`, `product-name`, `model`, `firmware-version`, `hardware-version`). The enclosure-integrated MID's `vendor-name` is the enclosure vendor, and the `data-model-version` on the MID device tracks the MID's data-model spec version (independent of the enclosure's `data-model-version`).

**grid:**

Grid connection state, islanding state, and grid-forming-entity identity. This is the canonical home for these three properties; the enclosure device itself does not publish them.

**Node type:** `energy.ebus.capability.grid`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `islanding-state` | enum | MUST | Current operational state: `ON_GRID`, `OFF_GRID`, `UNKNOWN`. Reflects the MID's relay position (are we electrically connected to the utility?). |
| `grid-state` | enum | SHOULD | Sensed grid condition: `UP`, `DOWN`, `DEGRADED`, `UNKNOWN`. Reflects what the MID senses about the grid itself. `DEGRADED` (grid quality outside the band for `UP` but not yet declared an outage) is OPTIONAL — publishers SHOULD distinguish it when they have the underlying measurement capability; proxied black-box MIDs typically report only `UP`/`DOWN`/`UNKNOWN`. `islanding-state` and `grid-state` can differ — a system can be `OFF_GRID` with `grid-state = UP` (intentional island) or `OFF_GRID` with `grid-state = DOWN` (outage). |
| `grid-forming-entity` | string | SHOULD | Identity of the device currently establishing the AC voltage/frequency reference. Value: `"GRID"` when grid-tied, or the Homie device ID of the grid-forming device (typically the DER parent device ID, e.g., the BESS) when islanded. Empty string or absent during transitions or when unknown. In a multi-DER islanded chain where more than one DER is technically capable of grid-forming, exactly one is the actual reference at any given moment, and its parent device ID is the published value; behavior during simultaneous grid-forming (parallel BESSs) is implementation-defined and out of scope here. |

Native eBus MIDs (those implementing the in-progress eBus MID data-model specification — a separate companion document) publish additional `grid` properties (`system-state` 8-state machine, `mid-relay-state`, cross-side phase angles, `sync-ready`, etc.) and per-side meter children. The three properties above are the minimum surface any MID — proxied or native — MUST/SHOULD publish.

**connection** (when the enclosure-integrated MID is a connection point):

See §"Connection Capability" below for the full property catalog.

---

## Connection Capability

An enclosure-side device that is itself an *electrical connection point* — every circuit, both lugs devices, and the enclosure-integrated MID — publishes a `connection` node recording what is wired to it. This is the enclosure-side topology surface: it identifies which circuit feeds which DER, where an UPSTREAM DER (e.g., a BESS wired between utility and the enclosure main lugs) sits, and how enclosures chain together in multi-enclosure installs.

**Node type:** `energy.ebus.capability.connection`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `feeds-device-id` | string | MAY | Homie device ID of the device wired *downstream* of this connection point. Published only when the specific downstream device is known. Omitted when unknown, when the circuit is mixed-load with no specific commissioned downstream device, or when nothing is connected. |
| `feeds-device-type` | string | MAY | `$description.type` of the downstream-connected device (e.g., `energy.ebus.device.bess`, `.pv`, `.evse`, `.distribution-enclosure`). Published when the downstream device class is known, even if the specific device ID is not. Omitted when the class is not known. |
| `feeds-device-status` | enum | MAY | Enclosure's view of communication-link health to the fed device: `OK`, `LOST`, `DEGRADED`. Published only when `feeds-device-id` is published AND the enclosure has a communication integration with that device (typical for commissioned DERs the enclosure polls via an internal backup integration; never applicable for regular branch-circuit loads). |
| `fed-by-device-id` | string | MAY | Homie device ID of the device wired *upstream* of this connection point. Published only when known. Typical populated cases: an UPSTREAM BESS wired between utility and the enclosure main lugs, or an upstream sister enclosure in a multi-enclosure chain. Omitted when the upstream side is the utility (not modeled as an eBus device), when the upstream side is the enclosure busbar (implicit, not modeled), or when the publisher does not know. |
| `fed-by-device-type` | string | MAY | `$description.type` of the upstream-connected device. Published with `fed-by-device-id`. Omitted when the latter is omitted. |
| `fed-by-device-status` | enum | MAY | Enclosure's view of communication-link health to the upstream device. Same value domain and applicability rules as `feeds-device-status`. |
| `count` | integer | MAY | When the connected node aggregates multiple physical units (e.g., 4 microinverters on one AC string reported as one solar device, or 6 battery packs in one BESS), how many. |

**Absent properties mean "unknown."** A property in this capability is published only when the publisher has data for it. Empty strings are not used as sentinels for "unknown" — an unpublished property is the unknown signal, in keeping with Homie convention. The seven properties divide into three groups that are typically published together as a unit: the `feeds-*` triplet, the `fed-by-*` triplet, and `count`. Each group is independent.

**Both directions are MAY-level; populate when known.** The model defines both the `feeds-*` and `fed-by-*` triplets so any enclosure implementation can record connection metadata in either direction as it learns it. A publisher populates the side(s) it knows. Implementations that, today, know what feeds them via the upstream lugs device (the `fed-by-*` side, in the inter-enclosure chain or the upstream-BESS case) and what is fed by circuits and feedthrough lugs when a specific DER is commissioned (the `feeds-*` side) will populate those sides; the other side stays unpublished until commissioning data captures it. Consumers must not assume both directions are populated; the absence of a counterpart record is information, not error.

**Mixed-load and unsurveyed circuits.** Most residential branch circuits feed multiple unmarked loads (a "Kitchen" circuit serves several outlets, none of which is individually commissioned). For these circuits the `connection/feeds-*` properties are simply not published — the circuit child device still exists with its `info/name`, `info/breaker-rating`, `meter/*`, etc., but no specific commissioned downstream-device record is available. A spare breaker with nothing wired to it looks the same. The absence of `feeds-*` does not distinguish "no load wired" from "we have no record" from "multiple loads, none commissioned" — and functionally there is no need to distinguish those cases, because the enclosure has nothing further to say about the connection.

**Connection-point class is implicit in the publisher's device class.** Consumers do not need an extra discriminator field — they read the publisher's `$description.type`:

| Publishing device's `$description.type` | Connection-point class |
|---|---|
| `energy.ebus.device.circuit` | feeder-circuit (load fed through a breaker) |
| `energy.ebus.device.lugs` (downstream) | feedthrough-lugs |
| `energy.ebus.device.lugs` (upstream) | main-lugs (service entrance) |
| `energy.ebus.device.mid` | MID passthrough |

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

The DER child carries no `feed` property, no `relative-position` property, and no enclosure-↔-DER link-health property. A BESS device publishes its own `status/communication` property (the publisher's self-report of adapter-to-BESS communication) — that is a different signal from the enclosure-side link-health, published independently of the enclosure's view.

> **Interim placement.** The next three subsections — *Proxied BESS Child*, *Proxied PV Child*, *Proxied EVSE Child* — are partial BESS / PV / EVSE data models, framed as "what the enclosure publishes when proxying." Rules they state, such as "a conformant BESS publisher MUST include a MID child device," are properly BESS-data-model statements, not enclosure-spec statements. They will move to `data-models/bess.md`, `data-models/pv.md`, and `data-models/evse.md` when those per-device data models land in this repository. The general proxy-publication conventions themselves already live in [`data-models/proxy.md`](proxy.md).

### Proxied BESS Child

When no eBus-native BESS publisher is available, the enclosure proxies a BESS child device.

**Type:** `energy.ebus.device.bess` (same type as an eBus-native BESS)

A conformant BESS publisher MUST include a MID child device — including for proxied BESSs. The proxied BESS child therefore consists of the parent BESS device (typically with `info`, `soc`, `status`) plus a MID child device (`<bess-id>-mid`) carrying `info` and `grid` (with `islanding-state`, `grid-state`, and `grid-forming-entity`). When the underlying BESS hardware does not present a separable MID, the enclosure synthesizes a minimal MID child — the islanding state and grid-forming-entity values are enclosure-known (from the same internal integration) and are always populatable. Individual battery / inverter children are omitted unless the internal integration provides per-component data. The full BESS device shape is defined in the [Electrification Bus BESS data model](bess.md).

### Proxied PV Child

**Type:** `energy.ebus.device.pv`

Published when solar is commissioned but no eBus-native PV publisher exists. The proxied PV child carries identity (vendor/product/serial/nameplate) and — when the proxier has access to per-PV meter readings via its internal integration — instantaneous production.

#### info

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `vendor-name` | string | — | MUST | PV system manufacturer (e.g., "Enphase Energy", "SolarEdge"). |
| `product-name` | string | — | SHOULD | Product name. |
| `serial-number` | string | — | SHOULD | PV system serial number. May be absent when commissioning did not record a specific serial. |
| `firmware-version` | string | — | MAY | PV system firmware version, when the integration reports it. |
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

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `vendor-name` | string | MUST | EVSE manufacturer. |
| `product-name` | string | SHOULD | Product name. |
| `part-number` | string | MAY | Part number. |
| `serial-number` | string | SHOULD | EVSE serial number. |
| `firmware-version` | string | MAY | EVSE firmware version. |

#### meter

**Node type:** `energy.ebus.capability.meter`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | SHOULD | Current charging power delivered to the EV. |
| `imported-energy` | float | Wh | MAY | Cumulative energy delivered to the EV, when integrated metering is available. |
| `advertised-current` | float | A | SHOULD | The current the EVSE is advertising to the EV via the J1772 pilot signal — the actual offered current, computed as the minimum of `config/max-charge-current`, `config/user-max-charge-current`, and any active PCS import limit. |

#### switch

**Node type:** `energy.ebus.capability.switch`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `lock-state` | enum | MAY | EVSE connector lock state: `LOCKED`, `UNLOCKED`, `UNKNOWN`. |

#### status

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `operational-state` | enum | SHOULD | EVSE operational state: `IDLE`, `CONNECTED`, `CHARGING`, `FAULTED`, `UNKNOWN`. |

#### config

**Node type:** `energy.ebus.capability.config`

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `max-charge-current` | integer | A | MUST | no | Installer-configured maximum charge current. Reflects breaker rating and J1772 derating. |
| `user-max-charge-current` | integer | A | SHOULD | yes | User-configured maximum charge current ceiling. MUST be ≤ `max-charge-current`. |

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
| `energy.ebus.capability.config` | Settable configuration | BESS, EVSE |
| `energy.ebus.capability.switch` | Relay / switch control | Circuits |
| `energy.ebus.capability.priority` | Load shedding policy and relay control authority | Circuits |
| `energy.ebus.capability.connection` | Wiring relationship (downstream and upstream) and enclosure's view of link health | Circuits, lugs, enclosure-integrated MID |
| `energy.ebus.capability.door` | Door state sensor | Enclosure (when applicable) |
| `energy.ebus.capability.power-flows` | Site-level power aggregation | Enclosure |
| `energy.ebus.capability.pcs` | Power Control Systems (UL 3141) | Enclosure |
| `energy.ebus.capability.shed-forecast` | Off-grid backup time-remaining forecast (read-only) | Enclosure (when a BESS is commissioned) |
| `energy.ebus.capability.shed` | Enclosure-wide shed-policy controls (homeowner override, SOC threshold) | Enclosure (when a BESS is commissioned) |

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
  status/communication                                    OK

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
  status/communication                                    OK
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
  meter/l1-voltage                              121.3
  meter/l2-voltage                              121.1
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
  shed/override                                 false
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
  info/tab-number                               7
  info/dipole                                   true
  info/breaker-rating                           100
  meter/active-power                            0.0
  switch/relay                                  CLOSED
  priority/shed-priority                        NEVER
  priority/relay-controllable                   true
  connection/feeds-device-id                    "ab-1234-c5d67-TG123456789"
  connection/feeds-device-type                  "energy.ebus.device.bess"
  connection/feeds-device-status                OK

ebus/5/<circuit-5-id>/                          energy.ebus.device.circuit
  info/name                                     "EV Charger"
  info/tab-number                               5
  info/dipole                                   true
  info/breaker-rating                           60
  info/tags                                     "EVSE"
  meter/active-power                            5350.0
  switch/relay                                  CLOSED
  priority/shed-priority                        SOC_THRESHOLD
  priority/relay-controllable                   true
  connection/feeds-device-id                    "ab-1234-c5d67-SD123456789"
  connection/feeds-device-type                  "energy.ebus.device.evse"
  connection/feeds-device-status                OK

ebus/5/<circuit-1-id>/                          energy.ebus.device.circuit
  info/name                                     "Kitchen"
  info/tab-number                               1
  info/dipole                                   false
  info/breaker-rating                           20
  meter/active-power                            245.3
  switch/relay                                  CLOSED
  priority/shed-priority                        NEVER
  priority/relay-controllable                   true
  (no connection/feeds-* — mixed-load circuit, no specific commissioned downstream device)

  ... (more circuits, most without connection/feeds-* records)

ebus/5/ab-1234-c5d67-TG123456789/               energy.ebus.device.bess  (proxied)
  info/vendor-name                              "Tesla"
  info/serial-number                            "TG123456789"
  info/data-model-version                       "1.0"
  soc/soc                                       98.5
  soc/soe                                       80.1
  status/communication                          OK

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
  config/max-charge-current                     48
  config/user-max-charge-current                40
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
