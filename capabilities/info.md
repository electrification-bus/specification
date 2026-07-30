# Electrification Bus Capability: info

**Status:** DRAFT
**Version:** 0.2
**Date:** 2026-07-30
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.info` — device identity and descriptive metadata.

**Node type:** `energy.ebus.capability.info`

This document is the canonical catalog for the **shared identity core** of the `info` capability. Data-model documents reference this catalog for the identity properties and add their own device-specific `info` properties.

## Overview

`info` carries a device's identity and descriptive metadata. It is the one capability **present on every eBus device**. Its content divides into two parts:

- a **shared identity core** — the nameplate and rating properties defined here: identity strings common to any physical product, plus an optional rated `nameplate-capacity` for energy-storage devices;
- **device-specific properties** — defined by each device model (a circuit's load-facing `name` / `tags`, a utility meter's metrology nameplate, an outlet's port descriptors, a BESS's `nominal-power`, and so on).

This catalog defines the shared identity core. Each device model references it and documents its own additional `info` properties.

## Identity properties (shared core)

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `vendor-name` | string | - | SHOULD | Manufacturer name (e.g., "SPAN", "Tesla", "Rheem"). |
| `serial-number` | string | - | SHOULD | Device serial number. |
| `model` | string | - | SHOULD | Vendor-defined model identifier. The valid set is publisher-defined and MAY be advertised via Homie `$format` on the property. |
| `part-number` | string | - | MAY | Manufacturer part or SKU number. MAY differ from `model`: distinct part numbers can designate the same model (packaging, regional, or minor-revision variants). |
| `hardware-version` | string | - | MAY | Hardware revision. |
| `firmware-version` | string | - | SHOULD | Firmware version. Published when the device has firmware; a bare or surveyed device (e.g., a dumb load center) omits it. |
| `data-model-version` | string | - | SHOULD | Version of the eBus data model this device publishes (e.g., `"1.0"`). |
| `nameplate-capacity` | float | energy | MAY | Rated nameplate energy capacity, a term of art for energy-storage devices, reported in the device's native energy unit (a BESS in kWh electrical, a storage water heater in Wh thermal) via `$unit`. It is the static manufacturer rating: `soc` is roughly `soe` / `nameplate-capacity`, while the precise, dynamic denominator is `soc`'s `total-energy-storage` (which diverges from the nameplate figure as the reservoir degrades). Energy-storage device types (BESS, thermal storage) SHOULD publish it; power-rated devices (PV, inverter, EVSE) publish rated power via `nominal-power` instead. |

**No identity property is MUST.** A conformant device is identified by its `$description.type` discriminator and its Homie device ID, not by the population of any nameplate field. A proxied or surveyed device may know only some of these; publishers populate what they have and consumers tolerate absence. Publishers MAY add vendor-specific informational properties to `info` beyond those a device model defines.

## Nameplate versus conductor identity

Most device types are physical products whose `info` identity core *is* their nameplate. A **circuit** is different: it models a *conductor*, so its core `info` is load-facing (a user-assigned `name`, load-type `tags`), and a native panel branch carries no nameplate (the panel's nameplate lives on the enclosure).

When a circuit is **realized by a distinct physical instrument** — for example a proxied standalone sub-meter (an EKM or eGauge measuring one conductor) — that instrument has its own nameplate, and it has no other home. Such a circuit MAY carry the identity properties above **in addition to** its load-facing properties: `info/name` names the conductor ("Solar Feed"), while `info/vendor-name` / `serial-number` / `model` / `firmware-version` name the measuring instrument. Presence of the identity properties on a circuit signals that the circuit is realized by a distinct instrument; absence means it is a bare conductor. The two facets do not collide, because they are distinct property names. The instrument serial MAY additionally appear in the circuit's `info/external-ids` (e.g. `ekm:<serial>`) as a cross-system reference, complementary to the nameplate `serial-number`. See [`circuit.md`](../devices/circuit.md).

This resolves where instrument identity lives without promoting the host to a `utility-meter` (a customer-owned sub-meter is not a utility meter) and without a new device type: the shared identity core is simply available on the host that is realized by the instrument.

## Publishers

Every eBus device publishes `info`. The shared identity core is carried by physical-product device types (enclosure, utility-meter, BESS, water-heater, PDU, and others) and, for the instrument case above, by circuits realized by a standalone instrument.

## References

- [Electrification Bus framework specification](../framework.md)
- [circuit](../devices/circuit.md), [distribution-enclosure](../devices/distribution-enclosure.md), [utility-meter](../devices/utility-meter.md), [BESS](../devices/bess.md), and [water-heater](../devices/water-heater.md) data models — publishers that extend this capability.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
