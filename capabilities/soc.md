# Electrification Bus Capability: soc

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.soc` — the charge state of an energy reservoir: how much energy it currently holds, how much it can still absorb, and its capacity.

**Node type:** `energy.ebus.capability.soc`

This document is the canonical property catalog for the `soc` capability. Data-model documents that use it (today [`bess.md`](../data-models/bess.md) and [`water-heater.md`](../data-models/water-heater.md)) reference this catalog and document only their device-specific role and any device-specific refinements.

## Overview

`soc` exposes a device as an **energy reservoir**: a store that can be charged (energy put in) and discharged (energy drawn out), reported so an energy coordinator can treat a mixed fleet of reservoirs, a battery, a tank of hot water, with one vocabulary. A battery's reservoir is electrical; a water heater's is thermal (a hot-water tank is a thermal battery), and the same properties describe both. All properties are **read-only** (device-reported).

The `soc` ratio is a dimensionless fraction and is **directly comparable across reservoirs of any kind**; the energy magnitudes are **not** (a battery's `soe` is electrical kWh it can return to the grid, a water heater's is thermal Wh of stored heat, and the two are neither the same unit nor summable). Publishers therefore report each magnitude in its device's native energy unit and document that unit in their device model.

## Properties

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `soc` | float | % | MAY | State of charge: the fraction of capacity currently held (`0` = empty, `100` = full). A dimensionless ratio, comparable across all reservoirs. |
| `soe` | float | energy | MAY | State of energy: the energy currently stored and available to draw (the discharge side). Reported in the device's native energy unit (a BESS in kWh electrical, a water heater in Wh thermal). |
| `total-energy-storage` | float | energy | MAY | The reservoir's total energy capacity (empty to full), in the same unit as `soe`. |
| `loadup-headroom` | float | energy | MAY | The energy the reservoir can absorb **now** (the charge side), approximately `total-energy-storage − soe`. The dispatchable charge a load-up / charge action can take on. |

**Two opposite quantities.** `soc` and `soe` describe how much is **stored and available to draw** (discharge); `loadup-headroom` describes how much can still be **absorbed** (charge). They are complementary: `soe + loadup-headroom ≈ total-energy-storage`.

**Device-specific refinements.** A publisher MAY add reservoir refinements specific to its physics, advertised on its device and documented by that device model; for example a water heater adds a volumetric `available-volume` (L) and a `heat-required` (thermal Wh to reach setpoint). The catalog defines the reservoir core above; a device narrows or extends it.

## Conformance is per-device

Which properties are published, at what requirement level and in what unit, is a device-model decision. A **BESS** publishes `soc` (its headline figure) and `soe` in kWh (electrical). A **water heater** publishes the thermal view in Wh, all optional, plus its volumetric and heat-required refinements. See each device model for its subset.

## Aggregation

On a parent device that fronts several reservoirs (a BESS parent over its battery children), the published values are aggregated across the children; the parent documents the aggregation.

## Absence semantics

Absence of the `soc` node means the device does not expose a reservoir view. Absence of an individual property is the usual "not reported"; publishers populate what they measure.

## Why a distinct capability

Charge state is neither a power/energy measurement at a point (`meter`) nor a control surface (`flex`). It is the *stored-energy state* of a reservoir, the quantity a coordinator reads to decide how much a resource can shift, charge, or discharge. Its own capability lets any storage-bearing device, electrical or thermal, publish it with one vocabulary.

## Publishers

Any device that is an energy reservoir: today a BESS (electrical storage) and a water heater (thermal storage), and by design any future dispatchable store. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [bess](../data-models/bess.md) (electrical reservoir) and [water-heater](../data-models/water-heater.md) (thermal reservoir) data models — publishers of this capability.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
