# Electrification Bus Capability: status

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.status` — a device's operational health: its overall fault state, the health of its communication link, and any active alerts, plus device-specific diagnostics.

**Node type:** `energy.ebus.capability.status`

This document is the canonical property catalog for the `status` capability. Data-model documents that use it (bess, water-heater, distribution-enclosure, utility-meter, pdu, and others) reference this catalog and document only their device-specific role and additions.

## Overview

`status` is the most widely reused eBus capability after `meter`: nearly every device type publishes some operational health. It has a small **common core** that every publisher can speak, plus room for **device-specific diagnostics** that only some devices expose. A consumer can rely on the core across all device types, and read the device-specific properties for the devices it understands.

The core answers three questions any device can answer: is it faulted, can it communicate, and does it have active alerts. Everything beyond that, network-interface health, component runtimes, relay state, configuration echoes, integration sub-states, is device-specific and optional.

## Properties

### Core

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `fault-state` | enum | MAY | Overall fault state: `OK`, `FAULT`, `UNKNOWN`. Publishers MAY extend the value set via `$format` for device-specific fault categories. |
| `communication-state` | enum | MAY | The publisher's view of its own communication / link health, to the device it represents (for a proxy) or to its backhaul (for a native device): `OK`, `DEGRADED`, `LOST`, `UNKNOWN`. Orthogonal to whether the eBus publisher is currently reporting to *its* consumers. |
| `active-alerts` | string | MAY | Human-readable current alert(s), when the device exposes them. |

### Device-specific diagnostics

A publisher MAY add status properties specific to it, advertised on its device and documented by its device model. The catalog defines only the core above; a device narrows or extends it. Established examples (each MAY, outside the core):

- **network-interface health** (a distribution enclosure): `ethernet` / `wifi` (boolean), `wifi-ssid`, `cloud-connection`;
- **configuration echoes** (a distribution enclosure): `postal-code`, `time-zone`;
- **relay state** (a distribution enclosure with a whole-panel relay): `relay` (`OPEN` / `CLOSED` / `UNKNOWN`);
- **component runtimes** (a water heater): `compressor-runtime`, `resistance-runtime-{upper,lower}` (hours), and vendor refrigerant-cycle diagnostics;
- **integration sub-states** (a proxied device such as a BESS behind an adapter): `authentication` (`OK` / `FAILED` / `EXPIRED` / `MISSING`), `discovery` (`OK` / `NOT_FOUND` / `SERIAL_MISMATCH`).

These are illustrative, not exhaustive; a publisher documents its own set in its device model.

## Conformance is per-device

Which core properties are published, and which device-specific ones, is a device-model decision. A utility meter may publish only `communication-state`; a water heater `fault-state` + `active-alerts` + runtimes; a BESS `communication-state` + `fault-state` + its integration sub-states; a distribution enclosure its network / relay / configuration set. See each device model for its subset.

## Absence semantics

Absence of the `status` node means the device does not expose operational health. Absence of an individual property is the usual "not reported". A device that cannot determine a core value publishes `UNKNOWN` where the enum offers it, rather than omitting, when it wants to positively signal "unknown".

## Why a distinct capability

Operational health is neither a measurement (`meter`), an identity fact (`info`), nor a control surface. It is the *is-it-well* signal a consumer polls to decide whether to trust and use a device. Its own capability, reused across device types, lets a consumer check health uniformly.

## Publishers

Any device that reports operational health: today the distribution enclosure, BESS, water heater, utility meter, and PDU, and by design any device type. The core contracts above apply unchanged to any conformant publisher; device-specific diagnostics are documented per device model.

## References

- [Electrification Bus framework specification](../framework.md)
- [bess](../data-models/bess.md), [water-heater](../data-models/water-heater.md), [distribution-enclosure](../data-models/distribution-enclosure.md), [utility-meter](../data-models/utility-meter.md), [pdu](../data-models/pdu.md) data models — publishers of this capability.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
