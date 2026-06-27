# Electrification Bus Power Distribution Unit Data Model Specification

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-06-26
**Authors:** Don Jackson

## Overview

This document defines an Electrification Bus (eBus for short) data model for a **Power Distribution Unit (PDU)**: a device whose function is to distribute power to a set of individually **switchable** and **metered** output ports (outlets) that loads plug into. The canonical example is a smart, metered PDU (a data-center rack PDU, or a smart power strip). Its outlets are modeled as `outlet` child devices, defined once in [`outlet.md`](outlet.md) and reused by plug-in batteries and UPSs as well.

A PDU has no energy storage and is not a generation source. It takes power from a single input and delivers it to its outlets, reporting per-outlet power and energy and accepting per-outlet on/off control. Devices that *add* storage to this same outlet structure (a plug-in battery, a UPS) are modeled as a `bess` that hosts the same `outlet` children; see [`bess.md`](bess.md).

## Terminology

| Term | Definition |
|---|---|
| PDU | Power Distribution Unit: a device that distributes power to switchable, metered output ports. |
| Outlet | One output port: a receptacle (AC) or port (USB-C, etc.) that a load plugs into. Modeled as a child device. |

This is distinct from a **distribution enclosure** ([`distribution-enclosure.md`](distribution-enclosure.md)): an enclosure is the service-entrance panel whose `circuit` children are branch circuits of the premises wiring. A PDU is a plug-in appliance whose `outlet` children are receptacles on the device itself; loads plug directly into it. The two are structurally similar (a parent over switchable, metered child connection points) but electrically and physically different. The `outlet` child is the appliance-receptacle analogue of the enclosure's `circuit` child.

## Audience and Scope

- **Publishers**: PDU OEMs, or proxies bridging a non-eBus PDU (a vendor cloud API, a SNMP/Modbus rack PDU, an MQTT smart strip).
- **Consumers**: controllers and dashboards that read per-outlet power/energy and switch outlets on or off.

The model covers the PDU device, its identity, an optional aggregate meter, and its `outlet` child devices (each switchable and metered). It does **not** cover storage (`soc`, `dispatch`) or generation, which belong to other device classes.

## Design Principles

