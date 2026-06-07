# Circuit Tag Registry

**Status:** DRAFT v0.1
**Date:** 2026-05-23
**Authors:** Don Jackson

## Purpose

The eBus distribution-enclosure data model exposes a per-circuit `info/tags` property on circuit child devices — a multi-valued, comma-separated string drawn from the controlled vocabulary defined here. Each tag identifies a category of load that is physically connected to the circuit.

This document is the registry of currently-defined tag values. It is descriptive, not exhaustive: new tags may be added as the integrator ecosystem requires, without a schema change. Consumers MUST tolerate unknown tag values (e.g., display as raw strings, ignore for categorization).

**Applicability beyond circuits.** The registry's primary application is the circuit `info/tags` property, and the file is named accordingly. But the underlying pattern — a controlled vocabulary classifying what is on the downstream side of a connection-point device that the spec doesn't model as a structured eBus device — generalizes naturally. Other data-model documents MAY adopt this same vocabulary on their own `info/tags` properties when they have analogous use cases (for example, a feedthrough-lugs device feeding a non-eBus subpanel could carry `SUBPANEL`; a future power-distribution-unit data model could use per-outlet load tags; an MID grid-side interconnection could use a service-context tag). New tags required by such uses extend this registry rather than forming separate registries — keeping one shared vocabulary across all connection-point devices.

**What `info/tags` does not cover.** The distribution-enclosure data model carries circuit-level metadata that is orthogonal to load identification, and which `info/tags` deliberately does not duplicate:

- Single-load vs mixed-load circuits → `info`'s `dedicated` boolean property
- Load-shedding policy and priority → `priority` (`shed-priority`, `relay-controllable`, `pcs-priority`)
- What is wired upstream / downstream of the circuit, including chained enclosures → `connection` (`feeds-*` and `fed-by-*` triplets, with `feeds-device-type` discriminating eBus device classes)

This registry covers only "what kind of load is on the circuit."

## Format rules

Tag values are semantically Homie enum values — `info/tags` is multi-valued, but each individual tag is drawn from the enum vocabulary defined here. The case convention matches Homie's existing enum convention (`OK`, `LOST`, `DEGRADED` on `status`; `ON_GRID`, `OFF_GRID` on `grid`).

- Tags are SCREAMING_SNAKE_CASE ASCII strings: uppercase letters, digits, and underscores only.
- No leading or trailing underscores; no consecutive underscores.
- No spaces, no hyphens, no mixed case.
- A circuit's `info/tags` value is a comma-separated list of tag strings; individual tag strings do not contain commas (by the rule above).
- Tags are case-sensitive when compared; producers and consumers MUST emit and match the exact strings defined here.

## Naming conventions

Two patterns appear in this registry:

**Descriptor-first** for named equipment classes. The descriptor narrows a broader noun. Examples: `WATER_HEATER`, `POOL_HEATER`, `HEAT_PUMP`, `SUMP_PUMP`, `WELL_PUMP`. Reads as the natural English noun phrase.

**Family-first with sub-type suffix** when a tag refines a family that is itself a valid umbrella tag. Form: `{FAMILY}_{SUBTYPE}`. The family stem remains valid for installations where the sub-type is unknown or not differentiated. Examples: `LIGHTING` + `LIGHTING_INTERIOR` / `LIGHTING_EXTERIOR`; `COOKTOP` + `COOKTOP_INDUCTION` / `COOKTOP_RESISTIVE` / `COOKTOP_GAS`; `RANGE` + `RANGE_INDUCTION` / `RANGE_RESISTIVE` / `RANGE_GAS`; `VENTILATION_FAN` + `VENTILATION_FAN_WHOLE_HOUSE`; `HUMIDIFIER` + `HUMIDIFIER_WHOLE_HOUSE`. Enables prefix-matching queries.

`WHOLE_HOUSE` denotes variants serving the entire home (typically hardwired, central, in-duct) as distinguished from portable or plug-in variants of the same equipment.

## Currently-defined tags

Grouped into categories for readability. Categories are descriptive only — they are not part of the published value and consumers do not need to know about them.

