# Electrification Bus Circuit Data Model Specification

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-04
**Authors:** Don Jackson

## Overview

This document defines an Electrification Bus (eBus for short) data model for a **circuit**: the general device type for a single conductor path (a branch, feeder, or source circuit). A circuit is the foundational building block of the eBus site model. Metering, protection, and remote control are **optional** capabilities a circuit may carry; none is part of what makes something a circuit. The same device type describes a branch circuit inside a distribution enclosure, a standalone smart circuit breaker, a submeter's measured conductor, a bare monitored feed, and a spare breaker. It is layered on Homie 5 plus eBus's HEI-specific device and capability types and is intended to be vendor-neutral.

A circuit is deliberately minimal at its core and composed of **optional capabilities**. What a particular circuit *is* is described by which capabilities it publishes: a smart-panel branch publishes metering, a controllable relay, breaker protection, and a load-shed policy; a bare monitoring point publishes only metering; a spare breaker publishes almost nothing. The device type is the discriminator; capability population is the description.

## Terminology: "circuit"

This document uses **circuit** in the electrical-engineering sense, not the narrower colloquial "a breaker in a panel." In NEC and industry usage a circuit is any conductor path for current: a **branch circuit**, a **feeder**, a **PV source circuit**, a **PV output circuit**, a **battery circuit**, a motor circuit, and so on. All of these are circuits and are modelled by this device type.

Two related concepts are distinct:

- The **service entrance** (where the utility supply enters, or where a feed enters an enclosure) is modelled by the `energy.ebus.device.lugs` specialization (a circuit plus a `direction`), not as a plain circuit. See §"Specializations".
- A whole **metering instrument** (for example a revenue submeter that measures one service) is a device in its own right (`energy.ebus.device.utility-meter`, or a submeter device), not a circuit. A circuit is a conductor; a meter is an instrument that may measure one.

## Audience and Scope

- **Publishers**: any device or proxy that represents a conductor path. Native publishers (a smart panel publishing its branches, a smart breaker publishing itself) and proxies (an adapter republishing an Eaton/Siemens smart breaker, an eGauge/EKM meter-point, a dumb load center surveyed at commissioning).
- **Consumers**: controllers that read circuit state for energy management, load shedding, metering, and site topology.

The model covers the circuit device, its identity, and the optional capabilities it may carry. It does **not** define the container-specific *interaction* semantics (for example how a circuit's load-shed participation couples to a distribution enclosure's enclosure-wide shed policy and forecast); those live in the model of the hosting device (see [`distribution-enclosure.md`](distribution-enclosure.md)).

## Design Principles

This data model follows the Electrification Bus design principles. Three stances shape the tables below:

**Wide conformance latitude.** The **irreducible core of a conformant circuit is its type (`energy.ebus.device.circuit`) plus `info` (identity)**. Every other capability is optional. A circuit that publishes only `info` is a valid circuit (a named conductor of unknown topology and unmeasured flow, for example a spare breaker). Publishers populate what they have; consumers tolerate sparse publication. This stance matches [`utility-meter.md`](utility-meter.md). Metering and switchgear are not intrinsic to a circuit: they reflect one class of product (a smart panel) and are modelled as optional capabilities, never as requirements.

**Capability presence is a signal.** Because capabilities are optional, their *presence* carries information: a circuit that publishes `switch` is remotely controllable; one that publishes `breaker` is breaker-protected; one that publishes `meter` is instrumented. Absence of a capability means the circuit lacks that function (or the publisher does not expose it), which a consumer reads directly.

**Container-neutral.** A circuit is a Homie child device of some parent, but the parent may be any device: a distribution enclosure (branch circuits), a proxy (a proxied smart breaker or an eGauge/EKM meter-point), or a sub-enclosure. A circuit does not require a distribution-enclosure parent. Attributes that only make sense within a particular container (for example a physical panel position) are defined by the hosting device's model, not by the general circuit.

---

## Circuit Device

**Type:** `energy.ebus.device.circuit`

A circuit represents one conductor path. It has no eBus-modelled child devices; per-phase electrical measurements are recorded as property-name suffixes on its capability nodes (see *Per-phase representation*).

```
ebus/5/<circuit-id>/                   energy.ebus.device.circuit
  info                          Circuit identity                                  (always)
  connection                    Topological position (what it feeds / is fed by)  (SHOULD)
  meter                         Electrical measurements                           (when instrumented)
  switch                        Remotely-controllable relay                       (when switchable)
  breaker                       Overcurrent / fault protection                    (when breaker-protected)
  load-shed                     Load-shed participation                           (when the host sheds load)
  pcs                           PCS participation                                 (when the host runs a PCS)
```

Only `info` and the device type are always present. `connection` SHOULD be published when topology is known (its absence means "topology unknown", per the framework absence rule). `meter`, `switch`, `breaker`, `load-shed`, and `pcs` are each published when the circuit has the corresponding function.

