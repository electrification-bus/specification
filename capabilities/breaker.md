# Electrification Bus Capability: breaker

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.breaker` — overcurrent and fault **protection**.

**Node type:** `energy.ebus.capability.breaker`

This document is the canonical property catalog for the `breaker` capability. Data-model documents that use it (for example [`circuit.md`](../data-models/circuit.md)) reference this catalog and document only their device-specific conformance, rather than restating the properties.

## Overview

The `breaker` capability describes the overcurrent and fault **protection** provided by a circuit breaker. A device publishes it when it is protected by a breaker: a branch circuit inside a distribution enclosure, a standalone smart circuit breaker, or a proxy republishing an Eaton or Siemens smart breaker.

Protection is distinct from remote **control**. A breaker trips on a fault; a relay opens on command. The two are modelled as separate capabilities, `breaker` and [`switch`](switch.md), because they are physically separate mechanisms: Eaton's SBLCP protocol, for example, exposes them as two handles, a primary protective handle that trips on fault and is not remotely closeable, and a remote handle that a controller opens and closes. A device may publish `breaker` alone (a dumb breaker surveyed at commissioning), `switch` alone (a bare relay), both (a smart breaker), or neither.

Because capabilities are optional and their presence is a signal, publishing `breaker` means the device is breaker-protected; its absence means it is not (or the publisher does not expose the detail).

## Properties

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `rating` | integer | A | SHOULD | Continuous current rating. |
| `poles` | integer | — | MAY | Number of poles (1-4). A US split-phase 240 V breaker is `2`. |
| `interrupting-rating` | integer | kA | MAY | Interrupting capacity (kAIC), e.g. `10`, `65`, `100`. |
| `protection-functions` | enum | — | MAY | Multi-valued set of the protections this breaker provides: `OVERCURRENT`, `SHORT_CIRCUIT`, `GROUND_FAULT` (GFCI), `ARC_FAULT` (AFCI). |
| `trip-curve` | enum | — | MAY | Instantaneous trip curve: `B`, `C`, `D`, `K`, … |
| `trip-state` | enum | — | SHOULD | `OK`, `TRIPPED`, `STUCK`, `UNKNOWN`. A tripped breaker carries no current even if a co-located `switch/relay` reads `CLOSED`, so `trip-state` is not a relay state. |
| `trip-cause` | enum | — | MAY | Cause of the most recent trip: `OVERCURRENT`, `SHORT_CIRCUIT`, `GROUND_FAULT`, `ARC_FAULT`, `OVERVOLTAGE`, `UNKNOWN`. |

Optional further properties, adopted as consumers require them: `gfci-class`, `max-voltage`, `end-of-life` (relevant for solid-state breakers), `service-entrance-rated`.

Enum-valued properties are advertised through the Homie `$format` attribute so a consumer can read the value domain a publisher supports; publishers MAY extend the enums additively.

## Existing product capabilities considered

The property set reflects the capabilities of shipping smart-breaker products, each of which treats breaker data as first-class (not a label) and separates protection from remote control:

- **Eaton AbleEdge** — spec sheet and the SBLCP local control protocol: remote on/off independent of the trip mechanism; state open / closed / tripped; GFCI; 10 kAIC; a primary protective handle and a separate remote handle.
- **Siemens Inhab controllable circuit breaker** — solid-state dual-function (AFCI + GFCI), time-current curve, 10 / 65 / 100 kA interrupting ratings, gateway-fronted.

## Comparison to other standards

A comparison to smart-breaker data models in other standards will be added here as those standards are published.

## Publishers

Published by any device that is breaker-protected: the circuit device type ([`circuit.md`](../data-models/circuit.md)), including circuits published natively by a smart panel and circuits republished by a proxy fronting a smart breaker; and a distribution enclosure for its **main breaker** (`rating`, and its trip state where exposed).

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `switch` capability](switch.md) — the separate remote-control surface.
- [Electrification Bus circuit data model](../data-models/circuit.md) — the primary publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
