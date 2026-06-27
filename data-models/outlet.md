# Electrification Bus Outlet Data Model Specification

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-06-26
**Authors:** Don Jackson

## Overview

This document defines an Electrification Bus (eBus for short) data model for an **outlet**: one switchable, metered output port that a load plugs into. An outlet is most often a **reusable child device**, a building block composed by host parents that serve loads through their own receptacles: a Power Distribution Unit ([`pdu.md`](pdu.md)), a plug-in battery or UPS ([`bess.md`](bess.md)), and future portable power products. Defining the outlet once, here, lets every such host reuse an identical child contract. An outlet MAY also be published **standalone**, as its own Homie root, for a single-outlet product such as a smart plug or a smart in-wall receptacle. The capability contract is identical whether the outlet is hosted or standalone; only the device-ID convention differs.

An outlet coins no new capability. It is an `info` (identity plus a small port descriptor) plus the existing `switch` (on/off relay) plus the existing `meter` (power and delivered energy) capabilities. This mirrors the distribution-enclosure `circuit` child, which is likewise a switchable, metered connection point on a parent. The difference is electrical and physical, not structural: a `circuit` is a branch circuit of the premises wiring; an `outlet` is a receptacle on an appliance, into which a load plugs directly.

## Terminology

| Term | Definition |
|---|---|
| Outlet | One output port: a receptacle (AC) or port (USB-C, DC, etc.) on a host device that a load plugs into. Modeled as a child device. |
| Host | The parent device that owns the outlet (a PDU, a plug-in BESS, a UPS, ...). |

## Scope

The model covers one output port: its identity and ratings, its on/off control, and its per-outlet metering. It does not define the host device; see the host's data model (`pdu.md`, `bess.md`) for how outlets are aggregated and what else the host exposes.

## Design Principles

This follows the Electrification Bus design principles (see [framework.md](../framework.md#design-principles)): a Homie device represents a physical thing (each outlet is a distinct, independently controllable, metered port), capability reuse across device classes, proxying as a first-class peer to native publishing, and forward compatibility. Most properties are MAY-level; an outlet that publishes only its `switch` state is conformant.

---

## Outlet Device

**Type:** `energy.ebus.device.outlet`

```
ebus/5/<host-id>-outlet-<n>/     energy.ebus.device.outlet
  info                  Identity, port type, ratings, assigned name
  switch                On/off control and relay state            (when switchable)
  meter                 Per-outlet power and delivered energy      (when metered)
```

### Device ID

When the outlet is a child of a host, a native publication names it `{host-id}-outlet-{n}`, where `{host-id}` is the hosting parent's device ID and `{n}` is a stable per-outlet index; the host declares its outlet children in its `$description` `children` list. When the outlet is **standalone** (its own Homie root, e.g. a smart plug), its device ID is its own serial number, with no host prefix. When proxied, the proxier prefixes its own ID per [`proxy.md`](proxy.md).

### Capabilities

| Capability | Req | Notes |
|---|---|---|
| `info` | MUST | Outlet identity, port type, ratings, assigned name. |
| `switch` | SHOULD | On/off control and relay state. Omitted only for an always-on (unswitched) outlet. |
| `meter` | MAY | Per-outlet power and delivered energy. |

#### info

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `name` | string | — | MAY | User-assigned name for the outlet or the appliance plugged into it (e.g., `"Fridge"`). |
| `port-type` | enum | — | MAY | Receptacle / port type: `AC_OUTLET`, `USB_C`, `USB_A`, `DC`, `OTHER`. |
| `nominal-voltage` | float | V | MAY | Nominal output voltage (e.g., `120`, `240`, `5`, `20`). |
| `nameplate-power` | float | W | MAY | Maximum rated power for this outlet (e.g., `1800` for a 120 V / 15 A receptacle, `100` for a 100 W USB-C port). |
| `nameplate-current` | float | A | MAY | Maximum rated current, where the host rates outlets by current. |

#### switch

**Node type:** `energy.ebus.capability.switch`. Reused unchanged: the outlet's relay `state` (on/off) and its settable `/set` topic, exactly as for a distribution-enclosure circuit relay.

#### meter

**Node type:** `energy.ebus.capability.meter`. Reused. For an outlet, `active-power` is the power currently delivered to the connected load (positive = delivering out of the device, per the eBus convention that positive `active-power` flows out of the device). Cumulative delivered energy is carried in `exported-energy` (energy delivered out through the outlet). An outlet that does not meter individually omits `meter`.

---

## Example

Two outlets on a host (a power strip, a plug-in battery, etc.); the second is off:

```
ebus/5/<host>-outlet-1/$description.type    = energy.ebus.device.outlet
ebus/5/<host>-outlet-1/info/name            = "Fridge"
ebus/5/<host>-outlet-1/info/port-type       = "AC_OUTLET"
ebus/5/<host>-outlet-1/info/nominal-voltage = 120
ebus/5/<host>-outlet-1/info/nameplate-power = 1800
ebus/5/<host>-outlet-1/switch/state         = "ON"
ebus/5/<host>-outlet-1/meter/active-power   = 142.0
ebus/5/<host>-outlet-1/meter/exported-energy = 84210.0

ebus/5/<host>-outlet-2/$description.type    = energy.ebus.device.outlet
ebus/5/<host>-outlet-2/info/name            = "Lamp"
ebus/5/<host>-outlet-2/switch/state         = "OFF"
ebus/5/<host>-outlet-2/meter/active-power   = 0.0
```

To switch an outlet:

```
ebus/5/<host>-outlet-2/switch/state/set = "ON"
```

---

## Hosts and standalone use

The `outlet` device is used in two ways, with an identical capability contract:

- **As a child** of a host that serves loads through its receptacles: a **PDU** ([`pdu.md`](pdu.md), a storage-less unit whose only children are outlets), a **plug-in BESS or UPS** ([`bess.md`](bess.md), a battery that serves loads through its own outlets and, on a grid outage, backs them up via the `output-island` capability), or a future portable power product.
- **Standalone**, as its own Homie root: a single smart outlet product (a smart plug or a smart in-wall receptacle) that switches and meters one port.

An eBus consumer handles an `outlet` identically whether it is a child or standalone.

---

## Registry impact

- `energy.ebus.device.outlet` — **new** child device type. One switchable, metered output port.
- `energy.ebus.capability.info`, `energy.ebus.capability.switch`, `energy.ebus.capability.meter` — reused unchanged. The outlet `info` adds port-descriptor properties (`port-type`, `nominal-voltage`, `nameplate-power`, `nameplate-current`, `name`); these are properties within the existing `info` capability, not a new capability.

---

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus PDU data model](pdu.md) and [BESS data model](bess.md) — the host parents that compose this outlet child.
- [Electrification Bus distribution-enclosure data model](distribution-enclosure.md) — the `circuit` child precedent this outlet mirrors.
- [Electrification Bus proxy model](proxy.md)
- [Electrification Bus capability-type registry](../registries/capability-types.md) and [device-type registry](../registries/device-types.md).
