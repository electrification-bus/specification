# Electrification Bus Capability: dispatch

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.dispatch` — external dispatch controls for a storage resource: settable charge / discharge rate setpoints and SOC limits by which a controller coordinates the device's real-time behaviour, plus the observables that report what is actually happening.

**Node type:** `energy.ebus.capability.dispatch`

This document is the canonical property catalog for the `dispatch` capability. Data-model documents that use it (today [`bess.md`](../data-models/bess.md)) reference this catalog.

## Overview

`dispatch` lets a controller, a distribution enclosure's power-management logic, an energy-management system, or a HEMS, coordinate a BESS's charge/discharge behaviour in real time. It is **MAY-level**: a publisher exposes it only when the underlying product offers the corresponding control surface. A device that does not publish `dispatch` follows its own vendor-internal control logic; external controllers can observe its state but cannot directly dispatch it.

## Properties

| Property ID | Datatype | Unit | Req | Settable | Persistence | Description |
|---|---|---|---|---|---|---|
| `charge-rate-set` | float | W | MAY | yes | watchdog | Requested charge rate. Positive = charge at this rate; `0` = do not charge. Honored when conditions allow (hardware limits, SOC constraints). |
| `discharge-rate-set` | float | W | MAY | yes | watchdog | Requested discharge rate. Positive = discharge at this rate; `0` = do not discharge. Same conditional-honoring semantics. |
| `max-soc-set` | float | % | MAY | yes | policy | Upper SOC limit (0-100); the device stops charging at this value. |
| `min-soc-set` | float | % | MAY | yes | policy | Lower SOC limit (0-100); the device stops discharging at this value. |
| `backup-reserve` | float | % | MAY | yes | policy | Off-grid energy reserve (0-100): the SOC floor held back for backup. A backup-mode policy; see the interaction note below. |
| `dispatch-watchdog-timeout` | integer | s | MAY | no | — | How long a watchdog-class setpoint persists before reverting to `dispatch-safe-default`. Published so controllers know the refresh cadence to keep dispatch active. |
| `dispatch-safe-default` | enum | — | MAY | no | — | What the device reverts to after a watchdog-class setpoint expires: `IDLE` (both rates effectively `0`), `VENDOR_DEFAULT` (vendor-internal logic resumes), `LAST_VALUE` (rare; slow-response systems only). |
| `dispatch-state` | enum | — | MAY | no | — | Current dispatch status: `IDLE`, `CHARGING_DISPATCHED`, `DISCHARGING_DISPATCHED`, `VENDOR_CONTROLLED` (no external setpoint, or one expired to `VENDOR_DEFAULT`), `UNKNOWN`. |
| `dispatch-controller` | string | — | MAY | no | — | Identifier of the most recent client to successfully write a settable in this capability (MQTT client ID, issuing device ID, or authenticated user). Empty / absent when no dispatch is active. |
| `charge-rate-actual` | float | W | MAY | no | — | Observed instantaneous charge rate. Distinguishes "honoring the setpoint" from "hardware-limited to a different rate". |
| `discharge-rate-actual` | float | W | MAY | no | — | Observed instantaneous discharge rate. |
| `available-charge-power` | float | W | MAY | no | — | Currently available charge-power headroom. |
| `available-discharge-power` | float | W | MAY | no | — | Currently available discharge-power headroom. |

## Persistence classes

Each settable declares its persistence semantics:

- **watchdog** — reverts to `dispatch-safe-default` if not refreshed within `dispatch-watchdog-timeout`. Used for rate setpoints, where a stale value (a crashed controller) must not leave the device charging or discharging indefinitely.
- **policy** — persists until overwritten or device reset. Used for SOC limits and `backup-reserve`, which are set-and-forget commissioning decisions where persistence across controller restarts is desirable.
- **expiry** *(reserved for future)* — value carries an explicit expiry timestamp; reverts after it passes. For time-bounded scheduled dispatch.

A publisher MUST honor the persistence class declared for each settable above.

## Conflict resolution

If multiple controllers write the same settable, the default is last-write-wins. A publisher MAY enforce stricter access control (by client-certificate role per the core security model) but this is implementation-specific. `dispatch-controller` is the recommended debugging observable for multi-writer scenarios.

## Interaction with `backup-reserve` and `min-soc-set`

A device that publishes both `backup-reserve` (the off-grid reserve, a backup-mode policy) and `min-soc-set` (the dispatch-time lower SOC limit) MUST honor whichever is **higher** when discharging: it does not discharge below either.

## Relationship to `status/operational-state`

When `dispatch-state` is anything other than `VENDOR_CONTROLLED`, the device's behaviour is being driven by external dispatch, and its `status/operational-state` (`IDLE`/`CHARGING`/`DISCHARGING`/`STANDBY`) reflects the *result* of that dispatch, not the cause. A controller treats `dispatch-state` as the authoritative signal for "who is driving this device right now".

## Absence semantics

Absence of the `dispatch` node means the device exposes no external dispatch surface; it self-manages.

## Publishers

Any storage resource that exposes an external dispatch surface: today the BESS. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `soc` capability](soc.md) — the reservoir state dispatch acts on; and [`status`](status.md) for `operational-state`.
- [bess](../data-models/bess.md) data model — the current publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