This data model follows the Electrification Bus design principles (see [framework.md](../framework.md#design-principles)): Homie devices represent physical things (each outlet is a distinct, controllable, metered port), parent aggregation, capability reuse across device classes, proxying as a first-class peer to native publishing, and forward compatibility.

**Capability reuse.** The PDU coins no new capability. An outlet is an `info` plus the existing `switch` (on/off relay) plus the existing `meter` (power and energy) capabilities, exactly as a distribution-enclosure circuit is. The only new vocabulary this document introduces is the two device types (`pdu`, `outlet`) and a small set of outlet `info` properties describing the port.

**Conformance latitude.** Most properties are MAY-level; publishers populate what they have. A PDU that publishes only per-outlet switch state is conformant; so is one that adds full per-outlet metering and an aggregate input meter.

---

## PDU Device

**Type:** `energy.ebus.device.pdu`

The PDU parent represents the unit as a whole. Its outlets are child devices.

```
ebus/5/<pdu-id>/                 energy.ebus.device.pdu
  info                  Identity and nameplate
  meter                 Aggregate input power / energy           (when published)
  status                Device operational state                 (when published)
  ├── <pdu-id>-outlet-1   energy.ebus.device.outlet
  ├── <pdu-id>-outlet-2   energy.ebus.device.outlet
  └── ...
```

### PDU Capabilities

| Capability | Req | Notes |
|---|---|---|
| `info` | MUST | Vendor, serial, model, firmware, `data-model-version`, outlet count. |
| `meter` | MAY | Whole-unit (inlet) power and energy. See *Metering tiers* below. |
| `status` | MAY | Device-level fault / communication status. |

**Metering tiers.** PDUs vary in metering granularity, and the model supports the full range by making both the parent `meter` and each outlet's `meter` optional:

- **Switched only** (no metering): outlets publish `switch` but no `meter`, and the PDU parent omits `meter`.
- **Whole-unit metered**: the PDU parent publishes `meter` (the unit's inlet power and energy) and the individual outlets omit `meter`. This is the common "metered PDU" tier, where the hardware meters only the whole unit, not each outlet.
- **Per-outlet metered**: each `outlet` child publishes `meter`; the PDU parent MAY additionally publish the whole-unit aggregate.

An eBus consumer reads whichever `meter` nodes are present. Absence of per-outlet meters means only whole-unit (or no) metering is available; it does not imply the outlets carry no load.

#### info

**Node type:** `energy.ebus.capability.info`

Reuses the standard identity properties (`vendor-name`, `serial-number`, `model`, `firmware-version`, `data-model-version`). A PDU MAY add `outlet-count` (integer) for convenience; consumers can also count the `outlet` children.

#### meter

**Node type:** `energy.ebus.capability.meter`. Whole-unit (inlet) metering, using the standard `meter` properties (`active-power`, `imported-energy`, etc.). Present on whole-unit-metered PDUs; on per-outlet-metered PDUs it is the optional aggregate over the per-outlet meters.

---

## Outlet children

A PDU's outlets are `energy.ebus.device.outlet` child devices, defined in [`outlet.md`](outlet.md): each is an `info` (identity, port type, ratings, assigned name) plus `switch` (on/off relay) plus, where the hardware supports it, `meter` (per-outlet power and delivered energy). A PDU declares its outlet children in its `$description` `children` list, named `{pdu-id}-outlet-{n}`. See [`outlet.md`](outlet.md) for the full outlet contract.

---

## Example: smart power strip

A four-outlet metered smart strip, with the second outlet off and a USB-C port:

```
ebus/5/strip-9f2a/$description.type            = energy.ebus.device.pdu
ebus/5/strip-9f2a/info/vendor-name             = "ExampleCorp"
ebus/5/strip-9f2a/info/serial-number           = "PS-9F2A"
ebus/5/strip-9f2a/info/outlet-count            = 5
ebus/5/strip-9f2a/meter/active-power           = 320.0

ebus/5/strip-9f2a-outlet-1/$description.type   = energy.ebus.device.outlet
ebus/5/strip-9f2a-outlet-1/info/name           = "Fridge"
ebus/5/strip-9f2a-outlet-1/info/port-type      = "AC_OUTLET"
ebus/5/strip-9f2a-outlet-1/info/nominal-voltage = 120
ebus/5/strip-9f2a-outlet-1/info/nameplate-power = 1800
ebus/5/strip-9f2a-outlet-1/switch/state        = "ON"
ebus/5/strip-9f2a-outlet-1/meter/active-power  = 142.0
ebus/5/strip-9f2a-outlet-1/meter/exported-energy = 84210.0

ebus/5/strip-9f2a-outlet-2/$description.type   = energy.ebus.device.outlet
ebus/5/strip-9f2a-outlet-2/info/name           = "Lamp"
ebus/5/strip-9f2a-outlet-2/switch/state        = "OFF"
ebus/5/strip-9f2a-outlet-2/meter/active-power  = 0.0

ebus/5/strip-9f2a-usb-1/$description.type      = energy.ebus.device.outlet
ebus/5/strip-9f2a-usb-1/info/name              = "Right USB Port"
ebus/5/strip-9f2a-usb-1/info/port-type         = "USB_C"
ebus/5/strip-9f2a-usb-1/info/nameplate-power   = 100
ebus/5/strip-9f2a-usb-1/switch/state           = "ON"
ebus/5/strip-9f2a-usb-1/meter/active-power     = 18.0
```

To switch an outlet:

```
ebus/5/strip-9f2a-outlet-2/switch/state/set = "ON"
```

---

## Registry impact

- `energy.ebus.device.pdu` — **new** device type. Parent for a power distribution unit; hosts `outlet` children.
- `energy.ebus.device.outlet` — defined in [`outlet.md`](outlet.md); composed here as the PDU's children (this document does not re-register it).
- `energy.ebus.capability.info`, `energy.ebus.capability.meter`, `energy.ebus.capability.status` — reused unchanged on the PDU parent.

---

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus BESS data model](bess.md) — plug-in batteries and UPSs reuse the `outlet` child type defined here.
- [Electrification Bus distribution-enclosure data model](distribution-enclosure.md) — the `circuit` child precedent that the `outlet` child mirrors (switch + meter on a parent's connection points).
- [Electrification Bus proxy model](proxy.md)
- [Electrification Bus capability-type registry](../registries/capability-types.md) and [device-type registry](../registries/device-types.md).