### Device ID

The device ID is publisher-defined and opaque to consumers (a UUID, the breaker serial, or a proxier-scoped `{proxier-id}-{proxied-id}` identifier for a proxied circuit). The data model places no constraint on its form.

### Per-phase representation

Per-phase measurements use property-name suffixes (`-a` / `-b` / `-c`, and `-n` for the neutral) on the `meter` node, matching the convention in [`utility-meter.md`](utility-meter.md) and [`distribution-enclosure.md`](distribution-enclosure.md). A split-phase 240 V circuit populates `-a` and `-b`; a single-phase circuit populates only `-a`. System aggregates carry no suffix.

### info

Circuit identity. **Always published.**

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `name` | string | — | SHOULD | yes | User-assigned circuit name (e.g., "Kitchen", "Water Heater"). Free-text. |
| `tags` | string | — | MAY | no | Controlled vocabulary of load-type tags (e.g., `WATER_HEATER`, `EVSE`, `RANGE`). Multi-valued, comma-separated. See [`registries/circuit-tags.md`](../registries/circuit-tags.md). |
| `external-ids` | string | — | MAY | no | Multi-valued list of `<scheme>:<identifier>` references from external systems. See [`registries/external-id-schemes.md`](../registries/external-id-schemes.md). |
| `dedicated` | boolean | — | MAY | no | True when commissioned as serving a single load; false when explicitly mixed-load; omitted when undetermined. Absence is *not* equivalent to false. |

Physical position within a panel (which space(s) the breaker occupies) is an attribute of the *hosting enclosure*, not of the general circuit, and is defined by the enclosure's model (see [`distribution-enclosure.md`](distribution-enclosure.md)'s `info/spaces`). A two-pole breaker occupies two spaces, a tandem puts two circuits in one space, so a circuit's electrical pole count (`breaker/poles`) and its physical footprint are modelled separately.

### connection

The circuit's topological position: what is wired downstream of it (`feeds-*`) and what is wired upstream (`fed-by-*`). **SHOULD be published** when known; absence means topology is unknown, not "nothing connected". This is the same capability published by every device that is an electrical connection point (circuits, lugs, the enclosure-integrated MID). It is how a consumer reconciles overlapping measurements (for example an eGauge CT and a native device measuring the same conductor) by co-location.

**Node type:** `energy.ebus.capability.connection`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `feeds-device-id` | string | MAY | Homie device ID of the device wired *downstream* of this circuit. Published only when the specific downstream device is known. Omitted when unknown, mixed-load with no commissioned downstream device, or nothing connected. |
| `feeds-device-type` | string | MAY | `$description.type` of the downstream device (e.g., `energy.ebus.device.bess`, `.pv`, `.evse`, `.water-heater`, or a DER sub-device such as `.battery`). Published when the class is known even if the specific ID is not. |
| `feeds-device-status` | enum | MAY | Publisher's view of communication-link health to the fed device: `OK`, `LOST`, `DEGRADED`. Published only when `feeds-device-id` is published AND the publisher has a communication integration with that device. |
| `fed-by-device-id` | string | MAY | Homie device ID of the device wired *upstream* of this circuit. Published only when known (e.g., an UPSTREAM BESS, or an upstream sister enclosure). Omitted when the upstream side is the utility, an implicit busbar, or unknown. |
| `fed-by-device-type` | string | MAY | `$description.type` of the upstream device. Published with `fed-by-device-id`. |
| `fed-by-device-status` | enum | MAY | Publisher's view of communication-link health to the upstream device. Same value domain and applicability as `feeds-device-status`. |
| `count` | integer | MAY | When the connected node aggregates multiple physical units (e.g., 6 battery packs in one BESS behind one connection point), how many. |

**Absent properties mean "unknown."** A property is published only when the publisher has data for it; empty strings are not sentinels. The properties divide into three independently-published groups: the `feeds-*` triplet, the `fed-by-*` triplet, and `count`.

**Both directions are MAY-level; populate the side(s) you know.** Consumers must not assume both directions are populated; the absence of a counterpart record is information, not error.

**Connection-point class is implicit in the publisher's `$description.type`** — a consumer reads whether it is a `circuit`, `lugs`, or MID and needs no extra discriminator field.

> A single DER may connect via multiple circuits: more than one circuit MAY reference the same downstream device (each `feeds-device-id = {device}`, or a specific unit child). A consumer sums the circuits referencing one device to obtain its total flow. This is distinct from `count` (multiple units behind a *single* connection point).
>
> Conversely, one circuit MAY feed several sibling circuits: a *multi-load breaker* (tandem or quad) is a feed circuit whose shared meter and relay sit above per-load circuits that each carry only their own `breaker`. See §"Multi-load breakers (tandem and quad)".

