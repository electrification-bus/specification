# Electrification Bus Capability: grid

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.grid` — the state of the AC grid boundary: whether the site is grid-tied or islanded, the sensed health of the utility supply, and which device is forming the AC reference.

**Node type:** `energy.ebus.capability.grid`

This document is the canonical property catalog for the `grid` capability. Data-model documents that use it (today [`bess.md`](../data-models/bess.md), [`distribution-enclosure.md`](../data-models/distribution-enclosure.md), and [`utility-meter.md`](../data-models/utility-meter.md)) reference this catalog and document only their device-specific role and property subset.

## Overview

`grid` reports the **grid-boundary state** a device authoritatively observes. Two kinds of device publish it, each the subset it is qualified for (per [framework principle #7](../framework.md#design-principles), properties live on the device that authoritatively knows them):

- a **microgrid interconnect device (MID)** is the islanding authority: it knows whether the site is connected to or islanded from the utility, and which device is forming the AC reference;
- a device that **senses the AC supply** (a MID, or a utility meter at the service entrance) knows the sensed condition of the utility supply.

The same node type serves both because they publish the same conceptual signal, the state of the AC grid they observe; they differ only in which properties each is qualified to report.

## Properties

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `islanding-state` | enum | MAY | Whether the site is connected to or islanded from the utility: `ON_GRID`, `OFF_GRID`, `UNKNOWN`. Reflects the interconnect **relay position**. Published by the islanding authority (a MID); a device that does not sense the interconnect (a utility meter) does not publish it. |
| `grid-state` | enum | MAY | Sensed condition of the utility AC supply: `UP`, `DOWN`, `DEGRADED`, `UNKNOWN`. `DEGRADED` (outside the `UP` band but not a declared outage) is optional; a publisher SHOULD distinguish it when it has the measurement capability (a black-box proxied MID typically reports only `UP` / `DOWN` / `UNKNOWN`). Published by any device that senses the supply (a MID, a utility meter). |
| `grid-forming-entity` | string | MAY | Identity of the device establishing the AC voltage / frequency reference: `"GRID"` when grid-tied, or the Homie device ID of the grid-forming device (typically the DER parent device: a BESS, a V2H EVSE, a generator) when islanded. Empty string or absent during transitions or when unknown. Published by the islanding authority (a MID). |
| `last-outage-time` | datetime | MAY | Timestamp (ISO-8601 UTC) of the most recent transition from `UP` / `DEGRADED` to `DOWN` observed. |
| `last-restoration-time` | datetime | MAY | Timestamp (ISO-8601 UTC) of the most recent transition from `DOWN` to `UP` / `DEGRADED` observed. |

All are MAY at the catalog level; a device model sets the requirement level for the subset it publishes (a MID makes `islanding-state` MUST).

## Publisher qualification

- A **MID** publishes `islanding-state` (its defining signal), `grid-forming-entity`, and `grid-state`. It is the authority on whether the site is islanded and which device forms the reference.
- A **utility meter** publishes only `grid-state` and the outage / restoration timestamps: it observes the health of the supply at the service entrance but is **not** qualified for `islanding-state` (whether the customer site is islanded is a MID concern) or `grid-forming-entity` (which device forms the AC reference is a MID concern). It omits those.

## Relationships between the properties

`islanding-state` reflects the interconnect relay position (are we connected?); `grid-state` reflects what is sensed about the utility supply itself (is power available?). They can differ: `OFF_GRID` with `grid-state = UP` is an intentional island, `OFF_GRID` with `grid-state = DOWN` is an outage.

`grid-forming-entity` identifies *which* device is the reference. When grid-tied it is always `"GRID"`; when islanded exactly one DER forms the grid and its parent device ID is the value. The correlations hold: `islanding-state == ON_GRID` implies `grid-forming-entity == "GRID"`; `islanding-state == OFF_GRID` implies `grid-forming-entity` is a device ID. A consumer may use either for a binary tied-versus-islanded decision; `grid-forming-entity` adds the reference device's identity.

**Grid-forming-entity granularity.** The value is the DER **parent** device ID (the BESS, the V2H EVSE parent, the generator), not an inverter child ID: vendors typically do not expose per-inverter grid-forming coordination, and parent granularity matches what is externally observable. Where a vendor does surface per-inverter grid-forming state, that per-inverter detail lives on the inverter child via the separate `grid-forming` capability.

## Native MIDs

A native eBus MID (implementing the in-progress MID data-model companion specification) publishes additional `grid` properties, a `system-state` machine, `mid-relay-state`, cross-side phase angles, `sync-ready`, and so on, plus per-side meter children. The properties above are the minimum surface any MID, proxied or native, publishes.

## Absence semantics

Absence of the `grid` node means the device does not report grid-boundary state. Absence of an individual property is the usual "not reported / not qualified to report"; each publisher populates the subset it authoritatively knows.

## Why a distinct capability

Grid-boundary state is neither a measurement (`meter`), an operating limit (`doe`), nor a discrete grid event (`grid-event`). It is the standing *state of the connection to the utility*, the signal a backup coordinator or site EMS reads to know whether the site is tied or islanded and whether utility power is available. Its own capability lets any device that observes that boundary, a MID or a meter, publish it with one vocabulary.

## Publishers

Any device that authoritatively observes the grid boundary: today a MID (as a child of a distribution enclosure or a BESS) and a utility meter. The property contracts above apply unchanged to any conformant publisher, which populates the subset it is qualified for.

## References

- [Electrification Bus framework specification](../framework.md)
- [distribution-enclosure](../data-models/distribution-enclosure.md) and [bess](../data-models/bess.md) (MID publishers) and [utility-meter](../data-models/utility-meter.md) (supply-health publisher) data models.
- [Electrification Bus `grid-event` capability](grid-event.md) — discrete grid events, distinct from this standing state.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
