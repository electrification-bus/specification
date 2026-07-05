# Electrification Bus Capability: switch

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-05
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.switch` — a remotely-controllable relay (on/off **control**).

**Node type:** `energy.ebus.capability.switch`

This document is the canonical property catalog for the `switch` capability. Data-model documents that use it (for example [`circuit.md`](../data-models/circuit.md)) reference this catalog and document only their device-specific conformance, rather than restating the properties.

## Overview

The `switch` capability is the remote on/off **control** surface: a relay that opens or closes on command, or under an automatic policy such as load-shed or a Power Control System. A device publishes it when it has a controllable relay.

Control is distinct from **protection** ([`breaker`](breaker.md)). A relay opens on command; a breaker trips on a fault. The two are separate capabilities because they are physically separate mechanisms: Eaton's SBLCP protocol, for example, exposes a remote handle (this capability) alongside a primary protective handle (the breaker). A device may publish `switch` alone (a bare relay), `breaker` alone (a dumb breaker), both (a smart breaker), or neither.

Because capabilities are optional and their presence is a signal, publishing `switch` means the device is remotely controllable; its absence means it is not (or the publisher does not expose control).

## Properties

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `relay` | enum | — | MUST | when `relay-controllable` | Relay state: `OPEN`, `CLOSED`, `UNKNOWN`. Settable when `relay-controllable = true`. |
| `relay-controllable` | boolean | — | SHOULD | no | True = the relay can be opened and closed by command or automatic shed. False = locked (for example a circuit commissioned as permanently on). |
| `relay-requester` | enum | — | SHOULD | no | Source attribution for the last relay change: `USER`, `LOAD_SHED`, `PCS`, `CONFIGURATION`, `FAULT`, `NONE`, `UNKNOWN`. Publishers MAY extend via `$format`. |

Enum-valued properties are advertised through the Homie `$format` attribute so a consumer can read the value domain a publisher supports.

**Implementation note.** Some remote-relay mechanisms use a fail-safe timeout (for example the Eaton SBLCP remote handle requires a command refresh within 10 seconds, failing safe otherwise). That is a publisher concern, not a property of this capability.

## Relationship to load-shed and PCS

`load-shed` and `pcs` are policies that act on this capability's relay. They are meaningful only on a device that also publishes a controllable `switch`, and they correspond to the `LOAD_SHED` and `PCS` values of `relay-requester`. When a policy drives the relay, the publisher attributes the change through `relay-requester` so a consumer can tell an automatic action from a user action. The policy semantics themselves are defined by the capabilities and by the hosting device's model (for example how a circuit's load-shed participation couples to a distribution enclosure's enclosure-wide shed policy), not by this capability.

## Comparison to other standards

The `switch/relay` state corresponds to Matter's **On/Off** cluster, a long-standing public Matter cluster: a device that exposes a writable On/Off is remotely controllable, matching `relay-controllable`. eBus adds `relay-requester` (source attribution for the last change), which On/Off does not carry.

## Existing product capabilities considered

- **Eaton AbleEdge** — remote on/off "independent from the trip mechanism"; the SBLCP remote handle with a fail-safe timeout.
- **Siemens Inhab controllable circuit breaker** — on / standby control, gateway-fronted.

## Publishers

Published by any device with a controllable relay. Today that is the circuit device type ([`circuit.md`](../data-models/circuit.md)), including circuits published natively by a smart panel and circuits republished by a proxy fronting a smart breaker.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `breaker` capability](breaker.md) — the separate protection surface.
- [Electrification Bus circuit data model](../data-models/circuit.md) — the primary publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
