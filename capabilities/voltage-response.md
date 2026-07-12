# Electrification Bus Capability: voltage-response

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.voltage-response` — a voltage-triggered real-power response: the publisher reduces its power at the connection point when service voltage leaves an acceptable band, to help hold voltage in range and relieve the shared distribution transformer.

**Node type:** `energy.ebus.capability.voltage-response`

This document is the canonical property catalog for the `voltage-response` capability. Data-model documents that use it (today [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog and document only their device-specific role.

## Overview

`voltage-response` is the **load-side analog of Volt-Watt**: when measured service voltage falls below a configured **undervoltage** threshold, the publisher reduces its **import current**, lowering its draw across the shared secondary and distribution transformer so service voltage recovers toward its acceptable band. When voltage rises back above a restore threshold (the deadband), normal operation resumes.

The primary form is a **static undervoltage setpoint**: a fixed threshold, pre-agreed with the utility and set at commissioning, enforced locally. It is a hard setpoint, not a continuously-varying control loop, and it needs only local voltage measurement: no meter and no upstream signaling channel. Because the threshold is a standing local setpoint, it runs **autonomously** and is a **resilient fallback**: it keeps protecting the transformer even when a signaled power envelope ([`doe`](doe.md)) is stale or absent. A **proportional response** (a piecewise Volt-Watt-style `response-curve`) is an optional richer form for implementations that want it.

**This is real-power curtailment, not reactive support.** `voltage-response` reduces real-power flow (a current limit); it is distinct from a DER's reactive Volt-VAr function, which injects or absorbs VArs. The lineage it shares is with Volt-*Watt* (real power versus voltage), not Volt-VAr.

**Direction.** This version defines the **undervoltage** direction (reduce *import* on voltage sag), which is the form with a concrete consumer today (panel-only transformer support). An **overvoltage** direction (reduce *export* on voltage swell, the classic DER Volt-Watt case) is a natural future addition that mirrors the undervoltage fields on the export side; it is noted in [§Overvoltage direction](#overvoltage-direction-future) but not specified here. This import/export duality parallels [`doe`](doe.md) and [`price`](price.md).

## Standards

The proportional form is the load-side inverse of the [IEEE 2030.5 / CSIP](https://standards.ieee.org/ieee/2030.5/5897/) Volt-Watt function (`opModVoltWatt`): where a DER's Volt-Watt curtails *generation* on over-voltage, this curtails *consumption* on under-voltage. Thresholds are expressed relative to `nominal-voltage` in per-unit, in keeping with ANSI C84.1 service-voltage ranges (Range A is approximately 0.95-1.05 pu). It is deliberately **not** the reactive Volt-VAr function (`opModVoltVar`), which is a per-DER reactive-power control and belongs to a forthcoming `der-control` capability.

## Properties

The static undervoltage setpoint is carried as plain scalars (per [framework principle #10](../framework.md#design-principles), scalars by default); only the optional proportional curve is a `json` compound.

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `nominal-voltage` | float | V | SHOULD | no | Reference voltage for the per-unit thresholds (e.g. `120` or `240`). |
| `undervoltage-threshold` | float | pu | SHOULD | no | The voltage at or below which the publisher reduces its import current (e.g. `0.95`). |
| `restore-threshold` | float | pu | SHOULD | no | The voltage at or above which normal operation resumes; MUST be `>= undervoltage-threshold`. The gap is the deadband that prevents chatter (e.g. `0.96`). |
| `reduced-import-limit` | float | A | SHOULD | no | The import current limit the publisher applies while voltage is below `undervoltage-threshold`. (A publisher MAY instead express this as a fraction of the prevailing limit via `response-curve`.) |
| `mode` | enum | — | MAY | no | `OFF` (function present but not acting), `AUTONOMOUS` (the publisher enforces the setpoint locally). |
| `response-curve` | json | — | MAY | no | **Optional richer form.** A piecewise Volt-Watt-style curve, one atomic object (schema below), for a proportional rather than single-threshold response. When present, it supersedes the scalar threshold properties above. |

A single service-level threshold is the baseline. Per-phase thresholds (one setpoint per leg) are a possible future refinement, not defined here.

## Response-curve schema (optional)

When `response-curve` is published, its value is one object: an ordered list of `{ voltage, power-fraction }` breakpoints plus a deadband. Modeled on IEEE 2030.5 `opModVoltWatt`.

```json
{
  "points": [
    { "voltage": 0.96, "power-fraction": 1.00 },   // voltage in pu (of nominal-voltage)
    { "voltage": 0.95, "power-fraction": 1.00 },   // power-fraction 0..1: the fraction of the
    { "voltage": 0.92, "power-fraction": 0.50 },   //   prevailing import allowance permitted here
    { "voltage": 0.90, "power-fraction": 0.20 }
  ],
  "deadband": { "engage-voltage": 0.95, "restore-voltage": 0.96 }
}
```

Points are ordered by descending `voltage`; the publisher interpolates between breakpoints. `power-fraction` is the fraction of the prevailing import allowance permitted at that voltage (the publisher applies it as a current reduction, reconciling to amps itself, per [§Units](#units)). The `deadband` gives the engage / restore hysteresis, the proportional-form analog of `undervoltage-threshold` / `restore-threshold`.

## Relationship to `pcs` enforcement

`voltage-response` carries the **configuration** (how the publisher will respond); it does not itself carry the live limit. On a distribution enclosure, the current reduction it imposes is enforced through the enclosure's [`pcs`](../data-models/distribution-enclosure.md#pcs) arbitration: the enclosure reconciles the voltage-support threshold to a current reduction that feeds the `pcs` `min()`, and `pcs` reports `binding-constraint = VOLTAGE` when the voltage reduction is the binding limit. Reading `voltage-response` tells a subscriber *what the publisher will do*; reading `pcs/import-limit` and `pcs/binding-constraint` tells it *what is being enforced right now*.

The interaction with the dynamic grid limit is complementary: a utility power envelope (`doe`, watts) converts to a *higher* current allowance as voltage falls (`I = P / (V·pf)`), while the voltage-support reduction pulls the effective `min()` back down when voltage is below the threshold. The two are independent constraints on the same actuator, reconciled by the `pcs`.

## Units

Each quantity stays in its native unit: the thresholds in per-unit of `nominal-voltage` (volts), the reduced limit and enforcement in amps. The publisher (the enclosure) holds the voltage threshold and applies a current limit, the same single-point-of-reconciliation stance by which it turns a `doe` power envelope (W) into a `pcs` import limit (A). The model does not flatten quantities into a single unit.

## Publish-only

This capability is publish-only by default: the setpoint is provisioned out of band (device configuration, pre-agreed with the utility), exactly as [`doe`](doe.md) is fed out of band, and the publisher publishes what it will act on. Whether an authorized controller may *set* the threshold (an EMS or utility proxy updating it live) is left to a future revision, alongside the deferred utility-*signaled* form.

## Absence semantics

Absence of the `voltage-response` node means the publisher has no voltage-response function. Absence of an individual property is the usual "unknown / not configured" per Homie convention; `mode = OFF` positively records "the function exists but is not currently acting," which absence cannot distinguish.

## Why a distinct capability

A voltage-triggered current reduction is neither a measurement ([`meter`](meter.md)), a watts operating envelope ([`doe`](doe.md)), nor the amps enforcement / arbitration surface (`pcs`). It is the **volts-domain response configuration** that sits upstream of enforcement: the rule that maps a voltage condition to a current reduction. Its own capability keeps that volts threshold separate from the watts envelope and the amps enforcement, each in its native unit and on its authoritative owner.

## Overvoltage direction (future)

The undervoltage direction above reduces *import* on a voltage sag. The symmetric **overvoltage** direction reduces *export* on a voltage swell (the classic DER Volt-Watt over-voltage curtailment, to counter voltage rise from back-feed). When a consumer for it exists, it is added additively here as the export-side mirror (`overvoltage-threshold`, its restore threshold, and a `reduced-export-limit`), and its enforcement composes on the export side (a DER-control / `doe/export-limit` concern, not a `pcs` import-limit slot). No rename of this capability is required to add it.

## Publishers

Any device that measures its connection-point voltage and can curtail in response: today the distribution enclosure (which measures service voltage and holds a current limit). A future utility-*signaled* voltage obligation (the utility updating the threshold or curve the way `doe` signals a power envelope) would live on the meter / gateway per [framework principle #7](../framework.md#design-principles), analogous to `doe`; it is deferred until a real signaling channel and consumer exist.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `doe` capability](doe.md) — the watts operating envelope the enclosure reconciles alongside this volts threshold.
- [distribution-enclosure](../data-models/distribution-enclosure.md) data model, and [`pcs`](pcs.md) — the publisher and the arbitration / enforcement surface.
- IEEE 2030.5 / CSIP Volt-Watt (`opModVoltWatt`); ANSI C84.1 service-voltage ranges.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