### EV Charging

| Tag | Description | See also |
|---|---|---|
| `EVSE` | Electric Vehicle Supply Equipment (highway-EV, off-road ESV, marine, golf cart, forklift, e-scooter charging dock, etc.) | NEC 625 + 624; IEC 61851 + 62196; SAE J1772; CTA-2045-B SGD 0x1100-0x1103; IEEE 2030.5 DeviceCategoryType bit 17 |
| `EVSE_BIDIRECTIONAL` | Bidirectional / V2X / power-export-capable EVSE | NEC 625 (bidirectional clauses) + 624 (ESVPE) + NEC 705 (interconnection) |

### Lighting

| Tag | Description | See also |
|---|---|---|
| `LIGHTING` | Lighting circuit (sub-type not specified) | EU Ecodesign "Light Sources"; ENERGY STAR |
| `LIGHTING_INTERIOR` | Dedicated interior-lighting circuit (recessed, fixtures, decorative) | IEEE 2030.5 DeviceCategoryType bit 12 |
| `LIGHTING_EXTERIOR` | Dedicated exterior / landscape / facade / security-lighting circuit | IEEE 2030.5 DeviceCategoryType bit 11 |

### HVAC

| Tag | Description | See also |
|---|---|---|
| `HEAT_PUMP` | Heat pump (air-source / ASHP / multi-mode) | IEC 60335-2-40; OmniClass 23-33 17; ENERGY STAR Air-Source Heat Pumps |
| `MINI_SPLIT_AC_HP` | Mini-split AC / heat pump (ductless) | IEC 60335-2-40; IFC SPLITSYSTEM; ENERGY STAR Ductless Heating & Cooling |
| `AC_CONDENSER` | AC condenser (outdoor unit of a central split system) | IEC 60335-2-40; OmniClass 23-33 39 / 43; CTA-2045-B SGD 0x0004-0x0007, 0x001A |
| `GEOTHERMAL` | Geothermal / ground-source heat pump | IEC 60335-2-40 (water-source); ENERGY STAR Geothermal Heat Pumps |
| `AIR_HANDLER` | Air handler (blower, ducted) | IEC 60335-2-40 / 2-102; IFC AIRHANDLER; OmniClass 23-33 25 |
| `FURNACE` | Furnace (electric, gas, oil, propane) | IEC 60335-2-102; NEC 422.12; OmniClass 23-33 13 |
| `BOILER_AND_HYDRONIC_HEAT` | Boiler & hydronic heat (radiator, steam, baseboard hydronic) | IEC 60335-2-102 + 2-51; NEC 422.12; OmniClass 23-33 11 + 15 21; EU Ecodesign Solid Fuel Boilers |
| `HEAT_STRIP` | Heat strip (electric resistance auxiliary heat in an air handler or unit heater) | IEC 60335-2-30; IEEE 2030.5 bit 1 (Strip Heaters) |
| `ELECTRIC_RESISTANCE_HEATER` | Electric resistance heater (baseboard, unit heater, room heater) | IEC 60335-2-30; IEEE 2030.5 bit 2 (Baseboard Heaters); EU Ecodesign Local Space Heaters |
| `ELECTRIC_FLOOR_HEAT` | Electric floor heat (radiant) | IEC 60335-2-96 + 2-106 |
| `DEHUMIDIFIER` | Dehumidifier (whole-house or hardwired) | IEC 60335-2-40; IFC DEHUMIDIFIER; ENERGY STAR Dehumidifiers |
| `HUMIDIFIER_WHOLE_HOUSE` | Whole-house / in-duct humidifier integrated with HVAC | IEC 60335-2-88 |
| `AIR_PURIFIER` | Hardwired whole-house / in-duct air purifier or air cleaner | IEC 60335-2-65; ENERGY STAR Air Cleaners |
| `VENTILATION_FAN` | Ventilation fan umbrella (bathroom fan, attic fan, in-line duct fan, ERV / HRV) | IEC 60335-2-80; OmniClass 23-33 31 19; ENERGY STAR Ventilation Fans |
| `VENTILATION_FAN_WHOLE_HOUSE` | Whole-house propeller fan (attic-mounted, draws outdoor air through windows, exhausts via attic) | — |
| `CEILING_FAN` | Ceiling fan (when on a dedicated circuit, with or without light kit) | OmniClass 23-33 31 19 11 15; ENERGY STAR Ceiling Fans |
| `HVAC` | Other HVAC (fallback when no more specific tag applies) | — |

