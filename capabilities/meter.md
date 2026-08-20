# Electrification Bus Capability: meter

**Status:** DRAFT
**Version:** 0.4
**Date:** 2026-08-20
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.meter` — electrical measurements: instantaneous power, voltage, current, and cumulative energy.

**Node type:** `energy.ebus.capability.meter`

This document is the canonical property catalog for the `meter` capability. Data-model documents that use it reference this catalog and document only what is device-specific (the reference direction of `active-power`, which subset the device type typically publishes, and any device-specific notes), rather than restating the properties.

## Overview

The `meter` capability carries electrical measurements at a point in the system: instantaneous power (active, reactive, apparent), voltage, current, frequency, power factor, and cumulative energy. It is the most widely reused capability in eBus. The same node type appears on the distribution enclosure (service-entrance aggregate), on circuits and feed lugs (branch and feed metering), on the utility meter (revenue metering), on a BESS (its external AC boundary), on PV and EVSE proxies, on a water heater (its own draw), and on behind-the-meter sub-meters (published on their host circuit or lugs device). What differs between devices is the *subset* published and the *reference direction* of `active-power`, not the vocabulary.

Every property in this catalog is MAY. None is constitutive of `meter`: a metering point is worth publishing even when a single register is all a publisher has. Publishers populate what they measure and omit the rest; consumers tolerate sparse publication and read the device's `$description` for the authoritative property set. A device model documents the reference direction of `active-power`, which subset is worth publishing on that device type, and any device-specific notes; it does not raise these levels to MUST (see [Conformance Latitude](../framework.md#conformance-latitude)).

## Per-conductor representation

Per-conductor measurements use property-name **suffixes**: `-a` / `-b` / `-c` for the phase positions and `-n` for the neutral. System-level aggregates and single-point measurements carry no suffix: `active-power` (not `active-power-system`), and a single-conductor meter's bare `voltage` / `current`. The suffixes are for a meter with more than one measured conductor: a US split-phase service populates `-a` and `-b`, and a three-phase service `-a` / `-b` / `-c`. A single measured conductor never takes `-a` alone (there is no `-a` without a `-b`); it uses the bare property.

In US residential split-phase wiring the two hot legs are commonly labelled **L1** and **L2** by electricians and on panel schedules; these correspond directly to `-a` and `-b`. eBus uses the `-a` / `-b` / `-c` / `-n` suffix as its single per-conductor convention because it generalises to three-phase and names a neutral position; the equivalent `l1-` / `l2-` prefix spelling that appeared on some earlier device drafts is not used.

## Properties

### System-level (no suffix)

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | MAY | Total active power. Sign per the reference-direction rule below. |
| `reactive-power` | float | var | MAY | Total reactive power. |
| `apparent-power` | float | VA | MAY | Total apparent power. |
| `power-factor` | float | — | MAY | System power factor, signed: positive = lagging (inductive), negative = leading (capacitive); range `[-1.0, 1.0]`. |
| `frequency` | float | Hz | MAY | Line frequency. |
| `voltage` | float | V | MAY | RMS voltage at a single-point meter (one measured conductor, e.g. a branch circuit or a device's single AC boundary). A split-phase or three-phase meter uses the per-conductor `voltage-{a,b,c}` instead. |
| `current` | float | A | MAY | RMS current at a single-point meter (one measured conductor). A split-phase or three-phase meter uses the per-conductor `current-{a,b,c,n}` instead. |
| `imported-energy` | float | Wh | MAY | Cumulative active energy imported: the energy counterpart of positive `active-power` (into the metered device / consumption in the default frame; which register accrues follows the reference-direction rule below). Monotonically non-decreasing. |
| `exported-energy` | float | Wh | MAY | Cumulative active energy exported: the energy counterpart of negative `active-power` (out of the metered device / production or backfeed in the default frame; which register accrues follows the reference-direction rule below). Monotonically non-decreasing. |
| `imported-reactive-energy` | float | varh | MAY | Cumulative reactive energy imported. |
| `exported-reactive-energy` | float | varh | MAY | Cumulative reactive energy exported. |
| `apparent-energy-imported` | float | VAh | MAY | Cumulative apparent energy imported. |
| `apparent-energy-exported` | float | VAh | MAY | Cumulative apparent energy exported. |
| `shared-with-device-ids` | string | — | MAY | Comma-separated Homie device IDs of the other devices this meter's hardware also measures. Omitted when it measures only this device. See §"Shared metering hardware". |

### Per-conductor (suffix `-a` / `-b` / `-c`, and `-n` for the neutral where present)

| Property ID pattern | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `voltage-{a,b,c}` | float | V | MAY | RMS voltage on the named phase, line-to-neutral (or line-to-virtual-neutral on a delta service). |
| `current-{a,b,c,n}` | float | A | MAY | RMS current on the named conductor. Neutral current (`current-n`) may be measured or imputed. |
| `active-power-{a,b,c}` | float | W | MAY | Per-phase active power. Sign matches the system `active-power`. |
| `reactive-power-{a,b,c}` | float | var | MAY | Per-phase reactive power. |
| `apparent-power-{a,b,c}` | float | VA | MAY | Per-phase apparent power. |
| `power-factor-{a,b,c}` | float | — | MAY | Per-phase power factor, signed as for the system value. |
| `voltage-angle-{a,b,c}` | float | ° | MAY | Voltage angle relative to phase-A voltage (`voltage-angle-a` = `0`). |
| `current-angle-{a,b,c}` | float | ° | MAY | Current angle relative to the same-phase voltage. |
| `imported-energy-{a,b,c}` | float | Wh | MAY | Per-conductor cumulative imported energy. |
| `exported-energy-{a,b,c}` | float | Wh | MAY | Per-conductor cumulative exported energy. |

## Sign convention (reference direction)

The default reference direction is **positive = imported**: `active-power` and `imported-energy` are positive when power flows *into* the metered device or load (consumption, or import from the grid); `exported-energy`, and negative `active-power`, are the reverse. This matches the utility meter, feed lugs, EVSE, and water heaters.

A **circuit**'s reference direction is set by its host, not fixed here. A circuit **hosted in a distribution enclosure** is metered at the enclosure's branch terminal and uses the enclosure's reference direction: positive `active-power` is power flowing from the circuit *into the enclosure busbar*, so a consuming load reads negative `active-power` and accumulates `exported-energy` (enclosure-to-circuit delivery), while a backfeeding circuit (for example a PV inverter on that breaker) reads positive `active-power` and accumulates `imported-energy`; see [`devices/distribution-enclosure.md`](../devices/distribution-enclosure.md). A **standalone or instrument** circuit (a self-publishing smart breaker, a proxied submeter, an eGauge/EKM point) has no enclosure busbar to reference and uses the default above (positive = consumption into the conductor).

Device models whose natural reference is power flowing *out* invert the default and state so explicitly: a **BESS** publishes `active-power` positive when discharging (out of the device), a **PV** proxy positive when producing, and an **outlet** or **PDU** output positive when delivering to the connected load. A consumer reads the device's model to know the reference direction; the sign is never ambiguous within a given device type.

## Shared metering hardware

One current transformer can measure several devices at once: a multi-circuit breaker occupies a single position and protects several branch circuits through one sensor. The reading is real, but it covers the group rather than any one member, and attachment alone cannot say so (see [`framework.md`](../framework.md#capability-coverage-and-shared-hardware) for the declaration and its symmetry requirement).

A publisher in that position MAY omit `meter` on the affected devices, which is truthful and self-describing. A publisher that instead publishes the reading on each member MUST declare the group with `shared-with-device-ids`.

**The values then describe the whole group, not each member's share, so a consumer MUST NOT aggregate them across members of that group.** Summing `active-power` over three circuits behind one sensor reports three times the real load. The same applies to the energy registers: they accumulate the group's flow once, not once per member. A consumer totalling a site counts each shared group a single time.

## Encoding notes

Properties use the engineering-unit values listed (no scaling factor or `µ-` prefix). Unit strings follow the IEC 80000-6 symbols: apparent power/energy are `VA` / `VAh`, and reactive power/energy are the lowercase `var` / `varh` (the standardized symbol; not `VAR`), matching the Homie convention's SI-symbol casing. Cumulative energy quantities are floats in Wh / varh / VAh, sufficient for billing-grade energy from a Homie float property; a publisher whose internal representation is integer micro-Wh converts at publish time.

## Forward compatibility

The full 4-quadrant per-phase and system VA matrix (Q1-Q4 by delivered/received, fundamental-only or with-harmonics, arithmetic and vectorial flavors) is not defined here; it can be added additively later when a consumer needs it, without renaming existing properties. Meter-configuration and nameplate metadata (accuracy class, CT/PT ratio, calculation convention, register multiplier, neutral-connected) live on the metering device's `info`, not on `meter`; see [`utility-meter.md`](../devices/utility-meter.md).

## Absence semantics

Absence of the `meter` node means the device is not metered at that point, or the publisher does not expose measurements. Absence of an individual property is the usual "not measured / not reported"; publishers populate the registers they have.

## Publishers

Published by any device that reports electrical measurements: the distribution enclosure (service-entrance aggregate), circuits and feed lugs, the utility meter, a BESS (external AC boundary), PV and EVSE proxies, water heaters, and behind-the-meter sub-meters (on their host circuit or lugs device).

## References

- [Electrification Bus framework specification](../framework.md)
- [circuit](../devices/circuit.md), [distribution-enclosure](../devices/distribution-enclosure.md), [utility-meter](../devices/utility-meter.md), and [BESS](../devices/bess.md) data models — publishers of this capability.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
