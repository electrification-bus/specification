# Electrification Bus Capability: shed

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-12
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.shed` — the settable controls that govern how a load-coordinating host (a distribution enclosure) sheds circuits to preserve backup runtime.

**Node type:** `energy.ebus.capability.shed`

This document is the canonical property catalog for the `shed` capability. Data-model documents that use it (today [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog.

## Overview

`shed` is the **write side** of a host's automatic load-shedding: the settable inputs to the one auto-shed engine that decides, moment to moment, which circuits stay powered while the site is off-grid. It is the sibling of the read-only [`shed-forecast`](shed-forecast.md) (which reports how long backup loads will last). Keeping the read-only computed values and the settable controls in separate capabilities keeps the two concerns clean and lets each grow additively (future shed controls: manual force-shed-now, configurable aggressiveness, scheduled policies).

Two settable inputs feed that engine, which is why they are one capability rather than two:

- **`asserted-islanding-state`** — a consumer's fallback assertion of the host's islanding-state, for the window in which the host cannot sense its own islanding-state.
- **`policy`** — the shedding algorithm the host runs and its tunable parameters, expressed as a self-describing JSON document so the model is not tied to any one algorithm.

## Properties

| Property ID | Datatype | Req | Settable | Description |
|---|---|---|---|---|
| `asserted-islanding-state` | enum | MAY | yes | Consumer-asserted islanding-state for the host's own island scope, consulted only while the host has lost or degraded communication with the device that senses that state (its MID / BESS). `$format = "NONE,ON_GRID,OFF_GRID"`; default `NONE`. See "Asserted islanding-state" below. |
| `policy` | json | MAY | SHOULD, when the host exposes runtime tuning | The host's shedding algorithm and its parameters: `{ "algorithm": <id>, "parameters": { … } }`. The parameter object's shape is advertised as a JSON Schema in the property's `$format`. See "Shed policy" below. |

## Asserted islanding-state

`asserted-islanding-state` is a **fallback**, not a routine control. A host decides whether to auto-shed from its *effective* islanding-state; normally that is what the host senses (`<mid>/grid/islanding-state`). But when the host loses communication with the device that senses islanding-state, it can no longer trust that value, and an outage is exactly when shedding matters most. This property lets a consumer assert the correct state for that window, so that a host whose sensed islanding-state has gone wrong or unreachable, and which cannot itself be reconfigured in time, can still be corrected by the consumer that acts on it.

The assertion is **scoped**: it overrides the effective islanding-state of the host's *own* premises-segment island (the scope it participates in and normally senses), not any global "islanded?" flag. This is consistent with the islanding model, in which each scope carries its own state rather than a single reconciled bit (see [`grid`](grid.md) and the [distribution-enclosure](../data-models/distribution-enclosure.md) islanding model).

A consumer asserts only `ON_GRID` or `OFF_GRID`; `NONE` is enclosure-authored (it is the default, and the value the host publishes when it clears an assertion on comm-restore). The Homie `$settable` attribute is statically `true`; the host enforces eligibility at write time.

**Effective islanding-state.** The islanding-state the host acts on is derived, not simply the sensed value. While communication with the sensing device (MID / BESS) is healthy the effective islanding-state is the sensed `<mid>/grid/islanding-state`, and any `asserted-islanding-state` is ignored. While communication is lost or degraded the effective islanding-state is the asserted value when one is in force (`ON_GRID` or `OFF_GRID`), or the last-known sensed value when the assertion is `NONE`. This lets a consumer correct a stale or wrong sensed state precisely in the window where the host can no longer trust its own sensing.

**Runtime acceptance rule.** A consumer write of `ON_GRID` or `OFF_GRID` is accepted only while the host has lost or degraded communication with the MID and/or BESS (observable from `connection/feeds-device-status` or `connection/fed-by-device-status` on whichever connection-owner references the BESS/MID being `LOST` or `DEGRADED`), regardless of the sensed grid-state (`ON_GRID`, `OFF_GRID`, or `UNKNOWN`). Once comm to the sensing device is lost the host can no longer trust its own islanding-state, so the consumer is permitted to assert either direction. Out-of-condition writes (those made while comm is healthy) are silently ignored: the published value does not change, which is how a consumer detects rejection. A consumer write of `NONE` is likewise ignored: `NONE` is host-authored, and a consumer does not clear an assertion; the host itself returns the property to `NONE` when it reclaims authority.

**Clearing and comm-restore.** The host clears an active assertion by publishing `NONE` as a normal retained value; it MUST NOT retract the topic with an empty retained payload, which would delete the retained state and make the property appear absent to late subscribers. Because `NONE` is a first-class `$format` value, the topic always carries a value. On comm-restore the host resumes following the sensed islanding-state and republishes `NONE`; to avoid prematurely clearing a still-needed assertion when a marginal link flaps, the host SHOULD apply hysteresis to the comm-health signal before treating communication as restored.

**Why static `settable: true` rather than dynamically-toggled.** The Homie 5 `$description` mutability rule restricts `$description` changes to `$state` transitions through `init` / `disconnected` / `lost`. Toggling `$settable` based on real-time eligibility would require cycling `$state` on every transition (and during any comm flapping): heavyweight and visible to consumers. Keeping `settable: true` static and enforcing eligibility at write time avoids this churn at the cost of one specific user-visible quirk: a naive write may be silently ignored. The single `$format` (`NONE,ON_GRID,OFF_GRID`) likewise advertises `NONE` as a settable value even though only the host authors it; that too is enforced at write time. A consumer computes eligibility client-side from the MID/BESS comm-status signals alone (a `LOST` or `DEGRADED` `feeds-device-status` / `fed-by-device-status` on the connection-owner referencing the BESS/MID), offers only `ON_GRID` and `OFF_GRID` as choices, and greys out the control otherwise.

## Shed policy

`policy` carries **which shedding algorithm the host runs and how it is tuned**, as one JSON object:

```json
{ "algorithm": "soc-priority.v1",
  "parameters": { "soc-threshold": 50 } }