### Water heating

| Tag | Description | See also |
|---|---|---|
| `WATER_HEATER` | Water heater (sub-type not specified) | IEC 60335-2-21 + 2-35 + 2-73; NEC 422.13; OmniClass 23-31 29; EU Ecodesign Water Heaters |
| `WATER_HEATER_HEAT_PUMP` | Heat pump water heater (HPWH) — uses a heat pump (often with electric resistance backup) to heat a storage tank | IEC 60335-2-21 + 2-40; ENERGY STAR Heat Pump Water Heaters |
| `WATER_HEATER_RESISTIVE` | Electric resistance storage water heater (conventional tank with immersion heating elements) | IEC 60335-2-21 + 2-73 |
| `WATER_HEATER_RESISTIVE_TANKLESS` | Electric resistance tankless / instantaneous water heater — heats water on demand. Very high peak draw (often 80-150 A). | IEC 60335-2-35 |

### Kitchen

| Tag | Description | See also |
|---|---|---|
| `OVEN` | Wall oven (electric resistance) | IEC 60335-2-6; NEC Table 220.55 |
| `COOKTOP` | Cooktop (sub-type not specified) | IEC 60335-2-6 |
| `COOKTOP_INDUCTION` | Induction cooktop (electromagnetic, requires ferromagnetic cookware) | IEC 60335-2-6 |
| `COOKTOP_RESISTIVE` | Electric resistance cooktop (coil or smoothtop radiant) | IEC 60335-2-6; CTA-2045-B SGD 0x0015 (Cook Top — Electric) |
| `RANGE` | Combined oven + cooktop unit (sub-type not specified) | IEC 60335-2-6; NEC Table 220.55 |
| `RANGE_INDUCTION` | Combined oven + induction cooktop | IEC 60335-2-6 |
| `RANGE_RESISTIVE` | Combined oven + electric resistance cooktop | IEC 60335-2-6 |
| `MICROWAVE` | Microwave oven (when on a dedicated circuit; often built-in over-the-range) | IEC 60335-2-25; CTA-2045-B SGD 0x0012 |
| `DISHWASHER` | Dishwasher | IEC 60335-2-5; CTA-2045-B SGD 0x0011; IEEE 2030.5 bit 7 (Smart Appliance); ENERGY STAR |
| `DISPOSAL` | Garbage disposal | IEC 60335-2-16 |
| `HOOD` | Range hood / cooking exhaust | IEC 60335-2-31; OmniClass 23-21 23 43 11; EU Ecodesign Range Hoods |

### Laundry

| Tag | Description | See also |
|---|---|---|
| `WASHER` | Clothes washer (front-load, top-load) | IEC 60335-2-7; CTA-2045-B SGD 0x000C; ENERGY STAR |
| `DRYER` | Clothes dryer (gas, vented electric, condenser, heat pump) | IEC 60335-2-11 + 2-43; CTA-2045-B SGD 0x000D-0x000E, 0x0041; ENERGY STAR |
| `WASHER_DRYER` | Combo washer-dryer (single appliance on one dedicated circuit) | IEC 60335-2-7 + 2-11; EU Ecodesign Washer Dryers |

### Refrigeration

| Tag | Description | See also |
|---|---|---|
| `FRIDGE` | Refrigerator | IEC 60335-2-24; CTA-2045-B SGD 0x000F; ENERGY STAR |
| `FREEZER` | Standalone freezer (chest, upright) | IEC 60335-2-24; CTA-2045-B SGD 0x0010; ENERGY STAR |
| `FRIDGE_FREEZER` | Combined fridge & freezer (single appliance — the residential default) | IEC 60335-2-24; CTA-2045-B SGD 0x000F; OmniClass 23-21 23 33 15 |