### meter

Electrical measurements at the circuit. Published when the circuit is instrumented; omitted otherwise. The full property catalog and the `-a` / `-b` / `-c` / `-n` per-conductor convention are defined in [`capabilities/meter.md`](../capabilities/meter.md). On a circuit, `active-power` SHOULD be published and uses the default reference direction (positive = flowing to the load, i.e. imported).

The full per-phase / reactive / apparent / 4-quadrant matrix (as exposed by, for example, the Eaton SBLCP telemetry) is added additively as consumers require it.

### switch

The circuit's remotely-controllable relay. Published when the circuit has a controllable relay; omitted otherwise. This is the **control** surface, distinct from `breaker` (protection): a relay opens on command or load-shed, a breaker trips on fault. The full property catalog (`relay`, `relay-controllable`, `relay-requester`, and the fail-safe-timeout note) is defined in [`capabilities/switch.md`](../capabilities/switch.md).

### breaker

Overcurrent / fault **protection**. Published when the circuit is protected by a breaker; omitted otherwise (a bare monitored conductor or feedthrough has no `breaker`). Distinct from `switch`: protection is not remote control. In Eaton's SBLCP protocol these are literally two handles (a primary/protective handle and a remote/control handle), which validates the split at the hardware level. The full property catalog (`rating`, `poles`, `interrupting-rating`, `protection-functions`, `trip-curve`, `trip-state`, `trip-cause`, and the optional further properties) is defined in [`capabilities/breaker.md`](../capabilities/breaker.md).

### load-shed

The circuit's participation in load-shedding. Published when the hosting device coordinates shedding (typically a distribution enclosure); omitted otherwise.

**Node type:** `energy.ebus.capability.load-shed`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `priority` | enum | — | SHOULD | Shedding class. Baseline: `UNKNOWN`, `NEVER`, `OFF_GRID`. Optional (advertised in `$format`): `SOC_THRESHOLD` and future values. |

The **interaction** of `load-shed/priority` with a host's enclosure-wide shed policy (the SOC threshold, the shed forecast, the effective shed gate) is host-specific and is defined in the host's model, e.g. [`distribution-enclosure.md`](distribution-enclosure.md).

### pcs

The circuit's participation in the host's Power Control System (PCS, per UL 3141). Published when the host runs a PCS and this circuit is part of it; omitted otherwise. This is a **separate** concern from `load-shed`: a PCS controls circuits to keep site import/export within a binding limit, not to preserve backup runtime; a circuit may participate in one, both, or neither.

**Node type:** `energy.ebus.capability.pcs`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `managed` | boolean | — | MAY | Is this circuit managed by the host's PCS? |
| `priority` | integer | — | MAY | PCS priority ranking, consulted when an active CSL (Configurable Service Limit) is binding. |

Both `load-shed` and `pcs` are policies that act on the circuit's relay, so they are meaningful only on a circuit that also publishes a controllable `switch`. They correspond to the `LOAD_SHED` and `PCS` values of `switch/relay-requester`.

---

## Specializations

- **`energy.ebus.device.lugs`** = a circuit plus a `direction` (`UPSTREAM` / `DOWNSTREAM`), used for service-entrance and feedthrough connection points. Defined in [`distribution-enclosure.md`](distribution-enclosure.md).

A specialization is a circuit that always carries a specific additional property or capability.

---

## Multi-load breakers (tandem and quad)

Most circuits are a single conductor that is metered, switched, and protected as one unit, so all of a circuit's capabilities sit on one device (the ordinary case in the examples below). Some breaker packages instead put **several independently-protected loads behind one shared metering and switching point**: a *tandem* (two single-pole loads in one panel position, sharing that position's one relay and one meter) or a *quad* (two or three loads across a two-position footprint). The shared relay and shared meter mean those loads **cannot be metered or switched independently; they can only be protected independently.**

This is modelled with the capabilities already defined, split across circuits linked by `connection`:

- A **feed circuit** represents the shared metering and switching point. It publishes `meter` (the aggregate over every load it feeds) and, when controllable, `switch` (the shared relay). It publishes **no `breaker`**: it is the shared conductor, not a breaker. Any `load-shed` / `pcs` participation lives here too, because those policies act on its `switch`.
- One **load circuit per load** publishes `info` (name, tags) and its own `breaker` (rating, poles, and an independent `trip-state` / `trip-cause`), with `connection/fed-by` referencing the feed circuit. It publishes **no `meter` and no `switch`**: it is not independently metered or controllable.

The consequences follow directly from capability presence:

