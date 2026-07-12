# Electrification Bus Capability: grid-forming

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.grid-forming` — a single inverter's grid-forming capability and current state: whether it can form the AC grid, and whether it is doing so right now.

**Node type:** `energy.ebus.capability.grid-forming`

This document is the canonical property catalog for the `grid-forming` capability. Data-model documents that use it (today the inverter children in [`bess.md`](../data-models/bess.md)) reference this catalog.

## Overview

`grid-forming` is the **per-inverter** detail of which specific inverter is establishing the AC voltage / frequency reference, exposed on an inverter child device when a vendor surfaces that detail. It complements the site-level [`grid`](grid.md) capability's `grid-forming-entity`, which names the grid-forming DER at *parent* granularity (externally observable on all systems). This capability adds the finer, vendor-specific inverter-level state where available.

## Properties

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `capable` | boolean | MUST (when the capability is published) | Static hardware capability: does this inverter support grid-forming operation at all? |
| `active` | boolean | SHOULD (when `capable = true`) | Current state: is this inverter actively grid-forming right now? When `false` and the inverter is energized, it is grid-following. |

## Relationship to `grid/grid-forming-entity`

The two representations are coherent and layered: `<mid>/grid/grid-forming-entity == <der-parent-id>` says "this DER is the grid-forming entity" (externally observable, all systems); `<inverter-child-id>/grid-forming/active == true` says "this specific inverter is the one actively grid-forming" (vendor-specific, when published). The MID-level value is authoritative for *which DER* is grid-forming; the inverter-level flags are descriptive detail when available.

## Absence semantics

Absence of the `grid-forming` node means the publisher does not expose per-inverter grid-forming detail (the common case; the DER-level signal on [`grid`](grid.md) still applies).

## Publishers

Inverter child devices whose vendor exposes per-inverter grid-forming state (today under a BESS). The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `grid` capability](grid.md) — the site-level grid-forming-entity this refines.
- [bess](../data-models/bess.md) data model — the current publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
