# Electrification Bus Capability: grid-event

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-10
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.grid-event` — a schedule of grid-originated events the site is asked to respond to: demand-response asks (shed / load-up) and grid-condition alerts (conservation calls, critical-peak, grid emergencies), each with a severity, a voluntary-versus-mandatory flag, and a lifecycle.

**Node type:** `energy.ebus.capability.grid-event`

This document is the canonical property catalog for the `grid-event` capability. Data-model documents that use it (today [`distribution-enclosure.md`](../data-models/distribution-enclosure.md)) reference this catalog and document only their device-specific role.

## Overview

The `grid-event` capability carries the schedule of discrete **grid events** a site is asked to act on. It spans a family that real deployments treat as one thing:

- a **demand-response ask** to shed (curtail) or load-up (absorb) energy over a window;
- a **conservation alert** (a voluntary "please reduce" call, such as a CAISO Flex Alert);
- a **grid emergency** (a mandatory curtailment order, such as a CTA-2045-B Grid Emergency or a CAISO EEA stage);
- a **critical-peak event** (a heightened-urgency shed window).

These differ only in *direction*, *severity*, and *whether they are binding*, so they are one capability with those as fields, not four capabilities. A pure "shed 2 kW" DR command and a statewide "please conserve" alert are the same shape: a grid asking the site to change behavior over a time window.

Like [`price`](price.md) and [`doe`](doe.md), `grid-event` is **publish-only** and **publisher-agnostic**: per [framework principle #7](../framework.md#design-principles), any device that authoritatively receives grid events publishes them. The primary publisher is a **distribution enclosure** acting as the site EMS, which receives events out of band (typically an OpenADR 3 VEN or an IEEE 2030.5 DRLC client) and republishes them on the bus so consumers and DER children can see the ask. A utility meter or a dedicated OpenADR / 2030.5 gateway MAY publish it equally.

A grid event is a *signal*: it says what the grid is asking, not what any one device must physically do. How the site responds is a separate concern: an EMS decomposes the event and drives its flexible loads through their own device-level [`flex`](flex.md) control surface, and compliance is reported through `settlement-proof`. See [§Relationship to other signals](#relationship-to-other-signals).

**Geographic targeting is resolved upstream.** A grid event on eBus already applies to this site: the publisher (or the OpenADR VTN / price server feeding it) has done the region-to-site resolution before the event reaches the bus. `grid-event` carries no region field.

## Standards

Aligned with the **OpenADR 3** Program / Event model (a VTN publishes Events to VENs; the SIMPLE payload's 0-3 levels map to `severity`) and the **IEEE 2030.5 / CSIP** Demand Response Load Control function set (`DemandResponseProgram` / `EndDeviceControl`, whose `EventStatus` maps to `state`). The severity and voluntary-versus-mandatory framing follows **CTA-2045-B** Basic DR (Shed, Critical Peak, Grid Emergency, Load Up) and the CAISO alert hierarchy (Flex Alert → EEA Watch / 1 / 2 / 3). Matter deliberately does **not** model the grid event: its Device Energy Management cluster note states grid services "will use other protocols (OpenADR / IEEE 2030.5) ... outside the scope of Matter," and only models the device-side response (the analog of eBus [`flex`](flex.md)). `grid-event` is the local, bus-visible representation of the event those protocols deliver.

## Properties

The event schedule is carried as one `json` property, `events`, following [framework principle #10](../framework.md#design-principles) (`json` only for atomic compounds): an event's direction, severity, binding status, and window are one object that must be read as a unit.

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `events` | json | — | MAY | no | The current schedule of grid events: a JSON array of one or more event objects (schema below), ordered by `start-time`. Absent, or an empty array, when no events are signaled. |

Unlike [`price`](price.md) and [`doe`](doe.md), there is no import / export split: an event's direction is carried in its `mode` field, not in separate per-direction properties.

## Event object schema

Each element of `events` is an event object (the property carries a `$format` JSONSchema constraining it):

```json
{
  "event-id":   "fa-2026-0905-001",              // stable identity across the event's lifecycle
  "mode":       "SHED",                          // direction; required. SHED | LOAD_UP | NORMAL
  "severity":   "CONSERVATION",                  // optional ordered tier (enum)
  "voluntary":  true,                            // optional: true = request, false = directive
  "level":      0-100,                           // optional %: magnitude of the ask
  "state":      "ACTIVE",                        // optional lifecycle state (enum)
  "source":     "ISO",                           // optional origin (enum)
  "title":      "Flex Alert for Sept 5",         // optional human-readable label
  "start-time": "2026-09-05T23:00:00Z",          // optional ISO-8601 UTC; absent = effective now
  "end-time":   "2026-09-06T05:00:00Z"           // optional ISO-8601 UTC; absent = until superseded
}
```

- `event-id`: a stable identifier for the event, constant across its whole lifecycle (from pre-announcement through cancellation or completion). Required. A `settlement-proof` receipt, or a device's response, references this id. It is the one field a subscriber uses to recognize "the same event" across successive publishes.
- `mode`: the direction of the ask, reused from the device-level [`flex`](flex.md) vocabulary. `SHED` asks the site to reduce net consumption (curtail load or discharge storage); `LOAD_UP` asks it to increase net consumption (absorb surplus / cheap energy); `NORMAL` is an all-clear that ends an event. Required.
- `severity`: the event's tier, as an **ordered** enum from least to most urgent: `CONSERVATION` (a voluntary reduce call: Flex Alert, OpenADR SIMPLE moderate), `CRITICAL_PEAK` (a heightened-urgency shed window), `GRID_EMERGENCY` (a grid-emergency / mandatory curtailment: CTA-2045-B Grid Emergency, CAISO EEA), `UNKNOWN`. Advertised in `$format`; publishers MAY extend additively. A subscriber without a full model uses this to rank competing events.
- `voluntary`: whether participation is at the site's discretion. `true` = a request the site may decline; `false` = a directive (mandatory curtailment). Carried separately from `severity` because the two are independent: a CAISO EEA Watch is an early-warning tier that is still voluntary, while an EEA 1 at a similar stage is not. Absent means unknown; a subscriber SHOULD treat an unknown-binding event as voluntary unless `severity` is `GRID_EMERGENCY`.
- `level`: the magnitude of the ask as a percentage (for events that quantify one), reused from `flex`. Absent for an unquantified alert (a conservation call carries no percentage).
- `state`: the event's lifecycle position: `SCHEDULED` (announced, not yet started), `ACTIVE` (in force now), `COMPLETED` (ended normally), `CANCELLED` (called off, including a pre-announced event cancelled before it started), `SUPERSEDED` (replaced by a newer event for the same window). `CANCELLED` is the one transition a bare start / end schedule cannot express, which is why the state is explicit. Absent: infer `ACTIVE` if the current time is within the window, `SCHEDULED` if before it. Follows IEEE 2030.5 `EventStatus`.
- `source`: the event's origin: `ISO` (a balancing authority / grid operator), `UTILITY`, `AGGREGATOR` (a DR / VPP aggregator), `MARKET`, `UNKNOWN`. Absent means `UNKNOWN`.
- `title`: an optional human-readable label for display; carries no machine semantics (the machine-actionable fields are the others).
- `start-time` / `end-time`: ISO-8601 UTC. `start-time` absent means effective immediately; `end-time` absent means in force until superseded or cancelled.

## Selecting the effective event(s)

The retained array is the publisher's complete current view, replaced atomically on each publish. A subscriber treats as **in force** every element whose `state` is `ACTIVE` (or whose window contains the current time when `state` is absent), and as **upcoming** every element that is `SCHEDULED` (or window-future). `COMPLETED` / `CANCELLED` / `SUPERSEDED` elements are retained briefly for transition visibility, then pruned by the publisher.

More than one event MAY be in force at once (for example a standing conservation alert overlapping a called shed event). When in-force events **conflict in direction** (a `SHED` and a `LOAD_UP` overlapping), the subscriber follows the more urgent one: a non-`voluntary` event outranks a voluntary one, and failing that the higher `severity` wins. This is a conservative default; an EMS with its own optimization policy MAY resolve differently. Time-based evaluation needs a synced clock.

## Scheduling and lifecycle

Elements that are `SCHEDULED` (future `start-time`) are pre-announced events; a scheduling subscriber uses them to **pre-position** (pre-cool before a shed window, top up storage before a critical-peak, plan to absorb during a load-up). Because an event carries a stable `event-id` and an explicit `state`, a pre-announced event can later be published with `state = CANCELLED` (called off) or `SUPERSEDED` (rescheduled) under the same `event-id`, so a subscriber that pre-positioned can unwind. Publishers SHOULD retain a terminal-state event (`COMPLETED` / `CANCELLED` / `SUPERSEDED`) only long enough for subscribers to observe the transition, then drop it. `grid-event` is a live signal, not an archive; a consumer needing event history obtains it out of band.

## Publish-only

This capability is publish-only; no `/set` topic is defined. The event source is configured out of band (an OpenADR 3 VEN registration, an IEEE 2030.5 DRLC client, a price-server subscription); the publisher republishes the events it receives, and subscribers read them and respond locally. No subscriber needs write permission to any `grid-event` property.

## Absence semantics

Absence of `events`, or an empty array, means no grid event is currently signaled (the common steady state: grid emergencies and conservation calls are rare). Absence of the `grid-event` capability node entirely means the device does not expose a grid-event feed at all. Absence is the all-clear; a subscriber returns to its normal (price- and doe-guided) operation.

## Why a distinct capability

A grid event is neither a price ([`price`](price.md), an economic incentive), an operating limit ([`doe`](doe.md), a hard bound), nor a measurement ([`meter`](meter.md)). It is a discrete, time-bounded *ask or directive* from the grid, with a lifecycle (announced, active, cancelled) and a severity that a subscriber weighs against the other signals. Its own capability keeps that discrete, stateful event stream separate from the continuous signals around it.

## Relationship to other signals

The site-level signals compose the site's coordination inputs, and a subscriber treats each differently:

- **`grid-event`** — an *explicit event*. A discrete, time-bounded ask or directive (shed / load-up / conserve) with a severity and a voluntary-versus-mandatory flag.
- **[`price`](price.md)** — an *incentive*. Continuous economic signal; the site responds economically but is free not to.
- **[`doe`](doe.md)** — a *limit*. Continuous operating envelope the site MUST stay within.

The response side lives elsewhere: an EMS decomposes a `grid-event` and drives each flexible load through its device-level [`flex`](flex.md) control surface (settable `flex/request`, with the load reporting `flex/response` and `flex/opt-out`), and site-aggregate compliance is emitted as `settlement-proof`. `grid-event` (the site-wide ask) and `flex` (the per-load control + feedback) are the two ends of demand response; this capability is the ask, not the doing.

A continuous grid **carbon-intensity** signal (gCO2e/kWh, as in Matter's Electrical Grid Conditions cluster or SGIP MOER) is a *price*-like continuous signal, not an event, and is out of scope here; if eBus carries it later it is a sibling to `price`, not part of `grid-event`.

## Publishers

Any device that authoritatively receives grid events: today the distribution enclosure (as site EMS), and equally a utility meter or a dedicated OpenADR 3 / IEEE 2030.5 gateway that republishes an operator's events. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus `price` capability](price.md) and [`doe` capability](doe.md) — the continuous-signal siblings.
- [water-heater](../data-models/water-heater.md) data model — defines the device-level `flex` control + feedback surface that acts on these events.
- [distribution-enclosure](../data-models/distribution-enclosure.md) data model — the primary publisher of this capability.
- [Electrification Bus capability-type registry](../registries/capability-types.md) — the index this catalog is referenced from.
