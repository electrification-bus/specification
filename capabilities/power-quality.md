# Electrification Bus Capability: power-quality

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Identifier

`energy.ebus.capability.power-quality` — quantitative power-quality measurements (harmonic distortion and unbalance).

**Node type:** `energy.ebus.capability.power-quality`

This document is the canonical property catalog for the `power-quality` capability. Data-model documents that use it (today [`utility-meter.md`](../data-models/utility-meter.md)) reference this catalog.

## Overview

`power-quality` carries the summary power-quality figures a metering device computes: harmonic distortion and phase unbalance. It is the aggregate-figure tier, not the high-rate waveform tier (individual harmonic spectra and disturbance-event captures are out of scope).

## Properties

| Property ID pattern | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `thd-voltage-{a,b,c}` | float | % | MAY | Total Harmonic Distortion of voltage on the named phase, as a percentage of the fundamental. |
| `thd-current-{a,b,c}` | float | % | MAY | Total Harmonic Distortion of current on the named phase, as a percentage of the fundamental. |
| `tdd-current-{a,b,c}` | float | % | MAY | Total Demand Distortion of current on the named phase: like THD-current but normalized to the demand interval's peak current rather than the instantaneous fundamental. |
| `voltage-unbalance` | float | % | MAY | Voltage unbalance across phases (typically the NEMA definition: max deviation from the average, divided by the average). |

Higher-order harmonic spectra, individual harmonic magnitudes, and disturbance-event records (sags, swells, transient captures) are out of scope for v0; they begin to straddle the high-rate waveform tier this model excludes.

## Absence semantics

Absence of the `power-quality` node means the device does not compute power-quality figures.

## Publishers

A metering device that computes power-quality figures: today the utility meter. The property contracts above apply unchanged to any conformant publisher.

## References

- [Electrification Bus framework specification](../framework.md)
- [utility-meter](../data-models/utility-meter.md) data model — the current publisher.
- [Electrification Bus capability-type registry](../registries/capability-types.md).