### Pumps

| Tag | Description | See also |
|---|---|---|
| `PUMP` | Pump umbrella for circulators (hydronic), filter pumps, booster pumps, aquarium / pond pumps, and "pump sub-type unknown" fallback | IEC 60335-2-41 + 2-51 |
| `POOL_PUMP` | Pool pump | CTA-2045-B SGD 0x0030 (single speed) / 0x0031 (variable speed); IEEE 2030.5 DeviceCategoryType bit 4; ENERGY STAR Pool Pumps |
| `SUMP_PUMP` | Sump pump | IEC 60335-2-41 (scope) |
| `WELL_PUMP` | Well pump (submersible or jet) | IEC 60335-2-41 (scope) |
| `SEPTIC_PUMP` | Septic / effluent / sewage-ejector / grinder pump | IEC 60335-2-41 (scope) |

### Specialty

| Tag | Description | See also |
|---|---|---|
| `MACHINERY` | Machinery (welder, kiln, mill, lathe, drill press, saw, etc.) on a dedicated circuit | IEC 60204; IEC 62841 |
| `SNOW_MELTER` | Snow-melt (driveway / walkway radiant heating cable or mat) | IEC/EN 60800 (heating cables) |
| `STEAM_SHOWER_GENERATOR` | Steam shower generator | IEC 60335-2-105 |
| `HOT_TUB` | Hot tub / spa / jacuzzi | IEC 60335-2-60; EIA RECS "Hot tub heaters" |
| `SAUNA_HEATER` | Sauna heater | IEC 60335-2-53 |
| `POOL_HEATER` | Electric pool heater (resistive) | — |
| `IRRIGATION` | Irrigation (controller and booster pump) | IEC 60335-2-41; IEEE 2030.5 DeviceCategoryType bit 8; CTA-2045-B SGD 0x0040 |
| `SPARE` | Spare / unused circuit | — |

### Health

| Tag | Description | See also |
|---|---|---|
| `LIFE_SUPPORT` | Circuit feeding life-support equipment (mechanical ventilator, home hemodialysis, continuous-prescription oxygen concentrator, IPPB, LVAD, similar). Failure has near-immediate life-threatening consequences. | US utility medical-baseline rate-program qualifying-device lists |
| `MEDICAL_DEVICE` | Circuit feeding important health-assistive equipment that is not immediate-life-threat (CPAP / BiPAP, apnea monitor, nebulizer, suction machine, motorized wheelchair charger, hospital-grade electric bed, patient lift) | US utility medical-baseline rate-program qualifying-device lists |

### Other

| Tag | Description | See also |
|---|---|---|
| `SURGE_PROTECTOR` | Whole-panel surge protector / SPD | IEC 61643 |
| `SUBPANEL` | Circuit (feeder) feeding a downstream panel — eBus-aware or conventional. Whether the downstream panel is itself an eBus device is discoverable from `connection`'s `feeds-device-type` (a value of `energy.ebus.device.distribution-enclosure` indicates a chained eBus enclosure). | NEC Article 408; IEC 61439 |
| `ELEVATOR` | Elevator / lift | EN 81; OmniClass 23-23 11 11 |
| `SMOKE_CO_DETECTOR` | Smoke / CO detectors (smoke, carbon monoxide, fire-alarm, sprinkler-system control panels) | IEC 60839 / EN 14604 / EN 50291 |
| `SECURITY_SYSTEM` | Security system (alarm, burglar, intrusion-detection panel) | IEC 62642 / EN 50131 |
| `GARAGE_DOOR_OPENER` | Garage door opener | IEC 60335-2-95 + 2-103 |
| `ELECTRIC_GATE` | Electric gate | IEC 60335-2-103 |
| `OTHER` | Generic load that does not match any other tag in this registry | — |

## Multi-tag usage

A circuit serving multiple distinct categorized loads carries multiple tags. Example: a circuit feeding both a wall oven and a microwave on the same breaker publishes `info/tags = "OVEN,MICROWAVE"`. The order of tags within the comma-separated list is not significant.

