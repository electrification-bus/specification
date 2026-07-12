# Electrification Bus Capability: charge-limit

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.charge-limit` — an EV charger's charge-current ceiling, composed by `min()` from several sources so that any of them can lower charging for any reason and the lowest wins.

**Node type:** `energy.ebus.capability.charge-limit`

This document is the canonical property catalog for the `charge-limit` capability. Data-model documents that use it (today the EVSE child in [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog.

## Overview

A charge-only EVSE has exactly one flexibility actuator: the current it offers the vehicle. Everything that reduces charging, the owner's standing preference, a home energy-management system, a grid signal, a Power Control System, resolves to **lowering that one ceiling**, and the effective ceiling is the **minimum** across all of them. So `charge-limit` is a small multi-source limit family (the same shape as the distribution enclosure's `pcs` import-limit family), not a request/response protocol: there is no "load-up" for a charger that cannot discharge (a future V2G EVSE that *can* discharge would additionally use the richer [`flex`](flex.md) surface), and no per-request acknowledgement, only an effective ceiling that many sources can pull down.

The **installer maximum is the immutable baseline** (a rating from the breaker size and J1772 derating); the settable slots only ever reduce below it. The effective offered current is published as [`meter`](meter.md)`/advertised-current`.

## Properties

| Property ID | Datatype | Unit | Req | Settable | Persistence | Description |
|---|---|---|---|---|---|---|
| `installer-max` | integer | A | SHOULD | no | — | Installer-configured maximum charge current (breaker rating, J1772 derating): the immutable ceiling. |
| `owner-limit` | integer | A | MAY | yes | policy | The owner's charge-current ceiling. Held until changed ("until further notice"), not a bounded duration. MUST be `<= installer-max`. |
| `requested-limit` | integer | A | MAY | yes | (device-defined) | An external controller's (HEMS / grid) charge-current ceiling. |
| `requested-limit-cause` | enum | — | MAY | no | — | Why the external limit is set: `LOCAL_OPTIMIZATION`, `GRID_OPTIMIZATION`, `UNKNOWN`. Records who is reducing charging and why (for attribution and consent). |

## Composition

The effective ceiling the EVSE offers the vehicle is the **minimum** of every applicable source: `installer-max`, `owner-limit`, `requested-limit`, and any active PCS import limit on the circuit feeding the EVSE. It is published as `meter/advertised-current`. Any source can lower charging; the lowest wins; no source needs to know about the others. The **owner and external slots are kept separate** (rather than one last-write-wins setpoint) so that a transient external reduction does not overwrite the owner's standing preference, and vice versa, exactly as the `pcs` import-limit family keeps its sources separate.

## Absence semantics

Absence of the `charge-limit` node means the EVSE has no adjustable charge-current ceiling (it charges at a fixed rate). Absence of a settable slot means no reduction from that source is in force.

## Publishers

An EVSE whose charge current can be limited. The property contracts above apply unchanged to any conformant publisher. (A future stand-alone eBus EVSE Device Specification may adopt this capability directly.)

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `meter` capability](meter.md) — where the effective `advertised-current` is published.
- [Electrification Bus `flex` capability](flex.md) — the richer shed/load-up surface for devices that can also increase or reverse (a future V2G EVSE, a water heater).
- [distribution-enclosure](../data-models/distribution-enclosure.md) data model — the current publisher (the proxied EVSE child).
- [Electrification Bus capability-type registry](../registries/capability-types.md).