```

- **`algorithm`** (string) is the algorithm's stable identifier and version, and is the **behavioral contract**. The JSON Schema in `$format` validates the *structure* of `parameters` (that `soc-threshold` is an integer 0–100); only the `algorithm` id conveys the *semantics* (what the algorithm does with that number, since two algorithms could share an identically-shaped parameter set yet behave oppositely). A consumer that recognizes the id knows the semantics and may read and tune the policy; one that does not recognize it treats the policy as opaque and read-only. Ids SHOULD be proposed upstream so the registry can track them and prevent collisions, exactly as shed-trigger enum values are.
- **`parameters`** (object) holds the algorithm's tunable values. Its shape is advertised by the JSON Schema in the property's `$format`, whose `$id` SHOULD equal the `algorithm` value.

The `json` datatype here is the deliberate escape hatch (framework design principle #10): a fixed scalar or enum cannot represent an open-ended family of algorithms whose parameter sets differ, so the value is a JSON document made self-describing by a JSON Schema. A simple host runs one well-known algorithm; a future host runs a different one, publishing a different `algorithm` id, a different `parameters` shape, and a different `$format` schema, with no change to this spec.

**Worked example: the SOC-priority scheme.** The baseline algorithm `soc-priority.v1` sheds each circuit according to its [`load-shed/priority`](load-shed.md) class: `OFF_GRID` circuits shed as soon as the site islands, `SOC_THRESHOLD` circuits shed once the host's aggregate BESS state of charge falls below `parameters.soc-threshold` (an integer percentage), and `NEVER` circuits are never auto-shed. Here the per-circuit `load-shed/priority` enum values are the **classes the algorithm operates on**, and `policy` names the algorithm and carries its one global knob. (Asserting `asserted-islanding-state = ON_GRID` during comm-loss makes the effective islanding-state on-grid and short-circuits every auto-shed path, including the SOC path.)

## Relationship to `load-shed`

`shed` (on the host) and [`load-shed`](load-shed.md) (on each circuit) are two halves of one scheme. `load-shed/priority` tags each circuit with its shed **class**; `shed/policy` names the **algorithm** that acts on those classes and carries its parameters. The classes a host's algorithm understands are advertised in each circuit's `load-shed/priority` `$format`; the algorithm and its tuning live here. Earlier revisions carried each trigger's tunable as its own companion scalar on the host (for example `shed/soc-threshold`); the `policy` document supersedes that convention, folding every algorithm parameter into one self-describing object.

## Absence semantics

Absence of the `shed` node means the host exposes no settable shed controls, typically because it coordinates no shedding (for a distribution enclosure, that no BESS is commissioned).

## Publishers

A host that coordinates automatic load-shedding across the circuits it serves: today a distribution enclosure, published only when at least one BESS is commissioned to it (the same presence rule as `shed-forecast`). The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md) — design principle #10 (scalars by default; `json` as the escape hatch).
- [Electrification Bus `shed-forecast` capability](shed-forecast.md) — the read-only sibling.
- [Electrification Bus `load-shed` capability](load-shed.md) — the per-circuit shed class the policy acts on.
- [distribution-enclosure](../data-models/distribution-enclosure.md) data model — the current publisher and its islanding model.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
