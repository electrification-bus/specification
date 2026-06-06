# Utility Meter ↔ Distribution Enclosure Integration Guide

**Type:** Integration Guide (informative)
**Status:** EXPLORATORY
**Version:** 0.1
**Date:** 2026-06-05
**Authors:** Don Jackson

## Overview

This integration guide is **informative**. It describes how two Electrification Bus (eBus for short) data models — the [utility meter](../data-models/utility-meter.md) and the [distribution enclosure](../data-models/distribution-enclosure.md) — compose at runtime when both are present on the same eBus broker, so that a utility-signaled operating envelope reaches the panel's UL 3141-listed Power Control System (PCS) and constrains the panel's load management. The normative property contracts remain in the individual data-model documents; this guide composes them.

The mechanism described here is vendor-neutral. A utility meter publishes its operating envelope to an eBus broker; a distribution enclosure subscribed to that envelope translates the published value into a PCS control setting and enforces it. The data-model surfaces involved (`doe` on the utility-meter, `pcs` on the distribution enclosure) make no vendor-specific assumptions; any conformant publisher / subscriber pair can participate.

The flow described here also mirrors the [Matter 1.5](https://csa-iot.org/all-solutions/matter/) target architecture for the same use case: a utility meter exposes the Meter Identification cluster's `PowerThreshold` attribute, an EMS device subscribes via the Matter Subscribe interaction, the EMS translates internally to its PCS power limit. The eBus pattern and the Matter pattern are structurally identical; experience built on an eBus integration carries directly to a Matter migration.

## Audience and Scope

This guide is for:

- **Utility-meter publishers** (meter OEMs, AMI head-end adapters, integrator-built meter proxies) implementing `doe` on a utility-meter device.
- **Distribution-enclosure publishers** (panel vendors) implementing the subscriber side that consumes a meter's published envelope and translates it to a PCS control setting on `pcs`.
- **Integrators and commissioners** wiring a specific meter and panel together at install time.
- **Reviewers** wanting to understand how the two data-model surfaces compose.

The guide covers:

- The pub / sub flow.
- The mapping from `doe` properties on the meter to `pcs` properties on the enclosure.
- The PCS CSL composition when a meter-driven input is one of several active limits.
- Source-attribution propagation.
- Valid-until handling.
- Commissioning, discovery, and authorization at install time.
- Failure-mode handling.
- The migration relationship to Matter.

The guide does **not** cover:

- Normative property definitions — those live in [`data-models/utility-meter.md`](../data-models/utility-meter.md) and [`data-models/distribution-enclosure.md`](../data-models/distribution-enclosure.md).
- The mechanism by which a utility configures the meter's envelope (AMI head-end, IEEE 2030.5 / CSIP backhaul, proprietary protocols) — out of scope.
- Vendor-specific commissioning UIs and provisioning flows.
- Matter-side specifics beyond the cross-reference in [§Relationship to Matter](#relationship-to-matter) — vendor / SDK-specific bring-up is out of scope here.

---

## Architecture

The integration uses three roles, two devices, and one broker.

```
                          eBus broker
                          (host is an
                           implementation choice)
                                 │
       ┌─────────────────────────┼─────────────────────────┐
       │                         │                         │
       │ publishes               │                         │ publishes &
       │ doe                     │                         │ subscribes
       │                         │                         │
  ┌─────────┐                    │                    ┌──────────┐
  │ Utility │ ──── publish ──────┼─────── subscribe ──│  Distr.  │
  │ Meter   │   (its capability) │   (to meter's doe) │ Enclosure│
  └─────────┘                    │                    └──────────┘
       ▲                         │                         │
       │ utility-signaled        │                         │ internally
       │ envelope (AMI / 2030.5  │                         │ updates own
       │  / proprietary)         │                         │ pcs
       │                                                   │
   ─────────                                          ─────────────
   Utility AMI                                        PCS enforces
                                                      effective limit
                                                      on circuits
```

Three roles:

- **Envelope publisher** — the utility meter. Publishes `doe/power-import-limit` (and optionally the export-side properties and the source / valid-until metadata) onto the eBus broker.
- **Envelope subscriber** — the distribution enclosure. Subscribes to the published envelope on the same broker and applies received values to its own internal state.
- **Enforcement publisher** — the same distribution enclosure. Independently of its subscriber role, the enclosure publishes its own `pcs` properties (the CSL family including `grid-import-limit` and the effective `import-limit`) so that downstream consumers (mobile app, dashboard, energy-management apps) can see what the PCS is currently enforcing.

Two devices, one broker. Both devices connect to the same eBus broker — the meter as a publisher of its `doe` properties, the enclosure as a subscriber to those properties (and, independently, as a publisher of its own `pcs` properties for downstream consumers). **Which LAN element hosts the broker is an implementation choice** that this guide deliberately does not constrain: it may be the enclosure, the meter, a separate gateway or hub, or any other device on the LAN. The pub / sub flow described in this guide is independent of that choice.

## Publish / subscribe semantics

### Topics

The utility meter publishes its full Homie 5 / eBus device representation onto the broker. The DOE properties land at:

```
ebus/5/<meter-id>/doe/power-import-limit
ebus/5/<meter-id>/doe/apparent-power-import-limit
ebus/5/<meter-id>/doe/power-import-limit-source
ebus/5/<meter-id>/doe/power-import-limit-valid-until
ebus/5/<meter-id>/doe/power-export-limit
ebus/5/<meter-id>/doe/apparent-power-export-limit
ebus/5/<meter-id>/doe/power-export-limit-source
ebus/5/<meter-id>/doe/power-export-limit-valid-until
```

The distribution enclosure subscribes to the meter's DOE node. The simplest robust subscription is to the wildcard `ebus/5/<meter-id>/doe/+` so the subscriber receives every DOE property as it is published, including future additions.

### No `/set` semantics

`doe` is publish-only. No `/set` topic is defined on any DOE property. The enclosure has no mechanism to tell the meter what envelope to publish — that is between the meter and the utility's out-of-band configuration channel.

This is a deliberate auth simplification. Each side requires only the minimum permission:

- The **meter** needs publish permission on its own device topics on the broker. It needs no read permission on the enclosure's topics and no write permission on any property of the enclosure.
- The **enclosure** needs subscribe permission on the meter's device topics on the broker. It needs no write permission on any property of the meter.

By contrast, an alternative design where the meter writes a value into the enclosure's `pcs/grid-import-limit` directly — either via MQTT `/set` or via a REST `PUT` — would require the enclosure to grant the meter write privilege on a property that directly controls the PCS. The publish / subscribe pattern avoids that entirely: the meter publishes its own state on its own topics; the enclosure subscribes and applies received values to its own state by its own internal logic. There is no shared mutable surface and no cross-device write privilege.

### Retained values

The DOE properties are published as retained MQTT messages (consistent with the Homie 5 convention for device properties). A subscriber that connects after a value has been published receives the most recent value immediately upon subscribing. The enclosure can re-establish subscription after a disconnect without missing the current envelope.

### Update cadence

DOE values change infrequently relative to instantaneous measurements — typically only when a utility-side event occurs (DR event, grid-management action, contract change). There is no required publish cadence; the meter publishes when the value changes, plus optional periodic re-publication for liveness. Subscribers should treat absence of an update as "no change" rather than as "still unknown."

---

## Property mapping: `doe` → `pcs`

When the enclosure receives a publish on a DOE property, it updates one or more of its own `pcs` properties. The mapping:

| Source (on meter)                              | Target (on enclosure)                              | Notes |
|---|---|---|
| `doe/power-import-limit`            | `pcs/grid-import-limit`                 | Direct mirror. The enclosure's published `grid-import-limit` reflects what the meter has signaled, so downstream consumers see the value the enclosure received. |
| `doe/apparent-power-import-limit`   | (no direct mapping in v0)                          | `pcs` does not currently expose apparent-power CSLs. If the meter publishes only apparent-power and not real-power, the enclosure SHOULD compute an approximate real-power equivalent (using a configured site power factor) and apply it as `grid-import-limit`. |
| `doe/power-import-limit-source`     | (informational, not currently mapped)              | `pcs/grid-import-limit` has no source attribute in v0. See "Source-attribution propagation" below. |
| `doe/power-import-limit-valid-until`| (informational, not currently mapped)              | The enclosure should remember the valid-until and revert to a default behavior when it elapses. See "Valid-until handling" below. |
| `doe/power-export-limit`            | (no current CSL slot)                              | `pcs` does not currently define an export-side CSL family. Enclosures that consume the meter's export limit SHOULD treat it as informational until the dist-enclosure spec adds the corresponding slot. See "Export side" below. |
| `doe/apparent-power-export-limit`   | (no current CSL slot)                              | Same as above. |
| `doe/power-export-limit-source`     | (no current CSL slot)                              | Same as above. |
| `doe/power-export-limit-valid-until`| (no current CSL slot)                              | Same as above. |

The mapping is intentionally a **mirror, not a clamp**. The enclosure publishes the meter-signaled value on `grid-import-limit` as-is (subject only to value-type conversion — e.g., negative-value handling, NaN handling). Clamping to the static feed rating happens via the CSL composition (the min across all CSLs), not by mutating the stored `grid-import-limit`. See "CSL composition" below for why.

### The enclosure stays the authoritative publisher of `pcs`

Even when the enclosure's `grid-import-limit` value is being driven by a meter subscription, the enclosure remains the authoritative publisher of `pcs/grid-import-limit`. Consumers reading the enclosure's PCS see what the enclosure is currently treating as the grid-source CSL — which happens to be what the meter most recently signaled. The chain of provenance is implicit and one-directional: meter publishes its `doe` (utility's intent), enclosure publishes its `pcs` (panel's enforcement state).

This is the same pattern as proxy-published representations (see [`data-models/proxy.md`](../data-models/proxy.md)): the consumer-facing surface is owned by one device per property, even when the underlying value is sourced from another. The DOE → PCS flow is not proxying per se (both devices are native publishers of their own data models), but the principle is the same.

## CSL composition with a meter-driven input

The enclosure's `pcs` already defines a family of import-limit CSLs that compose by `min()`:

- `feed-import-limit` — main breaker / equipment rating (static)
- `grid-import-limit` — grid-source limit (now meter-driven when a meter is present)
- `requested-import-limit` — externally-requested limit (DR push, fleet API)
- `off-grid-import-limit` — active only when islanded

The effective limit the PCS enforces is:

```
effective_import_limit = min(
    feed-import-limit,
    grid-import-limit,           ← driven by meter's doe/power-import-limit when present
    requested-import-limit,
    [off-grid-import-limit if islanded]
)
```

This composition is **why the meter-driven mapping does not clamp**. If the meter publishes 60 kW on a panel whose main breaker rating is 48 kW, the enclosure's `grid-import-limit` stores 60 kW (mirroring what the meter said), the `feed-import-limit` continues to publish 48 kW (the static main-breaker reality), and the effective limit composed by `min()` is 48 kW. Each CSL slot tells consumers what its source is independently of the others; the composition does the right thing without any individual slot needing to clamp.

The same composition handles the case where multiple inputs are present simultaneously — meter publishes a contract limit, fleet API has pushed a more-restrictive DR request — the `min()` picks the binding constraint.

### Interaction with `requested-import-limit`

The pre-existing `requested-import-limit` slot was originally documented in `distribution-enclosure.md` as the slot for "Externally-requested limit (e.g., utility demand-response)." With the meter-driven flow described in this guide, `grid-import-limit` becomes the natural slot for utility-signaled limits delivered over the eBus pub / sub path. `requested-import-limit` continues to exist as the slot for non-meter-driven external requests (e.g., a fleet-management cloud pushing a temporary limit via the panel's REST API, distinct from anything the meter signals).

The two slots can hold different values simultaneously, and the `min()` composition handles the precedence cleanly. An implementation MAY choose to disable external `/set` on `requested-import-limit` when a meter is actively driving `grid-import-limit`, but the spec does not require this — keeping both paths open lets a fleet operator push a more-restrictive limit on top of a meter-signaled one if needed.

---

## Source-attribution propagation

The meter's `doe/power-import-limit-source` carries the origin of the published limit (`CONTRACT` / `REGULATOR` / `EQUIPMENT` / `GRID` / `UNKNOWN`). The enclosure's `pcs/grid-import-limit` has no parallel source attribute in v0 of the distribution-enclosure spec.

Two reasonable v0 behaviors:

1. **Ignore the source** at the enclosure side. The enclosure mirrors the value to `grid-import-limit` and the effective limit calculation proceeds normally. The source attribute is observable on the meter's published topic for any consumer that needs it.
2. **Use the source for behavior modulation** — e.g., an enclosure UI might display a different message when `power-import-limit-source = GRID` (a temporary grid-management action) than when it is `CONTRACT` (a permanent contract limit). The behavior is local to the enclosure and not part of the published surface.

A future revision of the distribution-enclosure spec may add a `grid-import-limit-source` property under `pcs` so the source attribution propagates onto the published PCS surface. That decision is deferred — the source attribute is rarely needed for PCS enforcement (the value alone tells the PCS what to enforce), and adding it prematurely commits the dist-enclosure spec to a vocabulary that may not be the right shape.

## Valid-until handling

The meter's `doe/power-import-limit-valid-until`, when published, indicates when the current published value is expected to expire or be re-evaluated. Typical use cases:

- A demand-response event with a defined window (e.g., 4:00 PM – 7:00 PM peak event).
- A pre-scheduled grid-management action.
- A regulatory limit with a known sunset date.

When the value is published, the enclosure SHOULD remember it. Two behaviors when the timestamp elapses:

1. **Wait for the meter to publish an updated value.** The enclosure continues to enforce the existing `grid-import-limit` until the meter publishes a change. This is the simplest behavior and is appropriate when the meter is expected to publish a new envelope at expiry.
2. **Revert to a fallback when `valid-until` has passed.** The enclosure stops applying the expired value and reverts `grid-import-limit` to a fallback (e.g., the static feed rating). This is appropriate when there is doubt about whether the meter will publish on time.

Most implementations should default to behavior (1) — the meter is the authoritative source, and "wait for the next publish" is the lowest-surprise behavior. Behavior (2) is a defensive fallback for installations where meter reachability is unreliable.

The enclosure does not republish `power-import-limit-valid-until` on its `pcs`. Consumers that need to know when the current limit expires read the meter's published topic directly.

## Export side

The utility-meter data model defines an export-side quartet (`power-export-limit` + apparent + source + valid-until). The distribution-enclosure data model in its current form does not define an export-side CSL family — `pcs` covers import limits only.

This is a known gap. Until the distribution-enclosure spec adds an export-side CSL family:

- The enclosure MAY consume the meter's published export-side properties as informational input for its own internal logic (e.g., curtailing PV inverters or BESS discharge to stay under the export limit).
- The enclosure does NOT publish an export-side CSL on `pcs`. Consumers wanting visibility into the utility-signaled export limit read the meter's published `doe/power-export-limit` directly.
- When the distribution-enclosure spec adds an export-side family (likely properties named `grid-export-limit`, `feed-export-limit`, `requested-export-limit`, etc., mirroring the import side), this integration guide will be updated to extend the mapping table accordingly.

---

## Commissioning

The enclosure needs three things to subscribe to the meter:

1. **A network path to the broker.** Both devices must reach the same eBus broker over the LAN. Network-provisioning specifics (Wi-Fi vs. Ethernet, addressing, mDNS discovery) are out of scope for this guide; vendors document them in their product-specific integration material.
2. **Broker credentials for each side.** Both the meter and the enclosure authenticate to whichever LAN element hosts the broker, using that host's provisioning flow, and obtain MQTT credentials. The host's auth interface is its own concern (typically a vendor-specific REST or out-of-band provisioning channel) and is outside the scope of this guide.
3. **Knowledge of which meter ID to subscribe to.** Two options:
   - **Discovery-driven** — the enclosure subscribes to Homie discovery topics, observes any device that advertises `$description.type = energy.ebus.device.utility-meter`, and subscribes to that device's `doe` automatically.
   - **Commissioning-driven** — the enclosure is configured at commissioning time with a specific utility-meter device ID and subscribes only to that meter.

Discovery-driven is simpler and matches the spirit of Homie's auto-discovery convention. Commissioning-driven is more deterministic and prevents the enclosure from accidentally subscribing to an unrelated meter that joins the same broker.

Both approaches are valid. Implementations SHOULD support discovery-driven subscription and MAY layer a commissioning-driven filter on top of it (e.g., subscribe to any utility-meter, but only apply published envelopes from a specifically commissioned device).

## Failure modes

| Scenario                                              | Subscriber (enclosure) behavior                                                          |
|---|---|
| Meter offline; broker stops receiving meter publishes | Keep enforcing the last received `grid-import-limit`. The retained MQTT message remains the most recent published value. |
| Meter explicitly publishes empty / missing `power-import-limit` | Treat as "no meter-signaled limit" — revert `grid-import-limit` to absent (per Homie convention) or to a fallback (typically the static feed rating). |
| Meter publishes `power-import-limit` exceeding `feed-import-limit` | Store the meter's value on `grid-import-limit` as-is. The `min()` composition automatically caps the effective limit at the feed rating. No clamping at the slot level. |
| `power-import-limit-valid-until` elapses with no new publish | Default behavior: keep enforcing the existing value (the meter is authoritative, no news = no change). Defensive alternative: revert to fallback. See "Valid-until handling" above. |
| Subscription disconnects (the enclosure's MQTT client loses its connection to the broker) | Re-subscribe. Because messages are retained, re-subscription delivers the most recent published value immediately. |
| Enclosure restarts | On startup, the subscriber side re-subscribes and receives the retained DOE values. The PCS resumes enforcement based on the recovered envelope. |
| Meter publishes a value type the subscriber cannot parse | Treat as if no value were published; log diagnostic; revert to fallback. |
| Two utility-meter devices appear on the broker | An implementation choice. Discovery-driven subscribers SHOULD log a diagnostic and either (a) refuse to apply either value (safe default) or (b) apply the more-restrictive of the two values. Commissioning-driven subscribers ignore the non-commissioned device. The spec does not currently support multiple simultaneous utility meters on one service. |

## Examples

A concrete pub / sub trace showing a demand-response event.

```
T0 — Initial state. Meter and enclosure are both online. The meter's
     DOE values reflect a normal contract limit:

  ebus/5/meter-7a3f/doe/power-import-limit        = 30000
  ebus/5/meter-7a3f/doe/power-import-limit-source = "CONTRACT"
  ebus/5/meter-7a3f/doe/power-import-limit-valid-until = ""

     The enclosure has subscribed and is mirroring the value:

  ebus/5/enclosure-c402/pcs/feed-import-limit          = 48000  (static)
  ebus/5/enclosure-c402/pcs/grid-import-limit          = 30000  (meter-driven)
  ebus/5/enclosure-c402/pcs/requested-import-limit     = (absent)
  ebus/5/enclosure-c402/pcs/import-limit               = 30000  (effective = min)

T1 — Utility issues a DR event via AMI. The meter receives the new
     envelope and publishes updated DOE values:

  ebus/5/meter-7a3f/doe/power-import-limit        = 12000
  ebus/5/meter-7a3f/doe/power-import-limit-source = "GRID"
  ebus/5/meter-7a3f/doe/power-import-limit-valid-until = "2026-06-05T19:00:00Z"

T2 — Enclosure receives the publish on its DOE subscription. It updates
     its own PCS state:

  ebus/5/enclosure-c402/pcs/grid-import-limit          = 12000
  ebus/5/enclosure-c402/pcs/import-limit               = 12000  (new effective limit)

T3 — Enclosure's PCS recomputes the effective limit and curtails loads
     accordingly. High-power deferrable loads (EVSE, water heater) are
     throttled; critical loads continue. The mobile app, observing the
     enclosure's published PCS, shows the new effective limit and a
     "demand response active" indicator (sourced by the consumer from
     the meter's published power-import-limit-source = GRID).

T4 — DR event ends. The meter receives the post-event envelope and
     publishes:

  ebus/5/meter-7a3f/doe/power-import-limit        = 30000
  ebus/5/meter-7a3f/doe/power-import-limit-source = "CONTRACT"
  ebus/5/meter-7a3f/doe/power-import-limit-valid-until = ""

T5 — Enclosure mirrors the new value:

  ebus/5/enclosure-c402/pcs/grid-import-limit          = 30000
  ebus/5/enclosure-c402/pcs/import-limit               = 30000

     PCS un-curtails. Deferred loads resume.
```

Throughout the trace the meter never wrote to a PCS property and the enclosure never wrote to a DOE property. The two devices coordinated entirely through the pub / sub pattern with each side updating only its own published state.

---

## Relationship to Matter

The Matter target architecture for the same use case is structurally identical to the eBus flow described here. Cross-reference:

| eBus mechanism                                                | Matter equivalent                                                  |
|---|---|
| Utility meter publishes `doe` on the shared eBus broker | Utility meter exposes Meter Identification cluster (0x0B06) with `PowerThreshold` (PWRTHLD feature) |
| Enclosure subscribes via MQTT subscribe                        | EMS device subscribes via Matter Subscribe interaction             |
| Meter publishes update; enclosure receives publish             | Meter reports attribute change; subscribed EMS receives report     |
| Enclosure maps to `pcs/grid-import-limit`, recomputes effective limit | EMS maps to its PCS power limit setting                            |
| `power-import-limit-source` enum value                         | `PowerThresholdSourceEnum` (with eBus's added `GRID` value closing the gap Matter 1.5 currently has) |
| `power-export-limit` quartet                                   | (no Matter 1.5 equivalent; proposed for a future Matter release)   |
| Topic-based pub / sub on the broker                            | Cluster-attribute subscribe over Matter fabric                     |
| Self-signed TLS, broker credentials                            | Matter fabric credentials, CASE sessions                           |

The eBus flow is a near-mirror of the Matter flow at the *semantics* level. The differences are at the *transport* level (MQTT topics vs. Matter cluster attributes) and at the *trust* level (broker credentials and self-signed TLS vs. fabric and CASE).

An implementer who builds the eBus integration first carries the semantic understanding of the flow forward to the Matter migration; the architectural decisions (publish-only meter, subscriber-side mapping, `min()` composition with existing CSLs, valid-until handling, failure modes) are identical.

## Open questions

1. **Source propagation onto `pcs`.** Should the distribution-enclosure spec add a `grid-import-limit-source` (and possibly `grid-import-limit-valid-until`) property so the meter-signaled source attribution is visible on the enclosure's published PCS surface? Deferred until a real consumer of that propagation exists.
2. **Export-side CSL family on `pcs`.** When the distribution-enclosure spec adds export-side CSLs (likely as part of broader DER-aware revisions), update the mapping table here.
3. **Apparent-power CSLs on `pcs`.** Currently the enclosure's CSL family is real-power-only. If the dist-enclosure spec later adds apparent-power-aware CSLs, the meter's `apparent-power-import-limit` will have a direct mapping target.
4. **Multi-meter scenarios.** This guide assumes one utility meter per service. If the model needs to extend to multi-meter cases (sub-meters, dual-fed services), how does the enclosure compose multiple `doe` sources? Open.
5. **Discovery-vs-commissioning policy.** This guide describes both, leaves the choice to implementations. A future revision may pick a recommended default.
6. **Implementation patterns when one device both hosts the broker and publishes to or subscribes to it.** Specific broker implementations differ in how they expose the publish-and-subscribe-to-self loop (separate client connection vs. broker-internal subscription hook). Out of scope for this guide.

## References

- [Utility-meter data model](../data-models/utility-meter.md) — defines `doe` (the publisher side).
- [Distribution-enclosure data model](../data-models/distribution-enclosure.md) — defines `pcs` and the existing CSL family (the subscriber side, target of the mapping).
- [eBus capability-type registry](../registries/capability-types.md).
- [Proxy model](../data-models/proxy.md) — for the general convention that a device is the authoritative publisher of its own published surface even when the underlying value is sourced from another device.
- [Matter 1.5 Meter Identification cluster (0x0B06)](https://csa-iot.org/all-solutions/matter/) — the Matter-side mechanism this eBus flow mirrors.
- [UL 3141](https://www.shopulstandards.com/ProductDetail.aspx?productId=UL3141) — Power Control Systems. The standard the enclosure's PCS is listed against.
- IEEE 2030.5 / CSIP — origin of "dynamic operating envelope" terminology.