A multi-tag value indicates **multiple distinct loads on one circuit**, not a single combination appliance. Combination appliances use dedicated combo tags:

- A combination fridge-freezer is `info/tags = "FRIDGE_FREEZER"`, not `"FRIDGE,FREEZER"`.
- A combination washer-dryer is `info/tags = "WASHER_DRYER"`, not `"WASHER,DRYER"`.
- A combined oven + cooktop unit is `info/tags = "RANGE"` (or `"RANGE_INDUCTION"`, etc.), not `"OVEN,COOKTOP"`.

For a single dedicated load (the common case), the tag list has one entry. For a circuit with mixed loads where some are unmarked, only the known load types are tagged.

When a tag has known and unknown variants (cooktop technology, ventilation-fan sub-type, lighting interior/exterior), publishers SHOULD use the most specific tag available and MAY fall back to the umbrella tag (`COOKTOP`, `VENTILATION_FAN`, `LIGHTING`) when the sub-type is not known.

## Critical-load designation

A subset of tags identifies loads with life-safety, property-protection, or health-critical importance. These loads SHOULD NOT be load-shed under DR or BESS-islanding scenarios except under explicit homeowner / installer override. Consumers (e.g., BESS islanding logic, backup-power priority rankers) can use this set as a hint:

- **Hard-critical** (absolute hold; never curtail): `LIFE_SUPPORT`
- **Soft-critical** (very low shed priority; prioritize during outages but accept trade-offs in long outages): `MEDICAL_DEVICE`, `SUMP_PUMP`, `SEPTIC_PUMP`, `SMOKE_CO_DETECTOR`, `SECURITY_SYSTEM`, `ELEVATOR`

The shed-priority decision is ultimately implemented through `priority`'s `shed-priority` and `relay-controllable` properties on the circuit device. The tags above are a *categorical hint* a publisher can use when initializing `shed-priority` defaults, and a consumer can use when surfacing critical loads in a UI.

## Reserved values

**`UNKNOWN` is NOT a valid `info/tags` value.** A circuit with no known load type conveys that condition by omitting the property entirely (per the "absent = unknown / not applicable" convention). Publishing `info/tags = "UNKNOWN"` is non-conformant.

`OTHER` IS a valid tag value, but with a specific meaning: "we know there is a load on this circuit, it is not in the registry, and we have nothing more specific to say." Producers SHOULD prefer `OTHER` over omitting the property only when the load was deliberately surveyed but does not fit any registered category. The distinction:

- `info/tags` omitted → no load type information available (could be mixed-load, unsurveyed, or simply unknown)
- `info/tags = "OTHER"` → a specific load is on this circuit, but it does not match any registered tag

## Out of scope for `info/tags`

Some additional dimensions are recorded here for awareness but are not currently represented in `info/tags`:

- **Circuit role** (single-load vs mixed-load, dedicated vs general-purpose) is already represented by `info`'s `dedicated` property on the circuit device.
- **Shedding / DR participation** is represented by `priority` (`shed-priority`, `relay-controllable`, `pcs-priority`) and is independent of the load identification in `info/tags`.
- **Location** (basement, bathroom, bedroom, kitchen, garage). The existing `info/name` property already carries homeowner-assigned location labels in free-text form. A structured location tag is not currently needed.

## Adding new tags

New tag values may be added as the integrator ecosystem identifies categories not yet covered. The process:

1. The proposed tag follows the format rules above (SCREAMING_SNAKE_CASE).
2. The proposed tag does not duplicate an existing tag's meaning. If it would refine an existing tag, use the family-with-suffix naming convention.
3. The proposed tag is added to this document in an appropriate category.
4. Document version is bumped. The data-model spec's `info/tags` description does not change (it points at this registry).

Producers and consumers SHOULD treat unknown tag values as opaque strings — present them in UIs without categorization, persist them, but do not error. This permits forward-compatibility: a new tag may appear in a circuit's `info/tags` before older consumer code knows about it, and that consumer continues to function.
