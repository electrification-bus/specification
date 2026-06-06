# Electrification Bus Battery Energy Storage System (BESS) Data Model Specification

**Status:** DRAFT
**Version:** 0.6
**Date:** 2026-06-06
**Authors:** Don Jackson

## Overview

This Electrification Bus (eBus for short) specification defines how a Battery Energy Storage System (BESS) should be represented using the [Homie 5 convention](https://homieiot.github.io/specification/). It aspires and attempts to be vendor-agnostic — any BESS, regardless of manufacturer, should be able to conform to this specification when publishing its state to an eBus MQTT broker.

The spec defines a **device hierarchy** (parent BESS device with child devices for components), **capability nodes** (what each device can do), and **property catalogs** (specific properties with datatypes, units, and requirement levels).

### Terminology

| Term | Definition |
|---|---|
| BESS | Battery Energy Storage System — the complete backup system |
| DER | Distributed Energy Resource — any grid-connected energy device |
| MID | Microgrid Interconnect Device — manages grid connection and islanding |
| Proxy publisher | A device-role entity that publishes a Homie device on behalf of a non-eBus-native BESS — typically bridging from the BESS vendor's proprietary API. The published representation is a *proxy*. A proxy is functionally equivalent to a native eBus publication of the same device (same property contracts, same lifecycle, same discovery) and is discoverable as a proxy via its `root.$type`. See the [framework spec §Detail: Proxy Publishers](../framework.md#detail-proxy-publishers) and [`data-models/proxy.md`](proxy.md) for the canonical proxy convention. |
| Capability | A Homie node representing a functional aspect of a device (metering, state-of-charge, etc.) |

### Conventions

- **MUST**, **SHOULD**, **MAY** follow [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) definitions
- All properties use SI base units via the Homie `unit` attribute — no units in property IDs
- Power and energy follow the IEC 62053 metering convention:
  - `active-power` (W) — signed; positive = power flowing out of the device
  - `imported-energy` (Wh) — always positive, cumulative
  - `exported-energy` (Wh) — always positive, cumulative
- If a device cannot provide a property, it MUST omit it from `$description` rather than publishing sentinel values
- Property IDs use kebab-case (e.g., `active-power`, `serial-number`)

### References

- [eBus — ebus.energy](https://ebus.energy/) — eBus specification home
- [Homie 5 Specification](https://homieiot.github.io/specification/) — the underlying IoT convention this data model builds on
- [Homie Units](https://homieiot.github.io/specification/#units)
- [IEC 62053 — Electricity metering equipment](https://webstore.iec.ch/en/publication/62053)
- [Electrification Bus distribution-enclosure data model](distribution-enclosure.md) — companion data-model spec for distribution enclosures
- [SPAN-API-Client-Docs (public)](https://github.com/spanio/SPAN-API-Client-Docs) — public API documentation for the SPAN distribution-enclosure implementation, which currently uses the proxy publication pattern defined in this spec

---

## Device Hierarchy

A BESS is represented as a **parent Homie device** with **child devices** for its physical components. Each device exposes one or more **capability nodes**.

```
energy.ebus.device.bess (parent device)
  ├── energy.ebus.device.battery    (child, one per battery pack)
  ├── energy.ebus.device.inverter   (child, if applicable)
  ├── energy.ebus.device.mid        (child, REQUIRED for grid-forming-capable BESSs)
  └── energy.ebus.device.meter      (child, per metering point: site, load, solar)
```

### Grid-forming-capable vs grid-following-only BESS

This spec recognizes two BESS variants, distinguished by whether the BESS can act as the AC voltage/frequency reference for an islanded microgrid:

- A **grid-forming-capable BESS** (sometimes abbreviated **GFM-capable**) is able to form a microgrid — to act as the voltage/frequency reference when the home is islanded from the utility grid. This is the typical residential backup product (Tesla Powerwall, Enphase IQ Battery, SolarEdge Energy Bank, etc.).
- A **grid-following-only BESS** (**GFL-only**) operates only as a current source synchronized to an existing grid-forming reference (the utility). It cannot back up the home during a grid outage; its value is energy management (TOU shift, NEM3 self-consumption, demand response). Smaller, lower-cost batteries fall into this class.

**A grid-forming-capable BESS publisher MUST include a MID child device.** The MID is the canonical home for grid-connection and islanding state (`grid`) and for the grid-forming-entity signal. When the underlying hardware does not present a separable MID, the publisher synthesizes a minimal MID child exposing at least `info` and `grid`.

**A grid-following-only BESS publisher MAY omit the MID child** — the absence of the MID child is itself the signal that the BESS does not support backup / off-grid operation. A grid-following-only BESS is always on-grid (when operating) and never grid-forms, so `islanding-state` / `grid-state` / `grid-forming-entity` are not meaningful for it.

For a grid-following-only BESS, the value to a coordinating distribution-enclosure or HEMS comes primarily through `dispatch` (charge / discharge setpoint control — see below). Without dispatch, a grid-following-only BESS is functionally indistinguishable from a PV system to the rest of the home.

### Design Principles

This data model follows the Electrification Bus design principles — the Homie devices-vs-nodes split, parent aggregation, standard capability-type reuse across device classes, proxying as a first-class peer to native publishing, property placement on the authoritative device, forward compatibility, and multi-instance modeling. See **[Design Principles in framework.md](../framework.md#design-principles)** for the canonical list. Examples worth noting for BESS publishers:

- *Homie devices represent physical things* — a battery pack, an inverter, a MID, a meter (framework principle #1).
- *Publish what you have, omit what you don't* — not every BESS has all components. A simple system might be just the parent BESS device with one battery child and one MID child; a complex system might have 6 battery children, an inverter, a MID, and 3 meter children. The spec accommodates both (framework principle #3).
- *Parent aggregates children* — the parent BESS device provides aggregated values (total SOC, total battery power) so consumers don't need to discover and sum children (framework principle #4).
- *Proxying is first-class* — a vendor implementing eBus directly in their BESS firmware and a third-party proxy publisher translating from the vendor's proprietary API both produce the same device shape. The consumer-facing surface is identical; the source of the data is transparent to consumers. This is fundamental to eBus's adoption strategy — proxies bridge the gap between today's reality (most BESS vendors do not yet speak eBus) and the future where they do (framework principle #6).

### Device Types

| Type | Description |
|---|---|
| `energy.ebus.device.bess` | Parent BESS system device. Contains aggregated state and system-level configuration. |
| `energy.ebus.device.battery` | Individual battery pack. Child of BESS. |
| `energy.ebus.device.inverter` | DC-AC inverter. May handle both battery and solar (e.g., Powerwall 3). Child of BESS. |
| `energy.ebus.device.mid` | Microgrid Interconnect Device (MID). Manages grid connection and islanding. Child of BESS. |
| `energy.ebus.device.meter` | Metering point. Used for site, load, or solar metering. Child of BESS. |

### Device IDs

Device IDs in a **native** publication (the BESS is its own Homie root) are derived from the physical serial number of the system:

| Device | ID Pattern | Example |
|---|---|---|
| Parent BESS | `{serial}` | `TG123456789` |
| Battery (pack N) | `{serial}-battery-{N}` | `TG123456789-battery-1` |
| Inverter | `{serial}-inverter` | `TG123456789-inverter` |
| MID | `{serial}-mid` | `TG123456789-mid` |
| Site meter | `{serial}-site-meter` | `TG123456789-site-meter` |
| Load meter | `{serial}-load-meter` | `TG123456789-load-meter` |
| Solar meter | `{serial}-solar-meter` | `TG123456789-solar-meter` |

**Proxied publication.** When the BESS is published by a proxy (e.g., a distribution enclosure proxying a Tesla Powerwall), the proxy prefixes its own device ID onto each of the BESS device IDs above. For example, an enclosure with device ID `ab-1234-c5d67` proxying a Tesla Powerwall `TG123456789` publishes the BESS as `ab-1234-c5d67-TG123456789`, the synthesized MID as `ab-1234-c5d67-TG123456789-mid`, and so on. This prevents collisions when (a) the vendor later begins publishing the same physical device natively (the native form uses the bare `{serial}`, distinct from any proxy's prefixed form), or (b) multiple proxiers share a broker (each proxy's prefix makes its device ID unique). Consumers correlate proxies and native publishers of the same physical BESS by reading `info/serial-number`, not by device ID.

### MQTT Topic Structure

All devices publish under the eBus Homie 5 topic prefix:

```
ebus/5/{device-id}/$state
ebus/5/{device-id}/$description
ebus/5/{device-id}/{capability-node-id}/{property-id}
```

Parent-child relationships are declared in the parent's `$description` via the Homie 5 `children` attribute.

---

## Capability Node Types

### info

System and device identification.

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `vendor-name` | string | — | MUST | Manufacturer name (e.g., "Tesla", "Enphase") |
| `serial-number` | string | — | MUST | Device serial number |
| `product-name` | string | — | SHOULD | Product name (e.g., "Powerwall 2 AC") |
| `model` | string | — | MAY | Model/part number |
| `firmware-version` | string | — | SHOULD | Device firmware/software version |
| `nameplate-capacity` | float | kWh | SHOULD | Nameplate energy capacity (battery devices) |
| `data-model-version` | string | — | SHOULD | Version of the eBus BESS data model this device publishes (e.g., `"1.0"`). Parent BESS device only. |
| `proxied` | boolean | — | MAY | Optional disambiguation when both a proxy publisher and a native publisher of the same physical device coexist. `true` = this representation is proxied (e.g., published by a third-party adapter); `false` = published natively (by the vendor's own implementation); absent = no explicit signal, and consumers fall back to inspecting the `root` device's `$description.type`. See §"Disambiguating publishers" below. |

### soc

Battery state of charge and energy.

**Node type:** `energy.ebus.capability.soc`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `soc` | float | % | MUST | State of charge (0–100%) |
| `soe` | float | kWh | SHOULD | State of energy — available energy remaining |

On the parent BESS device, these values are aggregated across all battery children.

### meter

Power and energy metering.

**Node type:** `energy.ebus.capability.meter`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | MUST | Instantaneous active power. Positive = power flowing out of device. |
| `imported-energy` | float | Wh | SHOULD | Cumulative energy imported (consumed) by the device. Always positive. |
| `exported-energy` | float | Wh | SHOULD | Cumulative energy exported (produced) by the device. Always positive. |
| `current` | float | A | MAY | RMS current |
| `voltage` | float | V | MAY | RMS voltage |
| `frequency` | float | Hz | MAY | AC frequency |
| `reactive-power` | float | var | MAY | Reactive power |
| `apparent-power` | float | VA | MAY | Apparent power |
| `power-factor` | float | — | MAY | True power factor (0–1) |
| `apparent-energy-imported` | float | VAh | MAY | Cumulative apparent energy imported. Always positive. |
| `apparent-energy-exported` | float | VAh | MAY | Cumulative apparent energy exported. Always positive. |

### grid

Grid connection and islanding state. Always published on a MID device — the parent BESS device does not publish this capability.

**Node type:** `energy.ebus.capability.grid`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `islanding-state` | enum | MUST | Current operational state: `ON_GRID`, `OFF_GRID`, `UNKNOWN` |
| `grid-state` | enum | SHOULD | Sensed grid condition: `UP`, `DOWN`, `DEGRADED`, `UNKNOWN`. `DEGRADED` (grid quality outside the band for `UP` but not yet an outage) is OPTIONAL — publishers SHOULD distinguish `DEGRADED` from `UP`/`DOWN` when they have the underlying measurement capability. Proxied black-box MIDs typically do not surface this distinction and report only `UP`/`DOWN`/`UNKNOWN`. |
| `grid-forming-entity` | string | SHOULD | Identity of the device currently establishing the AC voltage/frequency reference. Value: `"GRID"` when grid-tied, or the Homie device ID of the grid-forming hardware (typically the BESS parent device ID, or a V2H EVSE, or a generator) when islanded. Empty string or absent during transitions or when unknown. |

`islanding-state` reflects the MID's relay position (are we connected to the grid?). `grid-state` reflects what the MID senses about the grid itself (is power available?). These can differ — a system can be `OFF_GRID` with grid `UP` (intentional island) or `OFF_GRID` with grid `DOWN` (outage).

`grid-forming-entity` identifies *which* DER is acting as the voltage/frequency reference. When grid-tied, the utility is always the grid-forming entity and the value is `"GRID"`. When islanded, exactly one inverter-based DER is forming the grid; its parent device ID is the value. The two signals are correlated but distinct: `islanding-state == ON_GRID` ⇒ `grid-forming-entity == "GRID"`; `islanding-state == OFF_GRID` ⇒ `grid-forming-entity` is a Homie device ID. Consumers may use either signal for binary "tied vs. islanded" decisions; `grid-forming-entity` adds the identity of the GFE on top.

**Granularity convention:** the GFE value is the **DER parent device ID** (the parent BESS, the V2H EVSE parent, the generator), not an inverter child device ID. Vendor opacity is the controlling reason: vendors typically do not expose per-inverter grid-forming coordination to integrators, and reporting at parent granularity matches what is externally observable from any conformant adapter. When a vendor does expose per-inverter grid-forming state, the per-inverter detail lives on the inverter child via the optional `grid-forming` (defined below).

### grid-forming

Per-inverter grid-forming capability and current state. **Optional** — published only when an inverter is exposed as a distinct child device AND the vendor surfaces per-inverter grid-forming state. Most BESS adapters today will not publish this capability; the BESS-parent-level `grid-forming-entity` value on the MID is the externally-observable signal for "which DER is grid-forming."

**Node type:** `energy.ebus.capability.grid-forming`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `capable` | boolean | MUST (when capability is published) | Static hardware capability — does this inverter support grid-forming operation at all? |
| `active` | boolean | SHOULD (when `capable = true`) | Current state — is this inverter actively grid-forming right now? When `false` and the inverter is energized, it is grid-following. |

The two layers of representation are coherent: `<mid>/grid/grid-forming-entity == <bess-parent-id>` says "this BESS is the grid-forming entity" (externally observable, all systems); `<inverter-child-id>/grid-forming/active == true` says "this specific inverter is the one actively grid-forming" (vendor-specific, when published). The MID-level value is authoritative for which DER is grid-forming; the inverter-level flags are descriptive detail when available.

### config

System-level configuration and operational state. Applies to the parent BESS device.

**Node type:** `energy.ebus.capability.config`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `backup-reserve` | float | % | MAY | Backup reserve percentage (0–100%). Settable. |
| `operational-state` | enum | — | SHOULD | Current operational state: `IDLE`, `CHARGING`, `DISCHARGING`, `STANDBY`, `UNKNOWN` |
| `nominal-power` | float | W | MAY | Maximum rated power output |
| `available-charge-power` | float | W | MAY | Currently available charge power headroom |
| `available-discharge-power` | float | W | MAY | Currently available discharge power headroom |

### dispatch

External dispatch controls — settable charge / discharge rate setpoints and SOC limits — that allow a controller (a distribution enclosure's PowerUp logic, an energy-management system, a HEMS, etc.) to coordinate the BESS's charge/discharge behavior in real time. Applies to the parent BESS device.

`dispatch` is **MAY-level**. A BESS publisher publishes it only when the underlying product exposes the corresponding control surface. A BESS that does not publish `dispatch` follows its own vendor-internal control logic; external controllers can observe its state but cannot directly dispatch it.

**Node type:** `energy.ebus.capability.dispatch`

| Property ID | Datatype | Unit | Req | Settable | Persistence | Description |
|---|---|---|---|---|---|---|
| `charge-rate-set` | float | W | MAY | yes | watchdog | Requested charge rate (from grid, or wherever the BESS is configured to charge from). Positive value = charge at this rate. `0` = do not charge. The BESS honors the setpoint when conditions allow (within hardware limits, SOC constraints, and any active `config/operational-state` overrides). |
| `discharge-rate-set` | float | W | MAY | yes | watchdog | Requested discharge rate (to home or to grid, depending on system configuration). Positive value = discharge at this rate. `0` = do not discharge. Same conditional-honoring semantics as `charge-rate-set`. |
| `max-soc-set` | float | % | MAY | yes | policy | Upper SOC limit (0–100). The BESS stops charging when SOC reaches this value. Persists indefinitely (set-and-forget) until overwritten or device reset. |
| `min-soc-set` | float | % | MAY | yes | policy | Lower SOC limit (0–100). The BESS stops discharging when SOC drops to this value. Persists indefinitely. |
| `dispatch-watchdog-timeout` | integer | s | MAY | no | — | How long a watchdog-class setpoint persists before reverting to the BESS's safe-default behavior. Implementation-defined; typical range 30 s to 300 s. Published so controllers know the refresh cadence required to keep dispatch active. |
| `dispatch-safe-default` | enum | — | MAY | no | — | What the BESS reverts to after a watchdog-class setpoint expires: `IDLE` (no dispatch — both rates effectively `0`), `VENDOR_DEFAULT` (the BESS's own internal control logic resumes), or `LAST_VALUE` (rare; only for slow-response systems where reverting to default would cause undesirable transients). |
| `dispatch-state` | enum | — | MAY | no | — | The BESS's current dispatch status: `IDLE` (no external setpoint active), `CHARGING_DISPATCHED` (honoring an external `charge-rate-set`), `DISCHARGING_DISPATCHED` (honoring an external `discharge-rate-set`), `VENDOR_CONTROLLED` (running on vendor-internal logic — either no external setpoint, or a setpoint was active but expired and `dispatch-safe-default = VENDOR_DEFAULT`), `UNKNOWN`. |
| `dispatch-controller` | string | — | MAY | no | — | Identifier of the most recent client to successfully write a settable property in this capability. Format is implementation-defined; typical values include the writer's MQTT client ID, the Homie device ID of an issuing controller, or an authenticated user identifier. Useful for debugging multi-writer scenarios. Empty / absent when no dispatch is active. |
| `charge-rate-actual` | float | W | MAY | no | — | Observed instantaneous charge rate. Distinguishes "controller wrote charge-rate-set = 5000, BESS is actually charging at 5000" from "BESS could not honor the setpoint and is charging at a different rate (e.g., hardware-limited)." |
| `discharge-rate-actual` | float | W | MAY | no | — | Observed instantaneous discharge rate. |

**Persistence classes.** Each settable property declares its persistence semantics:

- **watchdog** — value reverts to the published `dispatch-safe-default` if not refreshed within `dispatch-watchdog-timeout`. Used for rate setpoints, which require ongoing coordination and where stale values would have undesirable consequences (a controller crash should not leave the BESS charging from grid indefinitely).
- **policy** — value persists indefinitely until overwritten or device reset. Used for SOC limits, which are set-and-forget commissioning decisions where persistence across controller restarts is desirable.
- **expiry** — *(reserved for future)* value carries an explicit expiry timestamp; reverts after the timestamp passes. Future extension for time-bounded scheduled dispatch.

A BESS publisher MUST declare each settable property's persistence class through the property description above (which is normative); publishers MUST honor the declared semantics.

**Conflict resolution.** If multiple controllers write to the same settable property, the default is last-write-wins. A BESS implementation MAY enforce stricter access control (e.g., by client certificate role per the eBus core spec's security model) but this is implementation-specific and not normatively required by the data model. The `dispatch-controller` observable is the recommended debugging surface for multi-writer scenarios.

**Interaction with `config/backup-reserve`.** A BESS that publishes both `config/backup-reserve` (the off-grid energy reserve) and `dispatch/min-soc-set` (the dispatch-time lower SOC limit) MUST honor whichever is higher when discharging. `backup-reserve` is a backup-mode policy; `min-soc-set` is a dispatch-time policy; the BESS does not discharge below either.

**Relationship to config/operational-state.** When `dispatch-state` is anything other than `VENDOR_CONTROLLED`, the BESS's behavior is being driven by external dispatch and `operational-state` (`IDLE`/`CHARGING`/`DISCHARGING`/`STANDBY`) reflects the *result* of that dispatch, not the cause. Controllers should treat `dispatch-state` as the authoritative signal for "who is driving this BESS right now."

### status

Operational status and fault reporting. Each property represents a standard fault category.

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Req | Description |
|---|---|---|---|
| `communication` | enum | MUST | Adapter-to-BESS communication: `OK`, `LOST`, `DEGRADED` |
| `authentication` | enum | SHOULD | Credential/auth status: `OK`, `FAILED`, `EXPIRED`, `MISSING` |
| `discovery` | enum | SHOULD | Device discovery status: `OK`, `NOT_FOUND`, `SERIAL_MISMATCH` |
| `device-fault` | enum | SHOULD | BESS-reported fault: `OK`, `FAULTED` |

---

## Device Specifications

### Parent BESS Device

**Type:** `energy.ebus.device.bess`

The parent device represents the BESS system as a whole. It provides aggregated state across all children and system-level configuration.

**Capabilities:**

| Capability | Required | Notes |
|---|---|---|
| `info` | MUST | Includes `data-model-version` |
| `soc` | MUST | Aggregated across all battery children |
| `meter` | MUST | Aggregated power/energy at the BESS's external boundary (i.e., what the BESS exchanges with the rest of the system); `active-power` MUST be published. |
| `config` | MAY | System-level settings (backup-reserve, etc.) |
| `dispatch` | MAY | External-dispatch controls (charge-rate setpoint, SOC ceilings, etc.). See §"dispatch" below. |
| `status` | MUST | System-level fault status |

Grid connection and islanding state live on the MID child device (`grid`) when the BESS is grid-forming-capable (see §"Device Hierarchy"). A grid-following-only BESS omits the MID child.

### Battery Device

**Type:** `energy.ebus.device.battery`

Represents an individual battery pack. A BESS may have one or many.

**Capabilities:**

| Capability | Required | Notes |
|---|---|---|
| `info` | MUST | Per-pack serial, capacity |
| `soc` | MUST | This pack's SOC/SOE |
| `meter` | SHOULD | This pack's power/energy |
| `status` | MAY | Per-pack fault status |

### Inverter Device

**Type:** `energy.ebus.device.inverter`

Represents the DC-AC inverter. May handle both battery and solar conversion (e.g., Tesla Powerwall 3).

**Capabilities:**

| Capability | Required | Notes |
|---|---|---|
| `info` | MUST | |
| `meter` | SHOULD | AC-side power/energy |
| `status` | MAY | |
| `grid-forming` | MAY | Per-inverter grid-forming capability and state; published only when the vendor exposes this detail |

### MID Device

**Type:** `energy.ebus.device.mid`

Represents the Microgrid Interconnect Device (MID). Manages grid connection and islanding. A **grid-forming-capable** BESS publisher MUST include a MID child device. A grid-following-only BESS publisher MAY omit it — see §"Grid-forming-capable vs grid-following-only BESS".

**Capabilities:**

| Capability | Required | Notes |
|---|---|---|
| `info` | MUST | |
| `grid` | MUST | `islanding-state` MUST, `grid-state` SHOULD, `grid-forming-entity` SHOULD |
| `status` | MAY | |

### Meter Device

**Type:** `energy.ebus.device.meter`

Represents a metering point. Used for site-level, load, or solar metering when the BESS provides this data.

**Capabilities:**

| Capability | Required | Notes |
|---|---|---|
| `info` | MUST | `product-name` identifies the metering point (e.g., "Site Meter", "Solar Meter") |
| `meter` | MUST | |

---

## Versioning

The parent BESS device SHOULD publish a `data-model-version` property on its `info` node (e.g., `"1.0"`). The BESS's `data-model-version` is independent of the distribution-enclosure's `data-model-version` and of any other device's `data-model-version` — each device class has its own version axis.

The data-model version follows standard [semver](https://semver.org/) semantics:

- **Major bump** — any change that could break a conforming consumer of the previous version: property removal, datatype change, semantic redefinition, enum value removal, requirement-level promotion that invalidates previously-conforming publishers, retiring or renaming any MUST/SHOULD property.
- **Minor bump** — backward-compatible additive change: new optional capabilities, new MAY-level properties, additive enum extensions, MAY → SHOULD promotion that does not invalidate previously-conforming publishers.
- **Patch bump** — clarifications and editorial fixes only; no on-the-wire impact.

Consumers MUST check `$description` to discover available properties regardless of version.

---

## Security and Discovery (Out of Scope)

This specification defines what a BESS adapter publishes once it is connected and operational. The following are implementation details outside the scope of this spec:

- **Credential management** — how the adapter obtains authentication tokens or credentials for the BESS vendor API
- **Device discovery** — how the adapter finds BESS devices on the network (mDNS, manual configuration, etc.)

---

## Disambiguating publishers

Typically a given physical BESS is published by exactly one publisher — either the vendor's own native implementation or a third-party adapter — and consumers see one representation. During an adoption transition (e.g., a third-party adapter publishes a BESS today; the vendor someday begins publishing the same BESS natively), it is possible for both publishers to coexist and present the consumer with two representations of the same physical device. The spec offers two mechanisms for consumers to disambiguate.

### Implicit, via the Homie `root` reference and the root device's `$description.type` (primary mechanism)

Every Homie child device declares its `root`. A consumer that finds two BESS devices with the same `info/serial-number` can determine which is which by inspecting the type of each one's root device:

- If the root device's `$description.type` is `energy.ebus.device.bess` — i.e., the BESS is its own root — this representation is the BESS publishing itself natively. (Equivalently: the BESS's `root` field is the BESS's own ID, or absent per Homie 5's convention for top-level devices.) The vendor identity is in the BESS's `info/vendor-name`.
- If the root device's `$description.type` is anything other than `energy.ebus.device.bess` (a distribution enclosure, a gateway, an integration hub of some other type), this representation is being proxied by that root device. The root's `info/vendor-name` identifies the proxy publisher.

Per the eBus vendor-neutrality principle, vendors publishing BESS devices natively use the same `energy.ebus.device.bess` type as adapters publishing on behalf of those vendors; vendor identity lives in `info/vendor-name`, not in the device type string. The general heuristic is "prefer the native (vendor-published) representation over a proxied one." This works without any new property: every Homie 5 device already publishes `root`, and the consumer just inspects the root's existing `$description.type`.

### Explicit, via the optional `proxied` boolean (secondary mechanism)

A publisher MAY publish a `proxied` boolean property on a device's `info` for direct disambiguation:

- `proxied = true` — this representation is proxied (e.g., published by a third-party adapter).
- `proxied = false` — this representation is published natively (by the vendor's own implementation).
- absent — no explicit signal; consumers fall back to the implicit-via-root mechanism above.

`proxied` is MAY-level and is not required. The property is reserved here so that any publisher that wants to make the distinction unambiguous has a defined slot to use, rather than inventing its own ad-hoc property.

---

## Example: Tesla Powerwall System

A Tesla Powerwall 2 system with 6 battery packs, a gateway (inverter), and a MID:

```
ebus/5/TG123456789/                          energy.ebus.device.bess (parent)
  $description                                JSON schema with children declared
  info/vendor-name                            "Tesla"
  info/serial-number                          "TG123456789"
  info/data-model-version                     "1.0"
  soc/soc                                     98.5
  soc/soe                                     80.1
  meter/active-power                          10.0
  status/communication                        OK

ebus/5/TG123456789-battery-1/                 energy.ebus.device.battery
  info/serial-number                          "PW2-001"
  info/nameplate-capacity                     13.5
  soc/soc                                     100
  soc/soe                                     13.5
  meter/active-power                          0.0

  ... (batteries 2-6 similar)

ebus/5/TG123456789-inverter/                  energy.ebus.device.inverter
  info/serial-number                          "INV-001"
  info/firmware-version                       "26.10.0"
  meter/active-power                          5530.0

ebus/5/TG123456789-mid/                       energy.ebus.device.mid
  info/serial-number                          "MID-001"
  grid/islanding-state                        ON_GRID
  grid/grid-state                             UP
  grid/grid-forming-entity                    "GRID"

ebus/5/TG123456789-site-meter/                energy.ebus.device.meter
  info/product-name                           "Site Meter"
  meter/active-power                          -2750.0
  meter/imported-energy                       99828300.0
  meter/exported-energy                       5990700.0

ebus/5/TG123456789-solar-meter/               energy.ebus.device.meter
  info/product-name                           "Solar Meter"
  meter/active-power                          5530.0
  meter/imported-energy                       7300.0
  meter/exported-energy                       33558900.0

ebus/5/TG123456789-load-meter/                energy.ebus.device.meter
  info/product-name                           "Load Meter"
  meter/active-power                          2740.0
  meter/imported-energy                       125308600.0
  meter/exported-energy                       0.0
```

---

## Example: Enphase IQ System

An Enphase system with an IQ Gateway (Envoy), IQ Battery (Encharge), 6 microinverters, and an IQ System Controller with grid relay (NSRB).

### Enphase Component Mapping

| Enphase Component | eBus Device Type | Notes |
|---|---|---|
| IQ Gateway (Envoy) | `energy.ebus.device.bess` (parent) | System gateway, serial from mDNS discovery |
| IQ Battery (Encharge) | `energy.ebus.device.battery` | Per-battery SOC from `/ivp/peb/devstatus` |
| IQ System Controller (ESUB) + NSRB relay | `energy.ebus.device.mid` | Grid relay state from `/ivp/livedata/status` `main_relay_state` |
| Microinverters (PCU) | `energy.ebus.device.inverter` (× N) | Per-inverter power from `/api/v1/production/inverters` |
| Production meter (EIM) | `energy.ebus.device.meter` (solar) | From `/ivp/meters/reports` `reportType: "production"` |
| Net consumption meter (EIM) | `energy.ebus.device.meter` (grid) | From `/ivp/meters/reports` `reportType: "net-consumption"` |
| Total consumption meter (EIM) | `energy.ebus.device.meter` (load) | From `/ivp/meters/reports` `reportType: "total-consumption"` |

### Enphase API → eBus Property Mapping

| Enphase API | Endpoint | eBus Property | Unit Conversion |
|---|---|---|---|
| `meters.soc` | `/ivp/livedata/status` | `soc/soc` | None (already %) — primary source* |
| `meters.storage.agg_p_mw` | `/ivp/livedata/status` | `meter/active-power` | mW → W (÷ 1000) |
| `main_relay_state` | `/ivp/livedata/status` | `grid/islanding-state` | 1 → ON_GRID, 5 → OFF_GRID — primary source** |
| `secctrl.agg_soc` | `/ivp/ensemble/status` | `soc/soc` | None (already %) — fallback source* |
| `relay.mains_oper_state` | `/ivp/ensemble/status` | `grid/islanding-state` | "closed" → ON_GRID, "open" → OFF_GRID — fallback source** |
| `wNow` | `/ivp/meters/reports` | `meter/active-power` | None (already W) |
| `whLifetime` (whDlvdCum) | `/ivp/meters/reports` | `meter/exported-energy` | None (already Wh) |
| `whLifetime` (whRcvdCum) | `/ivp/meters/reports` | `meter/imported-energy` | None (already Wh) |
| `rmsCurrent` | `/ivp/meters/reports` | `meter/current` | None (already A) |
| `rmsVoltage` | `/ivp/meters/reports` | `meter/voltage` | None (already V) |
| `freq` | `/ivp/meters/reports` | `meter/frequency` | None (already Hz) |
| `reactPwr` | `/ivp/meters/reports` | `meter/reactive-power` | None (already var) |
| `apprntPwr` | `/ivp/meters/reports` | `meter/apparent-power` | None (already VA) |
| `pwrFactor` | `/ivp/meters/reports` | `meter/power-factor` | None (already 0–1) |
| `lastReportWatts` | `/api/v1/production/inverters` | `meter/active-power` | None (already W) |
| `serialNumber` | `/inventory.json` | `info/serial-number` | None |

\* SOC is available from two Enphase endpoints. Both report the same aggregate value. The adapter should prefer `meters.soc` from `/ivp/livedata/status` (updates more frequently) and fall back to `secctrl.agg_soc` from `/ivp/ensemble/status` if livedata is unavailable.

\*\* Grid/islanding state is similarly available from two endpoints. Prefer `main_relay_state` from livedata, fall back to `relay.mains_oper_state` from ensemble status.

### Enphase Topic Example

```
ebus/5/202211182691/                              energy.ebus.device.bess (parent)
  info/vendor-name                                "Enphase"
  info/serial-number                              "202211182691"
  info/product-name                               "IQ Gateway"
  info/firmware-version                           "8.2.127"
  info/data-model-version                         "1.0"
  soc/soc                                         72.5
  meter/active-power                              -450.0
  status/communication                            OK
  status/authentication                           OK

ebus/5/202211182691-battery-1/                    energy.ebus.device.battery
  info/vendor-name                                "Enphase"
  info/serial-number                              "ENB-001"
  info/product-name                               "IQ Battery 10"
  info/nameplate-capacity                         10.08
  soc/soc                                         72.5

ebus/5/202211182691-mid/                          energy.ebus.device.mid
  info/vendor-name                                "Enphase"
  info/serial-number                              "202252017752"
  info/product-name                               "IQ System Controller"
  grid/islanding-state                            ON_GRID
  grid/grid-forming-entity                        "GRID"

ebus/5/202211182691-solar-meter/                  energy.ebus.device.meter
  info/product-name                               "Solar Meter"
  meter/active-power                              1354.5
  meter/imported-energy                           0.0
  meter/exported-energy                           10453248.4
  meter/current                                   11.0
  meter/voltage                                   247.3
  meter/frequency                                 60.0
  meter/power-factor                              1.0

ebus/5/202211182691-grid-meter/                   energy.ebus.device.meter
  info/product-name                               "Grid Meter"
  meter/active-power                              -1308.5
  meter/imported-energy                           872827.1
  meter/exported-energy                           9579927.3
  meter/current                                   10.7
  meter/voltage                                   247.2

ebus/5/202211182691-load-meter/                   energy.ebus.device.meter
  info/product-name                               "Load Meter"
  meter/active-power                              46.0
  meter/imported-energy                           872827.1
  meter/exported-energy                           0.0
```

Note: Enphase microinverters (PCU) could optionally be represented as individual `energy.ebus.device.inverter` child devices, each with per-inverter `meter/active-power`. This is MAY — the system-level solar meter provides the aggregate.

---

## Appendix: $description Example

The parent BESS device's `$description` topic publishes a JSON object conforming to the Homie 5 specification. It declares the device's capabilities (nodes), their properties, and child devices.

```json
{
  "name": "Enphase IQ System",
  "type": "energy.ebus.device.bess",
  "version": "2026-04-23T12:00:00Z",
  "children": [
    "202211182691-battery-1",
    "202211182691-mid",
    "202211182691-solar-meter",
    "202211182691-grid-meter",
    "202211182691-load-meter"
  ],
  "nodes": {
    "info": {
      "name": "System information",
      "type": "energy.ebus.capability.info",
      "properties": {
        "vendor-name": {
          "name": "Vendor name",
          "datatype": "string"
        },
        "serial-number": {
          "name": "Serial number",
          "datatype": "string"
        },
        "product-name": {
          "name": "Product name",
          "datatype": "string"
        },
        "firmware-version": {
          "name": "Firmware version",
          "datatype": "string"
        },
        "data-model-version": {
          "name": "Data model version",
          "datatype": "string"
        }
      }
    },
    "soc": {
      "name": "State of charge",
      "type": "energy.ebus.capability.soc",
      "properties": {
        "soc": {
          "name": "State of charge",
          "datatype": "float",
          "unit": "%"
        }
      }
    },
    "meter": {
      "name": "Aggregate battery meter",
      "type": "energy.ebus.capability.meter",
      "properties": {
        "active-power": {
          "name": "Active power",
          "datatype": "float",
          "unit": "W"
        },
        "imported-energy": {
          "name": "Imported energy",
          "datatype": "float",
          "unit": "Wh"
        },
        "exported-energy": {
          "name": "Exported energy",
          "datatype": "float",
          "unit": "Wh"
        }
      }
    },
    "status": {
      "name": "System status",
      "type": "energy.ebus.capability.status",
      "properties": {
        "communication": {
          "name": "Communication status",
          "datatype": "enum",
          "format": "OK,LOST,DEGRADED"
        },
        "authentication": {
          "name": "Authentication status",
          "datatype": "enum",
          "format": "OK,FAILED,EXPIRED,MISSING"
        },
        "discovery": {
          "name": "Discovery status",
          "datatype": "enum",
          "format": "OK,NOT_FOUND,SERIAL_MISMATCH"
        }
      }
    }
  }
}
```

Each child device publishes its own `$description` with its capabilities. A battery child's `$description` would include `info`, `soc`, and `meter` nodes. A MID child would include `info` and `grid`.
