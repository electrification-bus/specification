# Electrification Bus Water Heater Data Model Specification

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-06-20
**Authors:** Don Jackson

## Overview

This document defines an Electrification Bus (eBus for short) data model for a **water heater** — a device that heats and stores domestic hot water, and which (increasingly) participates in grid demand-response as a flexible, dispatchable load. The data model is vendor-neutral and transport-neutral: it describes the water heater as an appliance, not as the artifact of any one control protocol. A heat-pump water heater reporting over a proprietary serial bus, a CTA-2045 water heater behind a Universal Communications Module, and a Matter water heater all map onto the same model.

The model captures the water heater's identity and nameplate, its thermal state (setpoint, tank temperature, operating mode), its electrical metering, its standing as a **dispatchable thermal-storage resource** (how much hot water is stored, how much heating headroom remains), and a vendor-neutral **demand-response control surface** for shedding and loading-up the appliance. It is layered on Homie 5 plus eBus's HEI-specific device and capability types.

Four real control surfaces inform the model and serve as the worked example bindings in [§Examples](#examples): **CTA-2045-B** (the demand-response-minimal floor — a generic shed/load-up interface with no setpoint), an **[ESPHome integration to a Rheem EcoNet heat-pump water heater](https://github.com/esphome-econet/esphome-econet)** (the rich case — setpoint, dual tank temperatures, operating modes, heat-pump internals), **Matter's water-heater clusters** (the emerging-standard case — Water Heater Management, Water Heater Mode, and Device Energy Management), and the **[Cala Systems water heater](https://www.calasystems.com)** (the self-optimizing case — boost-only control plus advisory solar/battery context). Where the model's vocabulary aligns with any of these, the alignment is deliberate; the model is the union of what real water heaters expose, designed so each surface maps cleanly onto it rather than the model copying any one of them.

## Terminology: "water heater"

This document uses **water heater** for the device class — a storage water heater with a tank, whether the heat source is a heat pump, electric-resistance elements, gas combustion, or a hybrid of these. The defining characteristics for this data model are that the device (a) maintains a reservoir of heated water against a setpoint, and (b) is, or may become, a controllable grid-flexible load.

This is distinct from:

- **Tankless (instantaneous) water heaters** — these have no thermal storage and therefore no `soc` capability and a much-reduced demand-response role. A tankless unit MAY publish as an `energy.ebus.device.water-heater` populating only the subset of properties that apply (no tank temperature, no stored-energy); the conformance latitude below permits this.
- **The communications module that proxies a water heater.** A CTA-2045 Universal Communications Module (UCM), an ESPHome bridge, or a cloud-API adapter that republishes a non-eBus-native water heater is a **proxy** — modeled as an `energy.ebus.device.bridge` whose child is the water-heater device (see [`proxy.md`](proxy.md) and [§Proxying and the UCM](#proxying-and-the-ucm)). The module is not itself a water heater.

The data model uses "water heater" in normative prose. Vendor-specific examples may use whichever term the product literature uses ("HPWH", "smart water heater", "grid-enabled water heater", "EcoPort water heater", etc.).

## Audience and Scope

This document is the data-model specification for two audiences:

- **Publishers** — water-heater OEMs implementing the publisher role for their own product, or third parties proxying on behalf of a non-eBus-native water heater (a CTA-2045 UCM adapter, an ESPHome/Home-Assistant integration, a Matter-to-eBus bridge, a vendor-cloud adapter).
- **Consumers** — developers writing controller-role API clients that read water-heater state and issue demand-response commands for energy management, demand response, DERMS coordination, or customer-facing displays.

The model covers:

- The water-heater device, its identity / nameplate, and its capabilities.
- Thermal state and control: setpoint, tank temperature(s), ambient temperature, operating mode, and which heat sources are active.
- The water heater as dispatchable thermal storage: stored-energy state of charge and heating headroom.
- Electrical metering: instantaneous power and cumulative energy.
- A vendor-neutral demand-response control + feedback surface (shed / load-up, with the device's response and customer-override state).
- The water heater's own operational status (faults, component runtimes).

The model does **not** cover:

- **Vendor-specific configuration, provisioning, or firmware update.** Commissioning, Wi-Fi setup, firmware flows, register programming — out of scope.
- **Schedule / time-of-use programming.** An eBus consumer that needs to drive the water heater on a schedule does so by issuing demand-response events over time, or out-of-band; the model publishes current state and accepts current commands, not stored schedules. (This mirrors Matter's "Timed" mode, whose schedule lives in the Thermostat cluster — deferred here to a future revision.)
- **Detailed refrigerant-cycle telemetry** beyond a handful of MAY-level diagnostic temperatures. Full heat-pump cycle analytics belong on a vendor diagnostic channel.

## Design Principles

This data model follows the Electrification Bus design principles — the Homie devices-vs-nodes split, parent aggregation, proxying as a first-class peer to native publishing, property placement on the authoritative device, forward compatibility, and multi-instance modeling. See **[Design Principles in framework.md](../framework.md#design-principles)** for the canonical list.

Two stances shape the property tables that follow:

**Wide conformance latitude.** This data model defines a property **vocabulary**, not a conformance gauntlet. The **vast majority of properties are MAY-level**. A water heater that publishes only `setpoint` and `tank-temperature` is a valid `energy.ebus.device.water-heater`; so is a CTA-2045 unit that publishes no setpoint at all but exposes the full `dr` surface; so is a Rheem-class unit publishing the complete thermal + metering + diagnostics matrix. Publishers populate what they have and omit what they don't (framework principle #3); consumers tolerate sparse publication. The Homie device-type discriminator (`$description.type = energy.ebus.device.water-heater`) is what identifies a device as a water heater — not the population of any specific property. This stance matches the rationale recorded for [`utility-meter.md`](utility-meter.md): the model targets a long tail of appliance OEMs and proxy publishers where any conformance bar above MAY would exclude most candidates.

**The model is the appliance; control protocols are bindings.** The canonical vocabulary is deliberately clean and orthogonal. No control protocol's quirks are adopted into it — instead each protocol is *mapped* onto it, with the mapping shown in [§Examples](#examples). Most consequentially: CTA-2045's 15-value flattened "operational state" enum is **not** adopted; it is decomposed into the orthogonal properties this model already defines (a demand-response response value, a heating-active indication, and a customer-override boolean), and the 15 states map onto that decomposition losslessly.

---

## Water Heater Device

**Type:** `energy.ebus.device.water-heater`

The water-heater device represents the appliance itself. It has no eBus-modeled child devices; per-position tank temperatures are recorded as property-name suffixes on the `water-heater` capability node (see [§Per-position representation](#per-position-representation)).

```
ebus/5/<wh-id>/                  energy.ebus.device.water-heater
  info                  Identity and nameplate
  water-heater          Thermal state and control (setpoint, tank temps, mode)
  soc                   Dispatchable thermal storage (state of charge, headroom)   (when published)
  meter                 Instantaneous power + cumulative energy                    (when published)
  dr                    Demand-response control + feedback                         (when DR-capable)
  status                Operational state (faults, runtimes)                       (when published)
```

`info` is always present on a conformant water-heater device. `water-heater` is present on any device that maintains a setpoint or reports a tank temperature (i.e., essentially all storage water heaters). The remaining capabilities are populated when the device exposes the corresponding signals: `soc` when it reports stored-energy or tank percentage, `meter` when it measures its own power/energy, `dr` when it is controllable for demand response, `status` when it reports operational health.

### Device ID

The device ID is publisher-defined and opaque to consumers. Common conventions are the manufacturer serial number, a UUID assigned at commissioning, or — for a proxied device — the `{proxier-id}-{proxied-id}` form defined in [`proxy.md`](proxy.md). The data model places no constraint on the form. The device ID is the value of `<wh-id>` in topic paths.

### Per-position representation

A storage tank stratifies — hot water rests above cooler water, so a single tank often carries multiple temperature probes at different heights. Per-position tank temperatures use **property-name suffixes** — `-top`, `-bottom` (and `-middle` where a third probe exists) — rather than position-as-child-device. This reuses the per-phase-suffix precedent from [`utility-meter.md`](utility-meter.md) and [`distribution-enclosure.md`](distribution-enclosure.md). A representative/average tank temperature carries no suffix (`tank-temperature`).

The suffixes denote probe positions along the tank's vertical axis. A water heater with a single probe populates only `tank-temperature`. One with upper and lower probes populates `tank-temperature-top` and `tank-temperature-bottom` (and MAY also publish a representative `tank-temperature`). Matter's per-probe Temperature Sensor endpoints (tagged Top / Middle / Bottom from the Common Position namespace) collapse onto these suffixes.

**Why suffixes rather than probe-as-child-device.** A water heater is one physical appliance — one serial number, one firmware, one Homie `$state` lifecycle. Tank probes are sensors within it, not sub-entities. Using the heavyweight Homie device boundary for probe decomposition would import that weight where it does not pay for itself and break the colocation of the representative temperature with its per-position decomposition. Same decision and rationale as the utility-meter per-phase case.

### Water Heater Capabilities

#### info

Identity and nameplate properties. The standard Homie identity properties are reused from the eBus convention; water-heater-specific nameplate properties are added below them.

**Node type:** `energy.ebus.capability.info`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `vendor-name` | string | — | MAY | Manufacturer (e.g., `"Rheem"`, `"A. O. Smith"`, `"Bradford White"`). |
| `serial-number` | string | — | MAY | Appliance serial number. |
| `model` | string | — | MAY | Vendor-defined model identifier (e.g., `"PROPH50 T2 RH350 DCB"`). |
| `hardware-version` | string | — | MAY | Hardware revision. |
| `firmware-version` | string | — | MAY | Firmware version. |
| `data-model-version` | string | — | MAY | Version of the eBus water-heater data model this device publishes (e.g., `"0.1"`). |
| `fuel-type` | enum | — | MAY | Primary energy source: `ELECTRIC`, `GAS`, `HEAT_PUMP`, `HYBRID`, `OTHER`. `HYBRID` denotes a unit with both a heat pump and electric-resistance backup. |
| `heat-sources` | string | — | MAY | Comma-separated set of the heat sources the unit *can* call on, drawn from the vocabulary `HEAT_PUMP`, `RESISTANCE_UPPER`, `RESISTANCE_LOWER`, `RESISTANCE`, `GAS`, `OTHER` (e.g., `"HEAT_PUMP,RESISTANCE_UPPER,RESISTANCE_LOWER"`). Mirrors Matter's `HeaterTypes`. Which of these are *currently firing* is reported by `water-heater`/`heat-demand`. |
| `tank-volume` | float | L | MAY | Nominal tank capacity in litres. (A "50 gallon" unit publishes `≈189`.) Enables an energy manager to estimate heating energy. |
| `nameplate-power` | float | W | MAY | Rated maximum electrical power draw. |

Publishers MAY add vendor-specific informational properties to `info`; the spec defines only the properties listed above.

#### water-heater

Thermal state and the primary control surface — the setpoint, tank temperature(s), ambient temperature, the operating mode, and which heat sources are active. This is the appliance-specific capability.

**Node type:** `energy.ebus.capability.water-heater`

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `setpoint` | float | °C | MAY | yes | Target hot-water temperature. Settable where the publisher permits remote setpoint control. (CTA-2045 water heaters have no setpoint and omit this; Rheem and Matter water heaters publish it.) |
| `setpoint-min` | float | °C | MAY | — | Lowest settable setpoint (Matter `MinHeatSetpointLimit`). |
| `setpoint-max` | float | °C | MAY | — | Highest settable setpoint (Matter `MaxHeatSetpointLimit`). |
| `tank-temperature` | float | °C | MAY | — | Representative / average stored-water temperature. |
| `tank-temperature-{top,middle,bottom}` | float | °C | MAY | — | Per-position tank temperature at the named probe height (see [§Per-position representation](#per-position-representation)). |
| `ambient-temperature` | float | °C | MAY | — | Air temperature around the unit. Relevant to heat-pump efficiency. |
| `delivery-temperature` | float | °C | MAY | — | Temperature of the water currently being delivered at the outlet, when separately sensed — distinct from the stored tank temperatures. (Cala reports this as `delivery_c`.) |
| `operating-mode` | enum | — | MAY | yes | Heat-source / efficiency strategy: `OFF`, `HEAT_PUMP`, `ELECTRIC`, `HYBRID`, `HIGH_DEMAND`, `ENERGY_SAVER`, `VACATION`. `HEAT_PUMP` = heat-pump only (most efficient, slowest recovery); `ELECTRIC` = resistance only; `HYBRID` = automatic blend; `HIGH_DEMAND` = maximum recovery (all sources); `ENERGY_SAVER` = efficiency-biased; `VACATION` = minimal maintenance heating; `OFF` = not maintaining temperature. Publishers MAY extend the value space via Homie `$format` for vendor-specific modes. |
| `heat-demand` | string | — | MAY | — | Comma-separated set of heat sources *currently firing*, drawn from the `heat-sources` vocabulary; empty or absent means the unit is not heating. Mirrors Matter's `HeatDemand`. A consumer that only needs a boolean "is heating now" treats any non-empty value as true. |
| `water-flow` | float | L/min | MAY | — | Current hot-water draw — the outlet flow rate — when the unit meters it. (Cala reports this as `liters_used`.) |

The mapping between this model's `operating-mode` and any specific product's modes is in the example bindings. Matter separates *structural* mode (Off / Manual = hold-setpoint / Timed = schedule) from *preference* tags; this model folds the user-facing strategy into `operating-mode` and carries the setpoint as its own property, deferring schedule (Timed) handling to a future revision.

**Units.** Temperatures are °C throughout (SI; matches Matter and the rest of eBus). A publisher whose device reports °F converts at the edge.

#### soc

The water heater as a **dispatchable thermal-storage resource**. A tank of hot water is a thermal battery: it stores energy (heated water), can be "charged" (load-up / boost — heat now to store more) and "discharged" (shed — coast, letting stored heat be drawn down). This capability exposes that storage view. Published when the device reports stored-energy or tank-percentage; omitted otherwise.

**Node type:** `energy.ebus.capability.soc`

This is the same capability type used for batteries on BESS devices, reused here because a water heater and a battery are publishing the same conceptual signal — the charge state of an energy reservoir — and an energy coordinator benefits from treating a fleet of water heaters as aggregated flexible storage using one vocabulary. All properties are **read-only** (device-reported), as on a BESS.

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `soc` | float | % | MAY | State of charge — approximate fraction of the tank that is hot water (Matter `TankPercentage`). Conceptually the same quantity as the BESS `soc`, and — being a dimensionless ratio — directly comparable across both. For a stratified tank, the height of the hot layer; for a single-probe unit, derivable from temperature. `0` = fully drawn down, `100` = fully heated to setpoint. |
| `soe` | float | Wh | MAY | State of energy — *thermal* energy currently stored and available to draw. The conceptual analogue of the BESS `soe`, but a different physical quantity (see note below): a water heater stores heat, not electricity. |
| `available-volume` | float | L | MAY | The stored-hot-water quantity expressed as usable *volume* — often the more natural measure for a water heater, and the one Cala reports (`liters_available`). The volumetric companion to `soe`. |
| `total-energy-storage` | float | Wh | MAY | Total thermal storage capacity — the thermal energy to move the tank from its minimum to its maximum operating temperature (CTA-2045 "Total Energy Storage"). |
| `loadup-headroom` | float | Wh | MAY | Thermal energy the tank can absorb *now* — the present load-up (charging) headroom, ≈ `total-energy-storage − soe` (CTA-2045 "Present Energy Storage", i.e. its energy-*take* capacity). When over-heating is permitted it includes the extra beyond the normal maximum (CTA-2045 Advanced Load Up; the gap to Matter `Boost` `TargetPercentage`). The dispatchable charge a load-up event can absorb. |
| `heat-required` | float | Wh | MAY | Estimated thermal energy needed to bring the tank to its target setpoint (Matter `EstimatedHeatRequired`). The *electrical* energy is lower by the heat source's COP. |

**Two opposite quantities.** `soc` / `soe` / `available-volume` describe how much hot water is **stored and available to draw** (the discharge side); `loadup-headroom` describes how much energy the tank can still **absorb** (the charge side). They are complementary — roughly `soe + loadup-headroom ≈ total-energy-storage`.

**Thermal, not electrical — the BESS analogy is conceptual, not dimensional.** A water heater's stored energy is *thermal* (Wh of heat, or equivalently a hot-water volume); a battery's `soe` is *electrical* (the kWh it can discharge to the grid). These are **not** the same unit and **not** directly summable: a water heater can shift *when* it draws electrical power (load-shifting), but it cannot discharge electricity. The `soc` ratio is comparable across both; the stored-energy magnitudes are not. This model expresses the water heater's thermal quantities in Wh (matching CTA-2045 and the device's own `meter`), where the BESS expresses electrical energy in kWh — deliberately different units for different physical quantities. The heat source's COP (≈1 for resistance, ≈2–4 for a heat pump) relates these thermal quantities to the electrical energy a controller actually dispatches; the COP is out of scope for this capability.

#### meter

Instantaneous electrical power and cumulative energy. Reused from the eBus `meter` capability; a water heater populates the small subset below.

**Node type:** `energy.ebus.capability.meter`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `active-power` | float | W | MAY | Present electrical power draw. Positive = consuming. |
| `imported-energy` | float | Wh | MAY | Cumulative electrical energy consumed. Monotonically non-decreasing in normal operation. |

A water heater MAY publish additional `meter` properties (voltage, current) defined by the `meter` capability; most do not, and the conformance latitude permits omission.

#### dr

The vendor-neutral **demand-response control and feedback** surface — the heart of a grid-flexible water heater. A controller issues a demand-response *event* (shed the load, or load it up), and the device reports how it is responding and whether the customer has overridden. Published when the device is controllable for demand response; omitted otherwise.

**Node type:** `energy.ebus.capability.dr`

This capability is defined here in the water-heater context but is **cross-cutting and publisher-agnostic**: any controllable flexible load (a future HVAC SGD, an EV charger, a pool pump) MAY expose it. The property contracts below apply unchanged to any such publisher.

**The control direction is first-class.** Demand response on a storage appliance has two opposite intents relative to the appliance's self-managed baseline: **shed** (curtail below baseline — the grid is stressed; ≈ let the thermal battery discharge) and **load-up** (drive above baseline — surplus/cheap energy is available; ≈ charge the thermal battery). These are opposite directions, not points on one "throttle" axis. A magnitude (*how much*, for variable-power devices) and an intensity (*how aggressive / how mandatory*) modify the chosen direction.

| Property ID | Datatype | Unit | Req | Settable | Description |
|---|---|---|---|---|---|
| `event` | json | — | MAY | yes | The demand-response event to apply, as one atomic object (see schema below). Setting this property issues the event; the publisher translates it to the device's native control protocol. |
| `active-event` | json | — | MAY | — | The event currently in force (same shape as `event`) plus an `ends-at` timestamp, or null/absent when no event is active. |
| `dr-response` | enum | — | MAY | — | How the device is currently responding to demand-response control: `NONE` (no event in effect), `CURTAILED` (shedding — reduced consumption per a shed event), `BOOSTED` (loading up — heightened consumption per a load-up event), `NOT_FOLLOWING` (an event is in effect but the device is not currently able to honor it). This is the decomposed, vendor-neutral replacement for CTA-2045's 15-value operational-state enum (see [§CTA-2045 binding](#example-cta-2045-water-heater-via-a-ucm-bridge)). |
| `opted-out` | boolean | — | MAY | — | True when the customer has overridden demand-response participation (e.g., the appliance's "Grid Enabled" control is off). While `true`, the device may ignore or only partially honor events. Many devices auto-clear this after a fixed period. |
| `throttle-granularity` | enum | — | MAY | — | The magnitude resolution the device honors for `event.level`: `BINARY` (on/off only — `level` ignored, shed = off), `DISCRETE` (a fixed set of steps), `CONTINUOUS` (any 0–100%). Derived from the device's variable-power capability. A controller reads this to know whether a `level` of `45` is honored or rounded. |

**`event` object schema.** A settable Homie 5 `json` property (with `$format` JSONSchema); one `/set` carries the whole event atomically.

```json
{
  "mode":        "SHED" | "LOAD_UP" | "NORMAL",     // direction; required. NORMAL ends any event.
  "level":       0-100,                              // optional %: magnitude within the direction
                                                     //   (variable-power devices only; see throttle-granularity)
  "intensity":   "PEAK" | "EMERGENCY" | "ADVANCED",  // optional: aggressiveness within the direction
  "duration":    <seconds>,                          // optional: event length; absent = until changed
  "target-percentage":   0-100,                      // optional (LOAD_UP): heat until soc reaches this
  "temporary-setpoint":  <°C>                        // optional (LOAD_UP): heat to this setpoint for the event
}
```

- `mode` is the direction. `SHED` reduces consumption; `LOAD_UP` increases it; `NORMAL` ends any active event and returns the device to self-management.
- `level` is the per-direction magnitude as a percentage, honored only to the resolution given by `throttle-granularity`.
- `intensity` raises the aggressiveness of the chosen direction. On the shed side: `PEAK` (a critical-peak event — deeper curtailment) and `EMERGENCY` (a grid-emergency event — maximum curtailment, customer override discouraged). On the load-up side: `ADVANCED` (over-heat the tank beyond its normal maximum to store extra energy; corresponds to CTA-2045 Advanced Load Up and Matter `EmergencyBoost`, and is gated on the customer having enabled it).
- `target-percentage` and `temporary-setpoint` are optional LOAD_UP refinements drawn from Matter's `Boost` command, letting a controller load up to a specific tank state or temperature rather than for a fixed duration. Devices that do not support them ignore them.

**Authorization.** The `event` property is the only settable on a conformant water-heater device's demand-response surface (alongside `water-heater`/`setpoint` and `operating-mode`). A consumer issuing demand response needs write access only to `dr/event`.

#### status

Operational health — faults and, where the device exposes them, component runtimes and diagnostic temperatures. Reused from the eBus `status` capability.

**Node type:** `energy.ebus.capability.status`

| Property ID | Datatype | Unit | Req | Description |
|---|---|---|---|---|
| `fault-state` | enum | — | MAY | Overall fault state: `OK`, `FAULT`, `UNKNOWN`. Publishers MAY extend via `$format` for device-specific fault categories. |
| `active-alerts` | string | — | MAY | Human-readable current alert(s), when the device exposes them. |
| `compressor-runtime` | float | h | MAY | Cumulative heat-pump compressor running hours (maintenance/diagnostics). |
| `resistance-runtime-{upper,lower}` | float | h | MAY | Cumulative resistance-element running hours. |

Publishers MAY add vendor-specific diagnostic properties (refrigerant-cycle temperatures such as evaporator / discharge / suction, fan speed, expansion-valve position, etc.) as additional `status` properties; the spec defines only the properties listed above. Such deep diagnostics are entirely MAY and outside the model's core.

---

## Proxying and the UCM

A water heater that is not yet eBus-native is published by a **proxy** per [`proxy.md`](proxy.md). The proxy is modeled as an `energy.ebus.device.bridge`, and the water-heater device is its child, named `{bridge-id}-{wh-id}`.

The CTA-2045 case is the canonical example. A CTA-2045 **Universal Communications Module (UCM)** plugs into the water heater's CTA-2045 socket and bridges it to a network. In eBus terms the UCM is **just a bridge** — `energy.ebus.device.bridge` — with the water heater as its child. The UCM carries no water-heater capabilities of its own; its identity lives on the bridge's `info`. Two communication links are involved, and each is reported by whichever party can authoritatively observe it — reusing established eBus conventions rather than new properties:

- **UCM ↔ water heater (the CTA-2045 socket)** — the proxier's *downstream* view of link health to the device it proxies — on the bridge's `connection` capability as `feeds-device-status` (`OK` / `LOST` / `DEGRADED`), alongside `feeds-device-id` / `feeds-device-type` identifying the proxied child. The bridge is the *surviving observer* of this link (it still reaches the network when the socket drops), so it is the right reporter. This is the same property an enclosure uses for its view of a commissioned DER it polls (see [`distribution-enclosure.md`](distribution-enclosure.md) §`connection`), and it is where [`proxy.md`](proxy.md) places proxy-side link-health: on the proxier, not the proxied child.
- **UCM ↔ network (the UCM's upward link)** — reported by **the other side of that link**, not self-asserted by the bridge. A device whose uplink is down cannot reliably announce its own disconnection over that same dead link, so the authoritative reporter is whoever the UCM connects up to *and stays connected to observe it*: an upstream eBus device that hosts or consumes the UCM reports its view via **its own** `connection/feeds-device-status` pointing at the UCM bridge, and/or the bridge device's Homie `$state` / availability (LWT) surfaces the staleness to consumers. This is the same asymmetry as the enclosure reporting *its* view of a DER it polls rather than the DER self-reporting its uplink to the panel — **the surviving observer reports the link.**

Per that rule the water-heater child carries no link-health property of its own — **"has the UCM lost contact with the water heater?" is answered by the bridge's `connection/feeds-device-status`, the direct analogue of "has the panel lost contact with the BESS?"** — and conversely "has the host lost contact with the UCM?" is answered by the host's view (or the bridge's availability), not by the UCM bridge itself. The precise status/connection surface of a proxy host is governed by [`proxy.md`](proxy.md) and the framework, not by this data model; the properties above are reused illustratively. The UCM is not specialized in the device-type registry: a UCM is a bridge like any other, and nothing in this model depends on recognizing it as CTA-2045-specific. Whether the UCM is in turn hosted by a panel or gateway is an implementation detail invisible to eBus.

The same pattern applies to an ESPHome/Home-Assistant integration bridging a vendor-serial water heater, or a Matter-to-eBus or vendor-cloud adapter. When the water heater (or its vendor) someday publishes natively, the native publication uses the bare `{wh-id}` and consumers prefer it per [`proxy.md`](proxy.md).

---

## Examples

The conformance-latitude principle means valid water-heater publishers vary widely. The following illustrate the three real bindings the model was designed against.

### Example: CTA-2045 water heater via a UCM bridge

A CTA-2045 heat-pump water heater behind a SkyCentrics UCM. CTA-2045's demand-response-minimal surface: **no setpoint, no tank temperature** — only demand response, energy, and the thermal-storage view. The UCM is a `bridge`; the water heater is its child.

```
ebus/5/ucm-20f85e/$description.type              = energy.ebus.device.bridge
ebus/5/ucm-20f85e/$state                         = ready       # bridge liveness (LWT → lost on uplink failure)
ebus/5/ucm-20f85e/info/vendor-name               = "SkyCentrics"
ebus/5/ucm-20f85e/info/firmware-version          = "CEA-2045AC-0.2.22"
ebus/5/ucm-20f85e/connection/feeds-device-id     = "ucm-20f85e-wh01"
ebus/5/ucm-20f85e/connection/feeds-device-type   = "energy.ebus.device.water-heater"
ebus/5/ucm-20f85e/connection/feeds-device-status = "OK"        # UCM ↔ water heater (CTA-2045 socket; bridge is surviving observer)

ebus/5/ucm-20f85e-wh01/$description.type        = energy.ebus.device.water-heater
ebus/5/ucm-20f85e-wh01/info/fuel-type           = "HEAT_PUMP"
ebus/5/ucm-20f85e-wh01/meter/active-power       = 421.0
ebus/5/ucm-20f85e-wh01/meter/imported-energy    = 2709860
ebus/5/ucm-20f85e-wh01/soc/soe                  = 2400
ebus/5/ucm-20f85e-wh01/soc/total-energy-storage = 9200
ebus/5/ucm-20f85e-wh01/soc/loadup-headroom      = 6800
ebus/5/ucm-20f85e-wh01/dr/throttle-granularity  = "DISCRETE"
ebus/5/ucm-20f85e-wh01/dr/dr-response           = "NONE"
ebus/5/ucm-20f85e-wh01/dr/opted-out             = false
```

A controller sheds this water heater for one hour by setting:

```
ebus/5/ucm-20f85e-wh01/dr/event/set = {"mode":"SHED","duration":3600}
```

The publisher encodes a CTA-2045 Shed (`0x01`) with the duration field; `dr/dr-response` transitions to `CURTAILED`. A critical-peak event is `{"mode":"SHED","intensity":"PEAK",...}` (CTA-2045 `0x0A`); a grid emergency is `intensity:"EMERGENCY"` (`0x0B`); a load-up is `{"mode":"LOAD_UP","duration":2700}` (`0x17`).

**CTA-2045 operational-state → model mapping.** CTA-2045's 15 operational states are a flattened cross-product of three orthogonal facts; they decompose losslessly onto this model's properties:

| CTA-2045 state | `meter/active-power` | `dr/dr-response` | `dr/opted-out` | `status/fault-state` |
|---|---|---|---|---|
| Idle Normal / Running Normal | ~0 / >0 | `NONE` | false | OK |
| Idle Curtailed / Running Curtailed | ~0 / >0 | `CURTAILED` | false | OK |
| Idle Heightened / Running Heightened | ~0 / >0 | `BOOSTED` | false | OK |
| Idle Opted Out / Running Opted Out | ~0 / >0 | `NONE` | **true** | OK |
| Variable Following / Not Following | — | `BOOSTED`-or-`CURTAILED` / `NOT_FOLLOWING` | false | OK |
| SGD Error | — | — | — | **FAULT** |

### Example: Rheem EcoNet heat-pump water heater (rich)

A Rheem EcoNet HPWH — the rich case, publishing the full thermal + metering + storage surface (as exposed by the [esphome-econet](https://github.com/esphome-econet/esphome-econet) integration). The device ID derives from the appliance serial in Homie form: `q242051522` (the reported serial `Q242051522`, lowercased). Shown here with that bare ID, as a native publisher would use it; an esphome-econet bridge proxying the unit would instead prefix its own ID per the [`proxy.md`](proxy.md) convention (`{bridge-id}-q242051522`).

```
ebus/5/q242051522/$description.type                    = energy.ebus.device.water-heater
ebus/5/q242051522/info/vendor-name                     = "Rheem"
ebus/5/q242051522/info/model                           = "PROPH50 T2 RH350 DCB"
ebus/5/q242051522/info/serial-number                   = "Q242051522"
ebus/5/q242051522/info/firmware-version                = "WH-HPW4-H3-01-36"
ebus/5/q242051522/info/fuel-type                       = "HYBRID"
ebus/5/q242051522/info/heat-sources                    = "HEAT_PUMP,RESISTANCE_UPPER,RESISTANCE_LOWER"
ebus/5/q242051522/info/tank-volume                     = 189
ebus/5/q242051522/water-heater/setpoint                = 52
ebus/5/q242051522/water-heater/tank-temperature-top    = 49.9
ebus/5/q242051522/water-heater/tank-temperature-bottom = 46.8
ebus/5/q242051522/water-heater/ambient-temperature     = 19.4
ebus/5/q242051522/water-heater/operating-mode          = "ENERGY_SAVER"
ebus/5/q242051522/water-heater/heat-demand             = ""
ebus/5/q242051522/soc/soc                              = 71
ebus/5/q242051522/meter/active-power                   = 116.2
ebus/5/q242051522/meter/imported-energy                = 2709860
ebus/5/q242051522/status/fault-state                   = "OK"
ebus/5/q242051522/status/compressor-runtime            = 1840.5
```

A customer (or controller) raises the setpoint:

```
ebus/5/q242051522/water-heater/setpoint/set = 54
```

Rheem's product modes map to `operating-mode`: Heat Pump → `HEAT_PUMP`, Electric → `ELECTRIC`, Energy Saver → `ENERGY_SAVER`, High Demand → `HIGH_DEMAND`, Vacation → `VACATION`, Off → `OFF`.

### Example: Matter water heater

A Matter water heater (device type `0x050F`) bridged to eBus. The mapping from Matter clusters onto this model:

| Matter source | eBus property |
|---|---|
| Thermostat `OccupiedHeatingSetpoint` | `water-heater/setpoint` |
| Thermostat `LocalTemperature` / per-probe Temperature Sensor endpoints (Top/Bottom tags) | `water-heater/tank-temperature[-top/-bottom]` |
| Water Heater Mode (Off/Manual/Timed + tags) | `water-heater/operating-mode` |
| Water Heater Management `HeaterTypes` / `HeatDemand` | `info/heat-sources` / `water-heater/heat-demand` |
| Water Heater Management `TankVolume` | `info/tank-volume` |
| Water Heater Management `TankPercentage` | `soc/soc` |
| Water Heater Management `EstimatedHeatRequired` | `soc/heat-required` |
| Water Heater Management `Boost(BoostInfo)` / `CancelBoost` | `dr/event = {mode:LOAD_UP, duration, target-percentage, temporary-setpoint}` / `{mode:NORMAL}` |
| Water Heater Management `BoostState` | `dr/dr-response` (`BOOSTED` when Active) |
| Device Energy Management (power-adjust / pause) | `dr/event = {mode:SHED, ...}` |
| Electrical Power / Energy Measurement | `meter/active-power` / `meter/imported-energy` |

Matter splits the two demand-response directions across two clusters — load-up is the Water Heater Management `Boost` command, shed is delegated to Device Energy Management — whereas this model unifies them under `dr/event`'s `mode`. Matter's `Boost` is a rich load-up (target tank percentage, temporary setpoint, reheat hysteresis); the `dr/event` object carries the same optional refinements, so the eBus surface is a superset.

### Example: Cala Systems water heater

A [Cala Systems](https://www.calasystems.com) heat-pump water heater. Its control model is the most restrictive of the four — and the most instructive: it accepts **only** a boost (load-up) command, never a shed, and otherwise self-optimizes from *advisory* solar/battery context. The mapping of Cala's observed quantities and controls onto this model:

| Cala signal / control | eBus property |
|---|---|
| `top_c` / `upper_c` / `lower_c` | `water-heater/tank-temperature-{top,middle,bottom}` |
| `delivery_c` | `water-heater/delivery-temperature` |
| `ambient_c` | `water-heater/ambient-temperature` |
| `liters_available` | `soc/available-volume` |
| `upper_element_on` / `lower_element_on` / compressor running | `water-heater/heat-demand` (`RESISTANCE_UPPER` / `RESISTANCE_LOWER` / `HEAT_PUMP`) |
| `energy_used_kwh` (per-minute) | `meter/active-power` (and cumulative `meter/imported-energy`) |
| `liters_used` | `water-heater/water-flow` |
| `compressor_hz`, `fan_on`, `fan_speed_high` | `status` diagnostics (MAY) |
| `wifi_rssi_dbm`, `fw_version`, connection state | bridge `info` / availability |
| `create_boost {hours}` / `cancel_boost` | `dr/event = {mode:LOAD_UP, duration}` / `{mode:NORMAL}` |
| `boost_mode_on` | `dr/dr-response` (`BOOSTED` when on) |

A Cala-style water heater exposes `dr/event` supporting only `LOAD_UP` and `NORMAL` — no shed, no `level`, `throttle-granularity` absent. This is conformant: the latitude lets a publisher expose only the demand-response directions it implements. Its liveness follows the surviving-observer rule — when the device stops reporting, the bridge (not the device) marks it stale.

**Advisory context, the eBus way.** Cala feeds the device advisory solar production and battery state-of-charge so it can self-optimize (heat when local generation is surplus), accepting no direct control over it. In eBus this needs **no new water-heater property**: a self-optimizing water heater is simply a *consumer* of other devices' published capabilities — the PV inverter's `meter`, the BESS's `soc`, the utility meter's `doe` — and decides locally. Which devices it watches is a commissioning concern (framework territory), not a property on the water heater.

---

## Registry impact

This data model introduces entries in the eBus registries:

- `energy.ebus.device.water-heater` — **new** device type. A storage water heater (heat-pump, electric, gas, or hybrid) as a controllable grid-flexible load. Registered in [`registries/device-types.md`](../registries/device-types.md).
- `energy.ebus.capability.water-heater` — **new** capability type. Water-heater thermal state and control (setpoint, tank temperatures, operating mode, heat demand).
- `energy.ebus.capability.dr` — **new** capability type. Vendor-neutral demand-response control + feedback (direction-first shed / load-up event, response, customer-override). Cross-cutting — applicable to any controllable flexible load.
- `energy.ebus.capability.soc` — reused (its `soc` / `soe` vocabulary) for the water heater's dispatchable thermal storage: state of charge (`soc`), stored *thermal* energy (`soe`), an `available-volume` companion, total capacity, and load-up headroom. The BESS and water-heater publishers populate overlapping but distinct property subsets; both are conformant. The energy quantities differ in physical kind (the water heater's are thermal, the BESS's electrical) and unit, but the `soc` ratio and the `soc`/`soe` property names are shared.
- `energy.ebus.capability.meter`, `energy.ebus.capability.info`, `energy.ebus.capability.status` — reused unchanged.

The new identifiers are registered in [`registries/capability-types.md`](../registries/capability-types.md) and [`registries/device-types.md`](../registries/device-types.md) with Source links pointing to this data model.

---

## References

- [Electrification Bus framework specification](../framework.md)
- [Electrification Bus design principles](../framework.md#design-principles)
- [Electrification Bus proxy model](proxy.md) — for the bridge / proxied-device convention used by the UCM and other water-heater proxies.
- [Electrification Bus utility-meter data model](utility-meter.md) — for the conformance-latitude stance and the per-position property-suffix precedent.
- [Electrification Bus distribution-enclosure data model](distribution-enclosure.md) — for the `meter`, `soc`, `status`, and per-line-suffix precedents.
- [Electrification Bus capability-type registry](../registries/capability-types.md) and [device-type registry](../registries/device-types.md).
- ANSI/CTA-2045-B (2022) — Modular Communications Interface for Energy Management. Source of the demand-response command set (shed, load-up, critical peak, grid emergency, power level), the operational-state vocabulary mapped in the CTA-2045 example, and the energy-storage / energy-take quantities mapped onto `soc`.
- California Title 24 / Joint Appendix JA-13 — the regulatory driver for water-heater load-shifting; defines the light / deep / full shed levels and the basic / advanced load-up energy-shift requirements.
- EcoPort — the water-heater-industry certification brand for CTA-2045 water heaters.
- [esphome-econet](https://github.com/esphome-econet/esphome-econet) — open-source ESPHome component for Rheem / Ruud EcoNet water heaters (and EcoNet HVAC), communicating over the appliance's RS-485 bus. The integration informing the Rheem EcoNet example binding (`info`, `water-heater`, `soc`, `meter`, `status` property mappings).
- [Cala Systems](https://www.calasystems.com) — heat-pump water heater; its `cala-home-assistant` integration is the source of the Cala example binding and of the `delivery-temperature`, `available-volume`, and `water-flow` properties.
- Matter — the water-heater device type and clusters that inform the Matter example binding, published by the Connectivity Standards Alliance:
  - Water Heater device type (`0x050F`) — Matter Device Library; composes the clusters below.
  - Water Heater Management cluster (`0x0094`) — heat sources, tank volume / percentage, estimated heat required, `Boost` / `CancelBoost`.
  - Water Heater Mode cluster (`0x009E`) — operating modes (Off / Manual / Timed plus preference tags).
  - Thermostat cluster (`0x0201`) — setpoint, setpoint limits, current temperature, schedule.
  - Device Energy Management cluster (`0x0098`) — demand-response / flexibility (the shed side of `dr`).
  - Electrical Power Measurement (`0x0090`) and Electrical Energy Measurement (`0x0091`) — power and cumulative energy.