- **No double counting.** Only the feed circuit publishes `meter`; the loads behind it do not. A consumer summing circuit power adds feed circuits and ordinary standalone circuits, never the loads behind a feed.
- **Ganged control is explicit in the topology.** Each load is `fed-by` the feed circuit and the `switch` lives on the feed circuit, so opening it de-energizes every load it feeds. Independent control of same-feed loads cannot be expressed, which is correct: it does not exist.
- **Independent protection is preserved.** Each load circuit carries its own `breaker`, so one tandem half can read `trip-state = TRIPPED` while its sibling reads `OK`.
- **`connection` links circuit to circuit.** Here the `fed-by` (and optional `feeds`) references point at sibling circuits, not at a downstream DER or an enclosure. The linkage is normally published from the load side (`fed-by` on each load); a feed circuit MAY additionally enumerate its loads via a multi-valued `feeds-device-id`.

A standard single-pole or two-pole breaker is **not** split this way: it is one load behind one metering and switching point, so the feed and the load collapse into a single circuit that carries `meter`, `switch`, and `breaker` together. The split appears only when one metering and switching point serves more than one protected load.

---

## Examples

Valid circuits look very different depending on which capabilities they publish.

### Smart-panel branch circuit (all capabilities)

```
ebus/5/<enc>-c17/$description.type   = energy.ebus.device.circuit
.../info/name                         = "Water Heater"
.../info/tags                         = "WATER_HEATER"
.../connection/feeds-device-type      = energy.ebus.device.water-heater
.../meter/active-power                = 3120.0
.../meter/imported-energy             = 812345.0
.../switch/relay                      = CLOSED
.../switch/relay-controllable         = true
.../breaker/rating                    = 30
.../breaker/poles                     = 2
.../breaker/trip-state                = OK
.../load-shed/priority                = OFF_GRID
```

### Dumb load-center breaker (protection only, surveyed at commissioning)

```
ebus/5/<enc>-c04/$description.type   = energy.ebus.device.circuit
.../info/name                         = "Bedrooms"
.../breaker/rating                    = 15
.../breaker/poles                     = 1
```

`meter`, `switch`, `load-shed`, and `pcs` are omitted entirely: not metered, not controllable, no shed or PCS policy.

### eGauge-measured conductor (metering only, proxied)

```
ebus/5/<egauge>-pv/$description.type = energy.ebus.device.circuit
.../info/name                         = "PV"
.../connection/feeds-device-type      = energy.ebus.device.pv
.../meter/active-power                = -4210.0
```

No `breaker` / `switch`: the eGauge only measures a conductor.

### Standalone smart breaker, proxied (protection + control + metering, no enclosure parent)

```
ebus/5/<proxier>-<serial>/$description.type = energy.ebus.device.circuit
.../info/name                         = "ADU Range"
.../meter/active-power                = 1840.0
.../switch/relay                      = CLOSED
.../switch/relay-controllable         = true
.../breaker/rating                    = 20
.../breaker/protection-functions      = "GROUND_FAULT,ARC_FAULT"
.../breaker/trip-state                = OK
```

### Spare breaker (identity only)

```
ebus/5/<enc>-c22/$description.type   = energy.ebus.device.circuit
.../info/name                         = "Spare"
```

### Tandem breaker (shared metering and control, independent protection)

A tandem puts two 120 V loads in one position: one meter, one relay, two breakers. A feed circuit carries the shared meter and relay; each load is a downstream circuit with its own breaker. Load B is shown tripped while load A is not.

```
# Feed circuit: aggregate meter + shared relay, no breaker
ebus/5/<enc>-c31/$description.type   = energy.ebus.device.circuit
.../meter/active-power                = 1450.0
.../switch/relay                      = CLOSED
.../switch/relay-controllable         = true

# Load circuit A: own breaker, no meter or switch
ebus/5/<enc>-c31a/$description.type  = energy.ebus.device.circuit
.../info/name                         = "Dishwasher"
.../breaker/rating                    = 20
.../breaker/poles                     = 1
.../breaker/trip-state                = OK
.../connection/fed-by-device-id       = <enc>-c31

# Load circuit B: own breaker, tripped independently
ebus/5/<enc>-c31b/$description.type  = energy.ebus.device.circuit
.../info/name                         = "Disposal"
.../breaker/rating                    = 15
.../breaker/poles                     = 1
.../breaker/trip-state                = TRIPPED
.../connection/fed-by-device-id       = <enc>-c31
```

---

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus distribution-enclosure data model](distribution-enclosure.md) — hosts circuits as child devices; defines the `lugs` specialization, the `connection` catalog, and the enclosure-specific load-shed interaction.
- [Electrification Bus utility-meter data model](utility-meter.md) — precedent for wide conformance latitude and per-phase suffixes.
- [Electrification Bus capability-type registry](../registries/capability-types.md)
- [Electrification Bus `breaker`](../capabilities/breaker.md) and [`switch`](../capabilities/switch.md) capabilities: the canonical property catalogs for the protection and control surfaces referenced above.
