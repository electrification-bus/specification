# Electrification Bus Capability: load-shed

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.load-shed` — a circuit's participation in load-shedding: its shed class, and (extensibly) the triggers under which it is shed.

**Node type:** `energy.ebus.capability.load-shed`

This document is the canonical property catalog for the `load-shed` capability. Data-model documents that use it (today [`circuit.md`](../data-models/circuit.md)) reference this catalog.

> Note: the node is `load-shed` (the topic is `load-shed/priority`). An earlier registry entry named this capability `priority` after its property and listed properties (`relay-controllable`, PCS metadata) that have since moved to `switch` and `pcs`; that entry is superseded by this catalog.

## Overview

`load-shed` marks how a circuit participates when its host coordinates load-shedding, typically a distribution enclosure preserving backup runtime while off-grid. It is a **policy that acts on the circuit's relay**: it is meaningful only on a circuit that also publishes a controllable [`switch`](switch.md), and it corresponds to the `LOAD_SHED` value of `switch/relay-requester`. It is distinct from [`pcs`](../data-models/distribution-enclosure.md#pcs): a PCS controls circuits to keep site import/export within a binding limit, not to preserve backup runtime; a circuit may participate in one, both, or neither.

## Properties

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `priority` | enum | SHOULD | The circuit's shedding class. Baseline (every host): `UNKNOWN`, `NEVER`, `OFF_GRID`. Optional additional triggers are advertised in the property's `$format`: `SOC_THRESHOLD` and future spec- or vendor-defined values. |

## Shed triggers and extensibility

The set of shed triggers a host supports is discoverable from the `$format` on this `priority` property: the enum values listed there are exactly the triggers that host implements. The baseline `UNKNOWN` / `NEVER` / `OFF_GRID` are required of every conforming host; others (`SOC_THRESHOLD`, plus future extensions) appear in `$format` only when implemented. Each optional trigger that has a tunable parameter publishes that parameter as a companion property on the **host's** shed surface, named as the lowercase-hyphenated form of the enum value (`SOC_THRESHOLD` corresponds to `shed/soc-threshold` on a distribution enclosure). Triggers with no tunable (for example `OFF_GRID`, which fires unconditionally when islanded) publish no companion. Vendors introducing new triggers should propose them upstream so the registry can track them and prevent name collisions.

## Host interaction

The *interaction* of `load-shed/priority` with a host's enclosure-wide shed policy, the SOC threshold, the shed forecast, and the effective shed gate, is host-specific and is defined in the host's model (see [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)). This capability defines the per-circuit vocabulary; the host defines how it acts on it.

## Absence semantics

Absence of the `load-shed` node means the circuit has no shed policy (its host does not coordinate shedding, or this circuit is excluded).

## Publishers

Any circuit whose host coordinates load-shedding: a load circuit or a feed circuit that publishes a controllable `switch`. The property contract above applies unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `switch` capability](switch.md) — the relay this policy acts on.
- [circuit](../data-models/circuit.md) data model — the current publisher; and [distribution-enclosure](../data-models/distribution-enclosure.md) for the host-side shed policy.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
