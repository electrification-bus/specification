# Electrification Bus Capability: power-flows

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.power-flows` — site-level aggregate power flows across all energy sources, computed by the device that coordinates the site.

**Node type:** `energy.ebus.capability.power-flows`

This document is the canonical property catalog for the `power-flows` capability. Data-model documents that use it (today [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog.

## Overview

`power-flows` is the **site-level aggregate** view: a single, coherent snapshot of how power is flowing across the whole site's sources and loads, computed by the site coordinator (a distribution enclosure) from its children and connected DER devices. It is distinct from a single point's [`meter`](meter.md): where `meter` reports one connection's measurement, `power-flows` is the computed roll-up across grid, storage, generation, and load.

## Properties

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `grid` | float | W | SHOULD | Grid power flow (positive = importing from grid). |
| `battery` | float | W | SHOULD | Battery power flow (positive = discharging). |
| `pv` | float | W | SHOULD | Solar PV power flow (positive = producing). |
| `site` | float | W | SHOULD | Total site power consumption. |

## Absence semantics

Absence of the `power-flows` node means the device does not aggregate site power. A device populates the flows it can compute.

## Publishers

A site coordinator that computes aggregate flows: today the distribution enclosure. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `meter` capability](meter.md) — single-point measurement, distinct from this site-level roll-up.
- [distribution-enclosure](../data-models/distribution-enclosure.md) data model — the current publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
