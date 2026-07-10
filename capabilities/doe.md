# Electrification Bus Capability: doe

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-09
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.doe` — a dynamic operating envelope: the import and export operating limits a device authoritatively knows.

**Node type:** `energy.ebus.capability.doe`

This document is the canonical property catalog for the `doe` capability. Data-model documents that use it (for example [`utility-meter.md`](../data-models/utility-meter.md) and [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog and document only their device-specific role.

## Overview

The `doe` capability carries a **dynamic operating envelope (DOE)**: the import and export operating limits a device authoritatively knows, each a power limit with its source and (where defined) its validity window, optionally delivered as a schedule of upcoming envelopes.

It is **publish-only** and **publisher-agnostic**. Per [framework principle #7](../framework.md#design-principles) (properties live on the device that authoritatively knows them), any device that authoritatively knows an operating envelope publishes it. Two publishers are defined today:

- a **utility meter** — the utility's signal at the service point (a source of the envelope on eBus);
- a **distribution enclosure** — the envelope the enclosure has obtained and is acting on (a read-only representation of its acting-on state).

More than one may be present for a single site (a meter's utility signal and an enclosure's acting-on state), and that is expected, not a conflict: they are **not competing authorities**. Each publishes its own authoritative view; a consumer reads whichever layer it needs and reconciles them itself. How a device *obtains* its envelope — AMI / IEEE 2030.5 to a meter, an OpenADR client or a fleet / DERMS API into an enclosure, or a subscription to another eBus `doe` publisher — is a deployment and policy concern (typically a configuration choice), not defined by this capability.

## Standards

The term *dynamic operating envelope* is from [IEEE 2030.5 / CSIP](https://standards.ieee.org/ieee/2030.5/5897/), where it names the utility-issued operating constraints a customer site agrees to remain within. In Matter 1.5 terminology, the import side corresponds to the Meter Identification cluster's `PowerThreshold` attribute (Section 9.10 of the Matter 1.5 Application Cluster Specification); the export side has no Matter 1.5 equivalent and is proposed for a future Matter release. In [UL 3141](https://www.shopulstandards.com/ProductDetail.aspx?productId=UL3141) / NEC 2026 Article 130 terms, the import and export limits are the Power Import Limit (PIL) and Power Export Limit (PEL) respectively.

## Properties

The envelope is carried as two `json` properties, one per direction (`import-limit` and `export-limit`), rather than as a family of parallel scalar properties. This follows [framework principle #10](../framework.md#design-principles) (`json` only for atomic compounds): a limit, its source, and its validity window are one envelope that must be read as a unit. Spread across separately-retained scalar topics, a subscriber cannot tell whether the validity window it reads belongs to the limit it reads, or when each was published; one retained object per direction makes each envelope update a single atomic transaction.

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `import-limit` | json | — | MAY | no | The import-side operating envelope: a JSON array of one or more envelope objects (schema below), ordered by `start-time`. Absent when there is no import limit. |
| `export-limit` | json | — | MAY | no | The export-side operating envelope, same schema. Absent when there is no export limit. |

## Envelope object schema

Each property's value is a JSON **array** of envelope objects (the property carries a `$format` JSONSchema constraining it). A single current envelope is an array of one; a schedule of upcoming envelopes is a longer array. Each object:

```json
{
  "power-limit":          3400,                    // integer W, real-power limit; non-negative
  "apparent-power-limit": 3600,                    // integer VA, optional (Matter apparentPowerThreshold)
  "source":               "GRID",                  // optional enum; absent = UNKNOWN
  "start-time":           "2026-07-01T16:00:00Z",  // optional ISO-8601 UTC; absent = effective now
  "end-time":             "2026-07-01T20:00:00Z"   // optional ISO-8601 UTC; absent = until superseded
}
```

- **At least one** of `power-limit` / `apparent-power-limit` MUST be present; an envelope with neither is meaningless. Both are non-negative integers (an operating envelope is a setpoint, not a measurement, and is practically delivered at watt-or-VA-or-greater granularity). `power-limit` is UL 3141 PIL / PEL and Matter `PowerThresholdStruct.powerThreshold`; `apparent-power-limit` is Matter `apparentPowerThreshold`.
- **Reactive power is not carried here.** In IEEE 2030.5 / CSIP, reactive-power limits and controls (volt-var, fixed power factor, fixed / max VAr) are per-DER grid-support functions applied at the inverter, not connection-point envelope limits; they belong to a forthcoming `der-control` capability, not `doe`. A `power-limit` (W) together with an `apparent-power-limit` (VA) already bound reactive power at the connection point (`|VAr| <= sqrt(VA^2 - W^2)`).
- `source`: the limit's origin. `CONTRACT` (service contract / customer agreement), `REGULATOR` (permanent regulatory mandate), `EQUIPMENT` (equipment / conductor rating), `GRID` (dynamic utility grid-management action: distribution-transformer protection, DR event, congestion management), `UNKNOWN`. Absent means `UNKNOWN`. `GRID` distinguishes a temporary utility action from a permanent `REGULATOR` mandate, closing a gap in Matter 1.5's `PowerThresholdSourceEnum`.
- `start-time` / `end-time`: ISO-8601 UTC. `start-time` absent means effective immediately; `end-time` absent means in force until superseded by a later publish (typical for static / contract limits).

## Selecting the effective envelope

The retained array is the publisher's complete current schedule for that direction, and each publish replaces it atomically. A subscriber determines the **effective** envelope as the array element whose `[start-time, end-time)` window contains the current time. If two windows overlap, the element with the latest `start-time` wins. If no element's window contains the current time (a gap in the schedule), there is no signaled limit for that direction, and the subscriber falls back to its local equipment / static rating. Time-based selection needs a synced clock; a publisher reports its own on `status`/`time-sync-state` where it has one.

## Scheduling and the safety asymmetry

Elements with a future `start-time` are pre-announced upcoming envelopes; a scheduling subscriber applies each as its window becomes current. Because mis-timing a limit is not symmetric, a subscriber that does not implement scheduling MUST behave conservatively: it MAY apply an upcoming **stricter** (lower) limit early, but MUST NOT apply an upcoming **looser** (higher) limit before its `start-time`. Publishers SHOULD prune elements whose `end-time` is already in the past.

## Publish-only

This capability is publish-only; no `/set` topic is defined. The envelope's source is configured out of band (an AMI head-end / IEEE 2030.5 channel to a meter, an OpenADR client or fleet / DERMS API to an enclosure, and so on); the publisher publishes the resulting values to the eBus broker, and subscribers read them and act locally. This separation — the source owns the envelope, the publisher owns publication, subscribers own enforcement — keeps authorization simple: no subscriber needs write permission to any `doe` property.

## Absence semantics

Absence of `import-limit` (respectively `export-limit`) means no limit in that direction; a subscriber falls back to its local equipment / static rating. An empty array is equivalent to absence. Absence of the `doe` capability node entirely means the device does not expose an operating envelope at all.

## Why a distinct capability

An operating envelope is neither a measurement (`meter` is for what a device measures) nor a verdict on grid health (`grid`). It is a third class of signal — a control input communicated downstream — with a distinct audience (PCS subscribers, EMS panels, DERMS coordinators) and lifecycle (externally driven, possibly time-bounded). Its own capability keeps the streams separable on the subscriber side.

## Relationship to enforcement

Knowing an envelope and enforcing it are separate. A device that enforces one publishes its enforcement apart from the envelope it knows: on a distribution enclosure, `doe` carries the envelope (the full schedule, both directions), while `pcs/grid-import-limit` carries the single effective import limit the enclosure is currently enforcing (composed by `min()` with its other import limits). Export limiting is a DER-control concern (curtailing PV / BESS), separate from the import-limit composition; `doe/export-limit` carries the export *signal*. See [`distribution-enclosure.md`](../data-models/distribution-enclosure.md).

## Publishers

Any device that authoritatively knows an operating envelope: today, the utility meter (the utility's signal at the service point) and the distribution enclosure (the envelope it has obtained and is acting on), plus future publishers such as an IEEE 2030.5 / CSIP gateway, a DERMS adapter, or an aggregator's site controller. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [utility-meter](../data-models/utility-meter.md) and [distribution-enclosure](../data-models/distribution-enclosure.md) data models — publishers of this capability.
- [Electrification Bus `pcs`](../data-models/distribution-enclosure.md#pcs) — the enclosure's enforcement surface.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
