# Electrification Bus Capability: pcs

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.pcs` — a Power Control System (UL 3141): the premises-equipment import protection (Firm Service Rating), and the arbitration that reconciles every active import constraint to a single enforced current limit.

**Node type:** `energy.ebus.capability.pcs`

This document is the canonical property catalog for the `pcs` capability. Data-model documents that use it ([`distribution-enclosure.md`](../data-models/distribution-enclosure.md), and the per-circuit participation in [`circuit.md`](../data-models/circuit.md)) reference this catalog.

## Overview

A `pcs` is the enclosure's import current limiter. It has one physical actuator (it sheds or throttles load to cap import current), and two roles:

1. **Premises-equipment protection (the Firm Service Rating, FSR):** a firm, always-on, amps-native limit reflecting the incoming feed / service capacity (busbar, conductor, service). This is the UL 3141 PCS archetype.
2. **The arbitrator:** it reconciles *every* active import constraint to an equivalent current limit and enforces the **most restrictive** (`min()`), and publishes the effective limit and which constraint is binding.

Crucially, the constraints come from **different regimes in different native units, and each lives in its own capability**:

- the **FSR** and the other amps-native operational limits (`feed-import-limit`, `off-grid-import-limit`, `requested-import-limit`) live **here**, in amps;
- the dynamic grid operating envelope lives on [`doe`](doe.md), in **watts** (IEEE 2030.5);
- the voltage-support reduction lives on [`voltage-response`](voltage-response.md), in **volts** (ANSI C84.1).

`pcs` does **not** re-publish `doe` or `voltage-response` as amps copies. Each constraint stays in its native unit on its own capability; the enclosure controller reconciles them to a current limit (`watts → amps` via `I = P / (V·pf)`; the voltage loop outputs a current trim directly) and enforces the `min()`. What `pcs` publishes is the **result**: the effective `import-limit` and the `binding-constraint`.

## The constraint classes and the failsafe structure

The three protection classes differ in lifecycle, and that difference is a **failsafe requirement**, not a detail:

- **FSR** (`feed-import-limit`) is a **standing, always-on** premises floor. It cannot be lost.
- **Voltage support** ([`voltage-response`](voltage-response.md)) is a **standing, always-on** transformer baseline (a local setpoint with no external dependency).
- The **grid envelope** ([`doe`](doe.md)) is **time-bounded and externally provided**: present only while an envelope is in effect, and absent between envelopes or when the signalling channel is unreachable.

Therefore, **when no `doe` is active, transformer protection lapses to the always-on FSR + voltage-support baseline, and import is never reverted to unlimited.** The voltage-support baseline is what provides continuous transformer protection beneath the intermittent, coordinated grid envelope.

## Standards

Aligned with [UL 3141](https://www.shopulstandards.com/ProductDetail.aspx?productId=UL3141) / NEC 2026 Article 130, which define the Power Control System and the Power Import Limit (PIL) / Power Export Limit (PEL) vocabulary. The dynamic grid envelope it reconciles is an [IEEE 2030.5 / CSIP](https://standards.ieee.org/ieee/2030.5/5897/) Dynamic Operating Envelope, carried in watts on [`doe`](doe.md). Export limiting is a DER-control concern (curtailing PV / BESS), not an import-limit slot; the export envelope lives on `doe/export-limit`.

## Properties

### System (the enclosure running the PCS)

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `enabled` | boolean | — | SHOULD | Is the PCS enabled on this enclosure? |
| `active` | boolean | — | SHOULD | Is the PCS actively limiting import right now? |
| `import-limit` | float | A | SHOULD | The **effective** enforced import limit: the `min()` across all active constraints reconciled to amps (the amps-native limits below, plus the reconciled `doe` and `voltage-response`). |
| `binding-constraint` | enum | — | SHOULD | Which constraint class currently sets `import-limit`: `FSR`, `DOE`, `VOLTAGE`, `OFF_GRID`, `REQUESTED`, `NONE`, `UNKNOWN`. The provenance of the enforced limit; publishers MAY extend via `$format`. |
| `feed-import-limit` | float | A | SHOULD | The **FSR**: commissioned firm feed / service capacity (premises-equipment protection), set at install. The always-on floor. May be less than the main-breaker rating when the upstream feed conductor is smaller (e.g. a 200 A panel on a 100 A service feed publishes `feed-import-limit = 100`). |
| `feed-import-limit-enablement` | enum | — | SHOULD | `UNSPECIFIED`, `UNCONFIGURED`, `DISABLED`, `ENABLED`. |
| `off-grid-import-limit` | float | A | MAY | Import cap when islanded (from BESS / DER). |
| `off-grid-import-limit-enablement` | enum | — | MAY | Same domain. |
| `requested-import-limit` | float | A | MAY | User- or operator-requested temporary limit (a homeowner via mobile app; a fleet operator via REST). Distinct from the utility grid envelope, which lives on `doe`. |
| `requested-import-limit-enablement` | enum | — | MAY | Same domain. |

The main breaker rating is **not** carried here: it is a `breaker` property (`breaker/rating`) on the device's [`breaker`](breaker.md) capability, and is a further hard ceiling the `min()` respects.

### Participation (a circuit under the PCS)

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `managed` | boolean | MAY | Is this circuit managed by the host's PCS? |
| `priority` | integer | MAY | PCS priority ranking, consulted when an active import limit is binding (which circuits shed first). |

## Publisher qualification

- A **distribution enclosure** publishes the *system* surface (state, the effective `import-limit`, `binding-constraint`, and the amps-native limits) — it runs the PCS and does the arbitration.
- A **circuit** publishes only its *participation* (`managed`, `priority`).

## Relationship to `load-shed` and `switch`

`pcs` and [`load-shed`](load-shed.md) are both policies that act on a circuit's relay, so they are meaningful only on a circuit that also publishes a controllable [`switch`](switch.md); they correspond to the `PCS` and `LOAD_SHED` values of `switch/relay-requester`. They are distinct concerns: a PCS limits site import/export to a binding limit; load-shed preserves backup runtime. A circuit may participate in one, both, or neither.

## Absence semantics

Absence of the `pcs` node means the device does not run (or participate in) a Power Control System.

## Publishers

Any device that runs a Power Control System (today the distribution enclosure) or participates in one (a circuit). The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `doe` capability](doe.md) (the watts grid envelope) and [`voltage-response`](voltage-response.md) (the volts baseline) — the native-unit constraints `pcs` reconciles and reports as `binding-constraint`.
- [Electrification Bus `breaker` capability](breaker.md) — where the main-breaker rating lives.
- [distribution-enclosure](../data-models/distribution-enclosure.md) and [circuit](../data-models/circuit.md) data models — the publishers.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
