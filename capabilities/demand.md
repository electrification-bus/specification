# Electrification Bus Capability: demand

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.demand` — peak-average demand quantities for commercial demand-charge billing.

**Node type:** `energy.ebus.capability.demand`

This document is the canonical property catalog for the `demand` capability. Data-model documents that use it (today [`utility-meter.md`](../data-models/utility-meter.md)) reference this catalog.

## Overview

Demand is the time-averaged active power over a fixed integration window (the *demand interval*). Each closed interval yields a single number; the peak across a longer billing period (typically a calendar month) is the basis for a demand charge in many commercial tariffs. This capability publishes the interval demand and the running peak.

## Properties

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `integration-window` | integer | s | MAY | Demand integration interval length. Common values: `900` (15 min), `1800` (30 min), `3600` (1 hour). |
| `current-interval-demand` | float | W | MAY | Running average over the currently-open interval; resets at each interval boundary. |
| `previous-interval-demand` | float | W | MAY | Closed value of the most-recently-completed interval. |
| `peak-demand-this-period` | float | W | MAY | Highest `previous-interval-demand` observed since the most recent peak reset. |
| `peak-demand-time` | datetime | — | MAY | Timestamp (ISO-8601 UTC) of the interval that produced `peak-demand-this-period`. |
| `peak-demand-reset-time` | datetime | — | MAY | When `peak-demand-this-period` was last reset (typically the start of the current billing period). ISO-8601 UTC. |

The peak-reset semantics (billing-month versus rolling-30-day versus since-last-utility-read) are determined by the meter's configuration and are not constrained here; a consumer reading `peak-demand-this-period` should also read `peak-demand-reset-time` to know the window it covers. Reactive and apparent demand variants are not included in v0; they will be added additively if a real consumer requires them.

## Absence semantics

Absence of the `demand` node means the device does not compute interval demand.

## Publishers

A meter that computes interval demand: today the utility meter. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [utility-meter](../data-models/utility-meter.md) data model — the current publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
