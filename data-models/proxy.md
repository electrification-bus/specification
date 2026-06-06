# eBus Proxy Model

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-05-22
**Authors:** Don Jackson

This document defines how eBus handles **proxying** — the publication of an eBus representation of a device by some publisher other than the device itself. Proxying is the bridge that lets the eBus ecosystem cover devices that are not yet eBus-native: an enclosure, gateway, or integration hub publishes the eBus tree for a non-eBus-native device, populated from vendor APIs, internal integrations, or commissioning data, until the device (or its vendor) becomes eBus-native and takes over publication itself.

Proxying is a first-class peer to native publishing (see [Design Principle 6 in data-models/README.md](README.md#design-principles)). This document specifies the consumer-facing surface for distinguishing proxied from native representations, the device-ID convention for proxied devices, and where proxy-side knowledge lives in the data model. It applies uniformly to every eBus data model whose devices may be proxied (BESS, PV, EVSE, MID, future device classes).

The long-term home for this content is the [eBus framework spec](../../../tree/wip/framework). Until that document matures, this file is the canonical reference for proxy conventions across all eBus data models.

## Proxy Model

Some devices do not yet represent themselves on eBus. An early-adopter publisher (typically an enclosure, gateway, or integration hub) **proxies** these devices — it publishes child devices on their behalf, populated from internal data sources (vendor APIs, internal integrations, commissioning data).

When a device becomes available on eBus — either through a vendor adapter or natively — the proxy SHOULD stop publishing that device, leaving the eBus-native publisher as the sole representation. Determining when to proxy is publisher-implementation-specific; commissioning configuration is the typical source.

During an adoption transition, both publishers may coexist (e.g., an enclosure proxies a Tesla Powerwall today; Tesla someday begins publishing the same Powerwall natively, and the enclosure publisher has not yet detected the new publisher and stopped proxying). This is expected and the data model accommodates it — see §"Disambiguating proxied from native publishers" below for how consumers identify and prefer the native representation. The proxy-suppression behavior above is an optimization to keep the eBus tree clean; it is not a hard contract guarantee against duplication.

Consumers identify all devices by the same `$description.type` regardless of whether the device is being proxied or self-representing. The distinction is transparent to consumers.

## Disambiguating proxied from native publishers

Typically a given physical device is published by exactly one publisher — either the vendor's own native publisher or a proxy — and consumers see one representation. During an adoption transition, it is possible for both publishers to coexist and present the consumer with two representations of the same physical device. eBus offers two mechanisms for consumers to disambiguate.

**Implicit, via the Homie `root` reference and the root device's `$description.type` (primary mechanism).** Every Homie child device declares its `root`. A consumer that finds two devices with the same `info/serial-number` can determine which is which by inspecting the type of each one's root device:

- If the root device's `$description.type` matches the device's own type — i.e., the device is its own root — this representation is the device publishing itself natively. (Equivalently: the device's `root` field is its own ID, or absent per Homie 5's convention for top-level devices.) The vendor identity is in the device's `info/vendor-name`.
- If the root device's `$description.type` is anything other than the device's own type (e.g., the root is `energy.ebus.device.distribution-enclosure` when the proxier is an enclosure), this representation is being proxied by that root device. The root's `info/vendor-name` identifies the proxy publisher.

For example: a BESS device whose root has type `energy.ebus.device.bess` is publishing itself natively; one whose root has type `energy.ebus.device.distribution-enclosure` is being proxied by that enclosure.

Per the eBus vendor-neutrality principle, vendors publishing devices natively use the same type identifier as proxies — vendor identity lives in `info/vendor-name`, not in the device type string. The general heuristic is "prefer the native (vendor-published) representation over a proxied one." This works without any new property: every Homie 5 device already publishes `root`, and the consumer just inspects the root's existing `$description.type`.

**Explicit, via an optional `proxied` boolean (secondary mechanism).** A publisher MAY publish a `proxied` boolean property on a device's `info` for direct disambiguation:

- `proxied = true` — this representation is proxied.
- `proxied = false` — this representation is published natively (by the device or its vendor).
- absent — no explicit signal; consumers fall back to the implicit-via-root mechanism above.

`proxied` is MAY-level. The property is reserved here so that any publisher that wants to make the distinction unambiguous has a defined slot to use, rather than inventing its own ad-hoc property if and when the need arises.

## Proxy-side knowledge stays on the proxy

Information that a non-proxying eBus-native publisher of the proxied device could not have lives on the proxier's surfaces, not on the proxied child. This is a direct application of [Design Principle 7 in data-models/README.md](README.md#design-principles) ("Properties belong on the device that authoritatively knows them"): the property contract for the proxied device must be satisfiable by *any* conformant publisher — native or proxy — so any property that only the proxier can populate belongs on the proxier, not on the device being proxied.

Typical categories of proxy-side knowledge include:

- **The wiring or physical relationship between the proxied device and the proxier** — recorded on the proxier's connection records, not on the proxied child.
- **The proxier's view of communication-link health to the proxied device** — recorded on the proxier's surfaces, not on the proxied child. (This is distinct from the proxied device's own self-reported communication status, which a native publisher would also publish.)

Data-model documents for specific proxier classes (e.g., the [distribution-enclosure spec](distribution-enclosure.md)) enumerate exactly which capabilities own which proxy-side facts in that data model.

## Proxied-device ID convention

Every proxied device is named `{proxier-id}-{proxied-id}` — the publisher (proxier) prefixes its own device ID onto a stable identifier of the proxied device. The proxied identifier is the device's hardware serial when it is known and stable, or a publisher-assigned identifier (e.g., `pv-1`, `pv-2`, …; `evse-1`, …) when the proxied device does not expose a clean single canonical serial (e.g., an Enphase PV string of microinverters with no system-level serial).

The convention prevents three collision scenarios:

1. **Native takeover collision** — when a vendor begins publishing the same physical device natively, its native publication uses the bare identifier, distinct from any proxy's prefixed form. (See §"Disambiguating proxied from native publishers" above for the consumer-side handling.)
2. **Multi-proxier collision** — when multiple proxiers (e.g., multiple enclosures in a multi-enclosure install with a shared broker) each proxy the same physical device, each proxy's prefix makes its device ID unique.
3. **Multi-instance collision** — when a single proxier hosts multiple instances of the same device class (two PVs on one enclosure, two EVSEs, etc.), the per-instance suffix disambiguates within a proxier.

Consumers correlate proxies and native publishers of the same physical device by reading `info/serial-number` (or another vendor-stable identifier), not by device ID.

### ID stability across the proxy-to-native transition

A proxied device's ID is **not** stable across a transition from proxied to natively-published — the proxied form is `{proxier-id}-{proxied-id}` and the native form is `{proxied-id}`. Consumers that need cross-transition stable identity use `info/serial-number` (or another vendor-stable identifier) rather than the Homie device ID.
