# Electrification Bus Capability: output-island

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.output-island` — device-output island (UPS) state and control for a plug-in BESS or UPS: a clean island of the device's own outlets, isolated from premises wiring.

**Node type:** `energy.ebus.capability.output-island`

This document is the canonical property catalog for the `output-island` capability. Data-model documents that use it (today [`bess.md`](../data-models/bess.md)) reference this catalog.

## Overview

`output-island` is the **device-output** island scope: the device forms a clean island of its own `outlet` children, physically isolated from the premises wiring by an internal transfer switch, and **never energizes premises wiring**. It is kept strictly separate from the premises-wiring island scope, which lives on the MID [`grid`](grid.md) capability, and nests inside it. A plug-in BESS or UPS publishes `output-island`; a premises-wiring grid-forming BESS does not (it uses the MID `grid`); a no-backup device publishes neither.

## Properties

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `state` | enum | — | SHOULD | no | Current output state: `PASS_THROUGH` (input present; outlets powered through from the input, battery idle or charging), `ON_BATTERY` (islanded; outlets powered from battery / solar, isolated from the input), `NO_OUTPUT` (no input and no output), `UNKNOWN`. |
| `mode` | enum | — | MAY | yes | Requested output mode: `FOLLOW_INPUT` (normal; island automatically only on loss of input) or `ISLAND` (force the device-output island now, running the outlets from battery even with input present). |
| `transfer-time` | float | ms | MAY | no | Nameplate input-to-battery switchover time (the UPS ride-through spec). |

`state` answers "is the device powering its outlets from the input or from its own battery"; `mode` is the control. This capability never energizes premises wiring; that is exclusively the MID `grid` scope.

## Backup-runtime forecast

This capability carries no backup-time-remaining figure. A plug-in BESS that forecasts its backup runtime publishes the [`shed-forecast`](shed-forecast.md) capability, computing it from its own outlet loads (which it authoritatively knows), the same capability a distribution enclosure publishes for a centralized BESS.

## Absence semantics

Absence of the `output-island` node means the device does not form a device-output island.

## Publishers

A plug-in BESS or UPS that isolates its own outlets. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `grid` capability](grid.md) — the premises-wiring island scope this nests within.
- [bess](../data-models/bess.md) data model — the current publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
