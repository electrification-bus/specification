# Electrification Bus Capability: price

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-10
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.price` — a dynamic price stream: the time-varying price of importing and exporting energy that a device authoritatively knows.

**Node type:** `energy.ebus.capability.price`

This document is the canonical property catalog for the `price` capability. Data-model documents that use it (for example [`utility-meter.md`](../data-models/utility-meter.md) and [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog and document only their device-specific role.

## Price versus tariff

This capability reports the **price** (the time-varying value), not the **tariff** (the rate plan / structure). The distinction is standard: a tariff is the full rate schedule (its time-of-use period definitions, tier thresholds, and energy / demand / fixed charges), while the price is the specific value in effect at a given moment, derived from that tariff. This mirrors Matter (a **Commodity Price** cluster for the value versus a **Commodity Tariff** cluster for the structure), IEEE 2030.5 (a `price` field within a `TariffProfile` structure), and the LF Energy split between [URPX](https://lfenergy.org/projects/utility-rate-plan-exchange-urpx/) (the rate-plan catalog) and a price server (the computed prices).

Modeling the rate structure itself is a genuinely hard problem and is **out of scope for eBus**: an eBus device publishes the price it is acting on, not the rate schedule that produced it. A consumer that needs the full rate plan should consult one of the dedicated efforts above (IEEE 2030.5 `TariffProfile`, Matter's Commodity Tariff cluster, or LF Energy URPX) directly. If eBus ever needs to carry structure, `tariff` is the natural name for it, but nothing here depends on that.

## Overview

The `price` capability carries a **dynamic price stream**: the price of importing (buying) and exporting (selling / feeding-in) energy, as a schedule of time-windowed prices. It covers time-of-use, real-time / market-indexed, and critical-peak pricing.

Like [`doe`](doe.md), it is **publish-only** and **publisher-agnostic**: per [framework principle #7](../framework.md#design-principles), any device that authoritatively knows a price signal publishes it. Two publishers are defined today:

- a **utility meter** — the utility's price at the service point (a source of the signal on eBus);
- a **distribution enclosure** — the price the enclosure (acting as the site EMS) has obtained and is coordinating to.

More than one may be present for a single site, and that is expected, not a conflict: they are **not competing authorities**, and a consumer reads whichever it needs and reconciles. How a device *obtains* its price — an AMI / IEEE 2030.5 pricing channel to a meter, a market feed or price server into an enclosure, or a subscription to another eBus `price` publisher — is a deployment and policy concern, not defined here.

Price is a *signal*, not a constraint: a subscriber responds economically (shift flexible load to cheaper windows, discharge storage into expensive ones) but is not bound by it. This is the "implicit demand response via dynamic price" mechanism, distinct from the hard limits of `doe` and the explicit events of `grid-event`; see [§Relationship to other signals](#relationship-to-other-signals).

## Standards

Aligned with **Matter's Commodity Price cluster** (`0x0095`): its `CurrentPrice` / `PriceForecast` attributes and the `CommodityPriceStruct` (a `Price` and a `PriceLevel` field) correspond directly to this capability's `price` and `price-level`. Aligned with the [IEEE 2030.5 / CSIP](https://standards.ieee.org/ieee/2030.5/5897/) Pricing function set (the `price` on a `ConsumptionTariffInterval`), and with the CTA-2045-B Price Stream message (opcode `0x0D`), which carries a relative price that maps to the `price-level` tier.

## Properties

The price schedule is carried as two `json` properties, one per direction (`import-price` and `export-price`), following [framework principle #10](../framework.md#design-principles) (`json` only for atomic compounds): a price, its currency, its tier, and its validity window are one object that must be read as a unit.

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `import-price` | json | — | MAY | no | The price to import (buy) energy: a JSON array of one or more price-window objects (schema below), ordered by `start-time`. Absent when no import price is signaled. |
| `export-price` | json | — | MAY | no | The price to export (feed-in / sell) energy, same schema. Absent when no export price is signaled. |

## Price-window object schema

Each property's value is a JSON **array** of price-window objects (the property carries a `$format` JSONSchema constraining it). A single current price is an array of one; a schedule of upcoming prices is a longer array. Each object:

```json
{
  "price":       0.42,                    // number, price per kWh in `currency`; MAY be negative; optional
  "currency":    "USD",                   // ISO 4217; required when `price` is present
  "price-level": "ON_PEAK",               // optional relative tier (enum)
  "source":      "SCHEDULED",             // optional enum; absent = UNKNOWN
  "start-time":  "2026-07-01T16:00:00Z",  // optional ISO-8601 UTC; absent = effective now
  "end-time":    "2026-07-01T20:00:00Z"   // optional ISO-8601 UTC; absent = until superseded
}
```

- **At least one** of `price` / `price-level` MUST be present; an object with neither is meaningless. A publisher with an absolute rate carries `price`; one carrying only a relative signal (a CTA-2045-B price byte) carries `price-level`; both may be present.
- `price`: the energy price for the window, per **kWh** (the billing convention, not per Wh), expressed in `currency`. It **MAY be negative** (negative / oversupply pricing is real, unlike the non-negative limits of `doe`). Corresponds to Matter `CommodityPriceStruct.Price`.
- `currency`: ISO 4217 code (e.g. `"USD"`, `"EUR"`). Required when `price` is present.
- `price-level`: the window's price **tier** relative to the schedule: `SUPER_OFF_PEAK`, `OFF_PEAK`, `MID_PEAK`, `ON_PEAK`, `CRITICAL_PEAK`, `UNKNOWN`. Advertised in `$format`; publishers MAY extend additively. This is what a consumer without a price-optimization model acts on ("is it peak?"); IEEE 2030.5 price tiers map directly, and a CTA-2045-B relative-price byte maps to the nearest tier. Corresponds to Matter `CommodityPriceStruct.PriceLevel`.
- `source`: the price's nature. `SCHEDULED` (a standing published schedule: time-of-use or fixed), `MARKET` (real-time / market-indexed), `EVENT` (a called critical-peak or dynamically-priced event), `UNKNOWN`. Absent means `UNKNOWN`. Orthogonal to `price-level`: a `SCHEDULED` time-of-use schedule still has `ON_PEAK` windows.
- `start-time` / `end-time`: ISO-8601 UTC. `start-time` absent means effective immediately; `end-time` absent means in force until superseded by a later publish.

## Selecting the effective price

The retained array is the publisher's complete current schedule for that direction, and each publish replaces it atomically. A subscriber determines the **effective** price as the array element whose `[start-time, end-time)` window contains the current time. If two windows overlap, the element with the latest `start-time` wins. If no element's window contains the current time, no price is currently signaled for that direction. Time-based selection needs a synced clock.

## Scheduling

Elements with a future `start-time` are pre-announced upcoming prices; a scheduling subscriber uses them to **pre-position** (for example, charge storage before an `ON_PEAK` / `CRITICAL_PEAK` window, or pre-cool before a high-price period). Unlike `doe`, price carries no safety asymmetry — mis-timing a price is an economic outcome, not a compliance breach — so a subscriber applies upcoming prices at its own discretion. Publishers SHOULD prune elements whose `end-time` is already in the past.

## Publish-only

This capability is publish-only; no `/set` topic is defined. The price source is configured out of band (an AMI / IEEE 2030.5 pricing channel to a meter, a market feed or price server to an enclosure); the publisher publishes the resulting values, and subscribers read them and respond locally. No subscriber needs write permission to any `price` property.

## Absence semantics

Absence of `import-price` (respectively `export-price`) means no price is signaled in that direction. An empty array is equivalent to absence. Absence of the `price` capability node entirely means the device does not expose a dynamic price stream. `price` carries the *energy* price only; **demand charges** (currency per kW of peak) are a separate billing dimension and are not carried here.

## Why a distinct capability

A price is neither a measurement (`meter`), an operating limit (`doe`), nor a verdict on grid health (`grid`). It is an economic signal that drives *voluntary* response, with its own audience (EMS panels, price-aware controllers) and lifecycle. Its own capability keeps it separable from the hard constraints a subscriber must obey.

## Relationship to other signals

Three utility-facing signals compose the site's coordination inputs, and a subscriber treats them differently:

- **`price`** — an *incentive*. The site responds economically (implicit demand response) but is free not to.
- **[`doe`](doe.md)** — a *limit*. The site MUST remain within the operating envelope.
- **[`grid-event`](grid-event.md)** — an *explicit event*. A discrete, time-bounded grid ask or directive (shed / load-up / conserve), with a severity and its own lifecycle.

An enclosure acting as the site EMS reads all three and coordinates its DER children accordingly.

## Publishers

Any device that authoritatively knows a price signal: today, the utility meter (the utility's price at the service point) and the distribution enclosure (the price it is coordinating to), plus future publishers such as an IEEE 2030.5 / CSIP gateway or a market-price / price-server adapter. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `doe` capability](doe.md) — the operating-limit sibling signal.
- [utility-meter](../data-models/utility-meter.md) and [distribution-enclosure](../data-models/distribution-enclosure.md) data models — publishers of this capability.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
