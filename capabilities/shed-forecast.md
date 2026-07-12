# Electrification Bus Capability: shed-forecast

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.shed-forecast` — a computed forecast of how long backup loads will continue to be served when the site is (or becomes) off-grid.

**Node type:** `energy.ebus.capability.shed-forecast`

This document is the canonical property catalog for the `shed-forecast` capability. Data-model documents that use it (today [`distribution-enclosure.md`](../data-models/distribution-enclosure.md), and a plug-in BESS for its own outlet loads) reference this catalog.

## Overview

`shed-forecast` answers the consumer-visible question "how long do my loads stay up?" off-grid. It is **computed knowledge**, not a direct measurement: a distribution enclosure computes it from the aggregate BESS state of energy across all commissioned BESS children, the per-circuit shed configuration, and per-circuit consumption history; a plug-in BESS computes it for its own `outlet` loads, which it authoritatively knows. It cannot be computed by a BESS in isolation for a whole-panel install, which is why (for that case) the forecast lives on the enclosure.

## Properties

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `total-time-remaining` | integer | min | SHOULD | At current state of energy, total time before all backed-up loads go unpowered. |
| `time-to-priority-shed` | integer | min | SHOULD | At current state of energy, time until priority-shed (e.g. `SOC_THRESHOLD`) circuits are auto-shed. |
| `full-charge-total-time-remaining` | integer | min | SHOULD | At 100% state of energy, total backup-duration capability. |
| `full-charge-time-to-priority-shed` | integer | min | SHOULD | At 100% state of energy, capability time until the priority-shed event. |
| `confidence` | enum | — | SHOULD | The algorithm's self-assessed confidence: `LOW`, `MEDIUM`, `HIGH`. Reflects accumulated usage history. |

## Aggregation and presence

On an enclosure with more than one commissioned BESS, the values are computed against the **aggregate** state of energy across all of them; a single set of values is published (per-BESS forecast detail is not exposed). On an enclosure, presence of the capability corresponds to at least one BESS being commissioned; with no BESS it is omitted entirely.

## Absence semantics

Absence of the `shed-forecast` node means the device does not compute a backup-time forecast (for an enclosure, that no BESS is commissioned).

## Publishers

A device that can compute the off-grid backup forecast for the loads it serves: today a distribution enclosure (from aggregate BESS state and per-circuit configuration) and a plug-in BESS (for its own outlet loads). The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [distribution-enclosure](../data-models/distribution-enclosure.md) and [bess](../data-models/bess.md) data models — the publishers.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
