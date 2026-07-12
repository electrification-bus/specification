# Electrification Bus Capability: door

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.door` — the state of a digitally-monitored access door on an enclosure or cabinet.

**Node type:** `energy.ebus.capability.door`

This document is the canonical property catalog for the `door` capability. Data-model documents that use it (today [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog.

## Overview

Some enclosures expose a sensor on their access door (for access to breakers, terminals, and so on). A device with such a sensor publishes `door`; a device without one omits it.

## Properties

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `state` | enum | MUST | Door state: `OPEN`, `CLOSED`, `UNKNOWN`. |

## Absence semantics

Absence of the `door` node means the device has no monitored door (or does not expose one).

## Publishers

Any enclosure or cabinet with a monitored access door: today the distribution enclosure. The property contract above applies unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [distribution-enclosure](../data-models/distribution-enclosure.md) data model — the current publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
