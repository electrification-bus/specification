# Electrification Bus Capability: connection

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-05
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.connection` — local wiring topology: what is wired downstream of, and where known upstream of, this electrical connection point.

**Node type:** `energy.ebus.capability.connection`

This document is the canonical property catalog for the `connection` capability. Data-model documents that use it (for example [`circuit.md`](../data-models/circuit.md) and [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog and document only their device-specific usage.

## Overview

The `connection` capability records the wiring topology *local to one electrical connection point*: what is wired downstream (`feeds-*`) and, where the publisher knows it, upstream (`fed-by-*`), together with attributes of the connection (the backup boundary, the role of an un-modelled downstream node, service and protection ratings). It is published by any device that is itself an electrical connection point: circuits, lugs, and a microgrid interconnect device (MID).

**eBus records site topology as a distributed set of these per-device edges, not as a central tree.** Each connection-owner publishes the edges it knows; a consumer assembles the site graph by following the references across devices. There is deliberately no central topology device or authority: the model is vendor-neutral and does not assume a single controller owns the whole-site picture. §"Assembling the site topology" describes how the distributed edges compose into the equivalent of a topology tree.

## Properties

### Downstream and upstream device references

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `feeds-device-id` | string | MAY | Homie device ID of the device wired *downstream* of this connection point. Published only when the specific downstream device is known. Omitted when unknown, when mixed-load with no commissioned downstream device, or when nothing is connected. |
| `feeds-device-type` | string | MAY | `$description.type` of the downstream device (e.g. `energy.ebus.device.bess`, `.pv`, `.evse`, `.water-heater`, `.distribution-enclosure`, or a DER sub-device such as `.battery`). Published when the class is known even if the specific ID is not. |
| `feeds-device-status` | enum | MAY | Publisher's view of communication-link health to the downstream device: `OK`, `LOST`, `DEGRADED`. Published only when `feeds-device-id` is published and the publisher has a communication integration with that device. |
| `fed-by-device-id` | string | MAY | Homie device ID of the device wired *upstream* of this connection point. Published only when known (e.g. an upstream BESS wired between the utility and the enclosure, or an upstream sister enclosure in a chain). Omitted when the upstream side is the utility, an implicit busbar, or unknown. |
| `fed-by-device-type` | string | MAY | `$description.type` of the upstream device. Published with `fed-by-device-id`. |
| `fed-by-device-status` | enum | MAY | Publisher's view of communication-link health to the upstream device. Same value domain and applicability as `feeds-device-status`. |

### Topology attributes

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `backed-up` | enum | — | MAY | Whether this path is on the backup (island) side of a microgrid interconnect device, and so stays energized off-grid: `BACKED_UP`, `NOT_BACKED_UP`, `UNKNOWN`. A wiring fact (which side of the interconnect), distinct from `load-shed/priority` (a shedding *policy*) and `grid/islanding-state` (the present *state*). |
| `feeds-role` | enum | — | MAY | Summary role of a downstream node that is **not** published as its own eBus device, or that is surveyed-empty: `LOADS`, `SUBPANEL`, `SOLAR`, `STORAGE`, `GENERATOR`, `MIXED`, `UNUSED`. `UNUSED` positively records "surveyed, nothing connected" (which absence cannot express). Complements `feeds-device-*`, which is used when the downstream *is* an eBus device. |
| `service-rating` | integer | A | MAY | Utility service rating (service size) at a service-entrance connection point. Distinct from `pcs/feed-import-limit` (a PCS enforcement limit) and `breaker/rating` (a main breaker). |
| `overcurrent-protection` | integer | A | MAY | Overcurrent-protection rating at a connection point that is not itself a breaker-protected circuit (for example a feeder conductor landing in unprotected lugs). Where the connection point *is* a breaker-protected circuit, the rating is `breaker/rating` instead. |
| `count` | integer | — | MAY | When the connected node aggregates multiple physical units behind a *single* connection point (e.g. 6 battery packs in one BESS, or 4 microinverters on one AC string reported as one solar device), how many. |

## Semantics

**Absent means unknown.** A property is published only when the publisher has data for it; empty strings are not sentinels. An unpublished property is the "unknown" signal, in keeping with Homie convention. `feeds-role = UNUSED` is the way to positively record "surveyed, nothing connected," which absence cannot distinguish from "unknown" or "not yet commissioned."

**Both directions are MAY; populate the side(s) you know.** The model defines both the `feeds-*` and `fed-by-*` references so a publisher can record connection metadata in whichever direction it learns. A publisher populates the side(s) it knows; consumers must not assume both directions are populated, and the absence of a counterpart record is information, not error. The references divide into independently-published groups (the `feeds-*` triplet, the `fed-by-*` triplet, and the standalone attributes), each published as a unit.

**Connection-point class is implicit in the publisher's `$description.type`.** A consumer reads the class from the publishing device's type and needs no extra discriminator:

| Publishing device's `$description.type` | Connection-point class |
|---|---|
| `energy.ebus.device.circuit` | feeder-circuit (a load fed through a breaker) |
| `energy.ebus.device.lugs` (upstream) | main-lugs (service entrance) |
| `energy.ebus.device.lugs` (downstream) | feedthrough-lugs |
| `energy.ebus.device.mid` | microgrid-interconnect passthrough |

**The backup boundary.** `backed-up` records which side of a microgrid interconnect device a downstream path is on. In a whole-home-backup install every downstream path is `BACKED_UP`; in a partial-backup install the feeders that bypass the island are `NOT_BACKED_UP`. It is the wiring fact a backup coordinator needs to know which loads survive an outage, and it is independent of whether any load-shed policy would later shed a backed-up load.

**Un-modelled downstream nodes.** When the downstream of a connection is not published as its own eBus device — a dumb subpanel, an AC-coupled inverter, a generator, an uncommissioned load group, or nothing — `feeds-role` gives its coarse role. A downstream worth modelling in detail SHOULD instead be published as its own device (for example, a surveyed subpanel as a minimal [`distribution-enclosure`](../data-models/distribution-enclosure.md) with its child circuits); `feeds-role` is the lightweight fallback for nodes not modelled that way.

**One node behind many connection points; many units behind one.** More than one connection point MAY reference the same downstream device (for example a multi-unit BESS whose units land on separate circuits, each circuit's `feeds-device-id = {bess}`); a consumer sums the connection points that reference one device to obtain its total flow. This is distinct from `count`, which stands in for multiple physical units aggregated behind a *single* connection point.

## Assembling the site topology

Because the edges are distributed, a consumer assembles the site graph itself:

1. Collect every device's `connection` record.
2. Link each `feeds-device-id` to the referenced device (and the reverse via `fed-by-device-id`); reconcile overlapping measurements (e.g. an external CT and a native device on the same conductor) by co-location on the same connection point.
3. Read each edge's connection-point class from the publisher's `$description.type`.
4. Treat the service-entrance connection point (the upstream `lugs` carrying `service-rating`) as the root.

The result is the equivalent of a centralized topology tree, assembled from distributed edges without any device having to own the whole-site picture.

## Publishers

Published by any device that is an electrical connection point: circuits, both lugs devices (service-entrance and feedthrough), and the MID. A device model documents which of its connection-owners carry which attributes (for example, `service-rating` on the service-entrance lugs, `backed-up` on downstream feeders).

## References

- [Electrification Bus framework specification](../framework.md)
- [circuit](../data-models/circuit.md) and [distribution-enclosure](../data-models/distribution-enclosure.md) data models — publishers of this capability.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
