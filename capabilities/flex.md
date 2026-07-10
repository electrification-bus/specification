# Electrification Bus Capability: flex

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-10
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.flex` — the control-and-feedback surface of a flexible load: a controller asks the device to shed (curtail below its self-managed baseline) or load-up (drive above it), and the device reports how it is responding and the customer's opt-out stance.

**Node type:** `energy.ebus.capability.flex`

This document is the canonical property catalog for the `flex` capability. Data-model documents that use it (today [`water-heater.md`](../data-models/water-heater.md)) reference this catalog and document only their device-specific role.

## Overview

`flex` is the **device-side** control-and-feedback surface for demand response and load flexibility. A controller (typically a site energy-management system) issues a **request** to shed or load-up, and the device publishes how it is responding and whether the customer has opted out.

It is the load-side counterpart to [`grid-event`](grid-event.md): `grid-event` carries the grid's *ask* (a site-level signal), while `flex` is how an *individual load* is controlled and reports back. An EMS reads a `grid-event`, decides how to allocate the response across its loads, and drives each one through its `flex` surface. Where `grid-event` is publish-only, `flex` is a **control** capability: its `request` property is settable.

It is **cross-cutting and publisher-agnostic**: any controllable flexible load (a water heater, an HVAC system, an EV charger, a pool pump) MAY expose it. The property contracts below apply unchanged to any such publisher. A device MAY extend the `request` with device-specific refinements (for example a water heater's thermal load-up parameters), advertised in its own `$format` and documented by that device model.

**The control direction is first-class.** A flexible load has two opposite intents relative to its self-managed baseline: **shed** (curtail below baseline: the grid is stressed, or energy is expensive) and **load-up** (drive above baseline: surplus or cheap energy is available). These are opposite directions, not two ends of one "throttle" axis; a magnitude and an intensity modify the chosen direction.

## Standards

The shed / load-up command model and the response decomposition follow **CTA-2045-B** Basic DR (Shed, End Shed, Critical Peak, Grid Emergency, Load Up). The opt-out model aligns with **Matter's Device Energy Management** cluster (`0x0098`): the four-way `opt-out` is Matter's `OptOutStateEnum` (local versus grid optimization), and `request.cause` is Matter's `AdjustmentCauseEnum`. The load-up refinements a device MAY add derive from **Matter's Water Heater Management** `Boost` command. Matter DEM's *forecast-and-adjust* paradigm (an appliance advertising a time-sliced power forecast that an EMS negotiates) is deliberately **not** adopted: `flex` is an imperative command surface, matching the large CTA-2045 install base; a device that cannot forecast can still participate.

## Properties

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `request` | json | — | MAY | yes | The flexibility request to apply, as one atomic object (schema below). Setting this property issues the request; the publisher translates it to the device's native control protocol. The property's `$format` JSONSchema advertises **this device's** control surface (see [§Self-describing control surface](#self-describing-control-surface)). |
| `active-request` | json | — | MAY | — | The request currently in force (same shape as `request`) plus an `ends-at` timestamp, or null / absent when none is active. |
| `response` | enum | — | MAY | — | How the device is currently responding: `NONE` (no request in effect), `CURTAILED` (shedding), `BOOSTED` (loading up), `NOT_FOLLOWING` (a request is in effect but the device cannot currently honor it). The decomposed, vendor-neutral replacement for CTA-2045's 15-value operational-state enum. |
| `opt-out` | enum | — | MAY | — | The customer's demand-response opt-out stance: `NONE` (participating), `LOCAL` (opted out of local-EMS optimization only), `GRID` (opted out of grid / utility optimization only), `ALL` (opted out of both). See [§Opt-out and cause](#opt-out-and-cause). |

## `request` object schema

A settable Homie 5 `json` property; one `/set` carries the whole request atomically. The **canonical (maximal)** schema:

```json
{
  "mode":      "SHED" | "LOAD_UP" | "NORMAL",         // direction; required. NORMAL ends any request.
  "level":     0-100,                                 // optional %: magnitude within the direction
  "intensity": "PEAK" | "EMERGENCY" | "ADVANCED",     // optional: aggressiveness within the direction
  "duration":  <seconds>,                             // optional: request length; absent = until changed
  "cause":     "LOCAL_OPTIMIZATION" | "GRID_OPTIMIZATION"  // optional: why issued; gates opt-out
}
```

- `mode` is the direction. `SHED` reduces consumption; `LOAD_UP` increases it; `NORMAL` ends any active request and returns the device to self-management. Required.
- `level` is the per-direction magnitude as a percentage, honored to the resolution the device advertises (see below).
- `intensity` raises the aggressiveness of the chosen direction. On the shed side: `PEAK` (critical-peak, deeper curtailment) and `EMERGENCY` (grid-emergency, maximum curtailment, customer override discouraged). On the load-up side: `ADVANCED` (drive beyond the normal maximum to store extra energy; corresponds to CTA-2045 Advanced Load Up and Matter `EmergencyBoost`).
- `duration` is the request length in seconds; absent means until changed by a later request.
- `cause` states why the request is being issued, so the device can apply the customer's `opt-out` (see [§Opt-out and cause](#opt-out-and-cause)). Absent means unspecified.

A device MAY add **device-specific refinement fields** to this object, advertised in its `$format` and documented by its device model. For example, a water heater adds thermal `LOAD_UP` refinements (`target-percentage`, `temporary-setpoint`); a device that does not support them omits them from its schema.

## Self-describing control surface

The device advertises exactly what it accepts in the `request` property's `$format` **JSONSchema** (`request` is a `json` property, whose Homie 5 `$format` is a JSONSchema). The control **granularity is schema, not data**: rather than a separate property describing the resolution, the device narrows the `request` schema to its actual surface, and a controller MUST read that schema and send only what it permits.

This makes the schema the device's whole control-surface self-description: which `mode`s and `intensity`s it accepts, and, for `level`, exactly which values. The three common `level` cases:

- **On/off or named-level only** (a CTA-2045 SGD that sheds without a percentage): the schema **omits `level`**; `mode` (and `intensity`) alone drive it.

  ```json
  { "type":"object",
    "properties":{ "mode":{"enum":["SHED","LOAD_UP","NORMAL"]},
                   "intensity":{"enum":["PEAK","EMERGENCY","ADVANCED"]} },
    "required":["mode"] }
  ```

- **Continuous percentage:** `"level": { "type":"integer", "minimum":0, "maximum":100 }` (a device with fixed steps adds `"multipleOf": 10`).

- **A fixed set of discrete levels** (for example 40 / 60 / 100 %): `"level": { "enum": [40, 60, 100] }` — the schema names the exact supported values, which a coarse "discrete" category could not.

A controller derives its UI from the same schema (an `enum` → buttons, a range → a slider, a range with `multipleOf` → a stepped slider). This is more expressive than a granularity category and keeps the description where Homie intends it: on the property.

## Opt-out and cause

`opt-out` is four-way (Matter `OptOutStateEnum`), because a customer's stance depends on *who* is optimizing: `LOCAL` is the home EMS optimizing for the customer (cost, comfort, self-consumption); `GRID` is responding to a utility / grid signal. A real stance is "let my EMS shift my water heater to save money, but the utility does not get to touch it" (`GRID`). A device that models only a single on/off override uses `NONE` and `ALL` (the CTA-2045 "Grid Enabled" toggle maps to `ALL` when off).

To honor a directional opt-out, the device must know which class a request belongs to, which is what `request.cause` carries. The rule is: **the device honors a request unless the customer has opted out of its `cause`.** A request with no `cause` is treated as unspecified and honored subject only to `opt-out = ALL`.

## Why `flex` uses `json` when most eBus properties are scalars

`request` (and its read-only mirror `active-request`) uses the Homie 5 `json` datatype rather than a scalar, per [framework principle #10](../framework.md#design-principles) (scalars by default; `json` only for atomic compounds). A flexibility request is a compound command whose fields are interdependent (a required `mode` plus optional `level`, `intensity`, `duration`, `cause`, and any device refinements), and it must take effect as one indivisible unit. Decomposed into separate settable properties (`flex/mode`, `flex/duration`, ...), each `/set` would expose a partial-request window in which the device acts on a half-specified command. One `json` object applied by a single `/set` is atomic, matching how CTA-2045 and Matter each model a demand-response command as a single message. The cost is that a controller parses the object rather than reading a scalar, which is acceptable for an opt-in control surface a controller must already understand. `json` is a first-class Homie 5 datatype, and the `$format` JSONSchema validates the payload.

## Authorization

`request` is the only settable property on this capability. A consumer issuing demand response needs write access only to `flex/request`; everything else (`active-request`, `response`, `opt-out`) is read-only.

## Absence semantics

Absence of the `flex` node means the device is not controllable for demand response. Absence of `active-request`, or a null value, means no request is in force. `response = NONE` is the corresponding steady state.

## Why a distinct capability

A flexibility request is neither a relay toggle (`switch`), a hardware power limit (`pcs`), nor a measurement (`meter`). It is a graded, bidirectional modulation of a load's operation with its own response feedback and customer-consent model. Its own capability keeps that control surface separate from the on/off relay and the metering, and lets any flexible-load device type reuse it unchanged.

## Relationship to other signals

- **[`grid-event`](grid-event.md)** — the *ask* (site-level, publish-only). An EMS reads it and drives loads through `flex`.
- **`flex`** — the *doing* (per-load control + feedback). This capability.
- **[`price`](price.md)** — an economic incentive an EMS may weigh when deciding how to flex a load.

## Publishers

Any controllable flexible load: today the water heater ([`water-heater.md`](../data-models/water-heater.md)), and by design any HVAC system, EV charger, pool pump, or similar dispatchable load. Whether published natively or by a proxy (for example a CTA-2045 UCM bridge), the property contracts above apply unchanged.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `grid-event` capability](grid-event.md) — the site-level ask this capability responds to.
- [water-heater](../data-models/water-heater.md) data model — the first publisher, and where the water-heater-specific `request` refinements are documented.
- ANSI/CTA-2045-B; Matter Device Energy Management (`0x0098`) and Water Heater Management (`0x0094`) clusters.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
