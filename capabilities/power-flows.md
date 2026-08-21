# Electrification Bus Capability: power-flows

**Status:** DRAFT
**Version:** 0.3
**Date:** 2026-08-20
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.power-flows` — site-level aggregate power flows across all energy sources, computed by the device that coordinates the site.

**Node type:** `energy.ebus.capability.power-flows`

This document is the canonical property catalog for the `power-flows` capability. Data-model documents that use it (today [`distribution-enclosure.md`](../devices/distribution-enclosure.md)) reference this catalog.

## Overview

`power-flows` is the **site-level aggregate** view: a single, coherent snapshot of how power is flowing across the whole site's sources and loads, computed by the site coordinator (a distribution enclosure) from its children and connected DER devices. It is distinct from a single point's [`meter`](meter.md): where `meter` reports one connection's measurement, `power-flows` is the computed roll-up across grid, storage, generation, and load.

## Properties

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `grid` | float | W | SHOULD | Grid power flow (positive = exporting to the grid). |
| `battery` | float | W | SHOULD | Battery power flow (positive = charging). |
| `pv` | float | W | SHOULD | Solar PV power flow (negative while producing). |
| `site` | float | W | SHOULD | Total site power consumption (positive = consuming). |

## Sign convention (reference direction)

The reference direction is **positive = out of the site node**: a flow is positive when power leaves the coordinator toward the named entity, and negative when it arrives from that entity. Exporting to the grid, charging a battery and consuming at the loads are therefore positive; importing from the grid, discharging a battery and PV production are negative.

This is one frame applied uniformly to all four properties, not four separately-reasoned conventions. It is chosen so that the roll-up is a closed node balance rather than a collection of independently-signed readings.

> **This reverses the sign that version 0.1 stated for `grid`, `battery` and `pv`.** 0.1 described each of those three in the terms natural to the thing it described (positive = importing, discharging, producing respectively), which is the opposite of the direction above; `site` is unchanged. An implementation written against 0.1 must invert those three. The reversal aligns the catalog with the reference implementer, which already publishes the frame described here.

### Balance

The four flows describe one node, so they sum to zero:

```
grid + battery + pv + site = 0
```

`site` is the **total** site load, including load the coordinator does not meter on its own branches (for example a sub-feed or a load upstream of the service disconnect). That totality is what makes the balance close; a `site` restricted to metered branches would not.

A publisher that omits a flow because the site has no such source is publishing a node in which that flow is identically zero, and the balance still closes over the properties it does publish. A publisher that omits a flow it simply cannot measure leaves the balance unverifiable, and a consumer MUST NOT recover the missing flow as the negated sum of the others, since it cannot distinguish the two cases. See [Absence semantics](#absence-semantics).

### Relationship to `meter`

`power-flows` is a computed roll-up for the site as a whole, not a measurement taken at a metered point, so the [`meter`](meter.md) capability's reference-direction rule does not govern it and the frame above applies instead.

The two are deliberately opposite, and a consumer reading both on the same publisher will see the same physical flow with two signs. That is the intended behaviour, the same way a proxied EVSE's own `meter/active-power` and its host circuit's reading disagree (see [`distribution-enclosure.md`](../devices/distribution-enclosure.md)). Concretely, on a distribution enclosure:

| This property | is the negation of | which uses |
|---|---|---|
| `grid` | the service `lugs` device's `meter/active-power`, **only where the lugs are the utility connection point** (see below) | the enclosure frame, positive = imported |
| `battery` | the BESS device's own `meter/active-power` | the BESS device frame, positive = discharging ([`bess.md`](../devices/bess.md)) |
| `pv` | a backfeeding PV circuit's `meter/active-power` | the enclosure frame, positive = into the busbar |

Publishing any of these as a **copy** of its counterpart rather than its negation is a sign inversion. Both values are correct in their own frame; neither is a substitute for the other.

**The `grid` row is conditional; `battery` and `pv` are not.** `battery` and `pv` describe the same flow as their counterpart in every topology, so the negation holds unconditionally. `grid` holds only where the service lugs *are* the utility connection point. Two common topologies break that: an **upstream DER**, such as a BESS wired between the utility and the main lugs, and an **enclosure chain**, where this enclosure is fed by another rather than by the service. In both cases the lugs measure the flow on the panel side of the intervening device while `grid` measures the flow on the utility side, and the two differ by whatever that device is contributing or absorbing. A publisher in either topology **computes** `grid` from the lugs reading together with the intervening DER; it does not obtain it by negating the lugs. A consumer must not derive one from the other without knowing the topology, which it can read from the lugs device's [`connection`](connection.md) node: `fed-by-device-id` names the intervening device when there is one.

This is not a rare case. See [`distribution-enclosure.md`](../devices/distribution-enclosure.md), whose worked multi-panel example carries exactly this arrangement.

## Absence semantics

Absence of the `power-flows` node means the device does not aggregate site power. A device populates the flows it can compute. Absence of an individual property means that flow is not published, which a consumer must read as "unknown" rather than as zero; see the caution about recovering it from the balance above.

## Publishers

A site coordinator that computes aggregate flows: today the distribution enclosure. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `meter` capability](meter.md) — single-point measurement, distinct from this site-level roll-up.
- [distribution-enclosure](../devices/distribution-enclosure.md) data model — the current publisher, and the definition of the enclosure reference frame this catalog's frame is the inverse of.
- [BESS](../devices/bess.md) data model — the device-frame counterpart of `battery`.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
