# Circuit Tag Registry

**Status:** DRAFT v0.2
**Date:** 2026-05-16
**Authors:** Don Jackson

## Purpose

The eBus distribution enclosure data model includes a per-circuit `info/tags` property on circuit child devices — a multi-valued, comma-separated string drawn from a controlled vocabulary that categorizes the load(s) on the circuit. See the [eBus distribution enclosure data model](../data-models/distribution-enclosure.md) for the property definition.

This document is the registry of currently-defined tag values. It is descriptive, not exhaustive: new tags may be added here as the integrator ecosystem requires, without requiring a schema change. Consumers MUST tolerate unknown tag values (e.g., display them as raw strings, ignore for categorization).

## Format rules

Tag values are semantically Homie enum values — `info/tags` is multi-valued, but each individual tag is drawn from the enum vocabulary defined here. The case convention matches Homie's existing enum convention (e.g., `OK`, `LOST`, `DEGRADED` on `capability.status`; `ON_GRID`, `OFF_GRID` on `capability.grid`).

- Tags are SCREAMING_SNAKE_CASE ASCII strings: uppercase letters, digits, and underscores only.
- No leading or trailing underscores; no consecutive underscores.
- No spaces, no hyphens, no mixed case.
- A circuit's `info/tags` value is a comma-separated list of tag strings; individual tag strings do not contain commas (by the format rule above).
- Tags are case-sensitive when compared; producers and consumers MUST emit and match the exact strings defined here.

## Currently-defined tags

Grouped into descriptive categories. Categories are descriptive only — they are not part of the published value and consumers do not need to know about them.

### EV

| Tag | Description |
|---|---|
| `EV_DRIVE` | EV charger (drive use) |
| `EV_OTHER` | Other EV charger |

### Specialty

| Tag | Description |
|---|---|
| `MACHINERY` | Machinery (welder, tool, kiln, mill, lathe, drill, saw) |
| `SNOW_MELTER` | Snow melt |
| `STEAM_SHOWER_GENERATOR` | Steam shower |
| `HOT_TUB` | Hot tub / spa / jacuzzi |
| `SAUNA_HEATER` | Sauna |
| `POOL_HEATER` | Pool heater |
| `PUMP` | Pump (circulator, filter, pool, sump, well, septic, water) |
| `SPARE` | Spare / unused circuit |

### Water heating

| Tag | Description |
|---|---|
| `WATER_HEATER` | Water heater (tank electric resistance, tankless, or other) |

### HVAC

| Tag | Description |
|---|---|
| `HEAT_STRIP` | Heat strip |
| `ELECTRIC_RESISTANCE_HEATER` | Electric resistance heater (baseboard, unit heater) |
| `ELECTRIC_FLOOR_HEAT` | Electric floor heat (radiant) |
| `AIR_HANDLER` | Air handler (blower, furnace, ducted) |
| `FURNACE` | Furnace |
| `AC_CONDENSER` | AC condenser (outdoor unit) |
| `HEAT_PUMP` | Heat pump (air-source / ASHP) |
| `MINI_SPLIT_AC_HP` | Mini-split AC / heat pump (ductless) |
| `GEOTHERMAL` | Geothermal (ground source) |
| `BOILER_AND_HYDRONIC_HEAT` | Boiler & hydronic heat (radiator, steam, baseboard) |
| `DEHUMIDIFIER` | Dehumidifier |
| `VENTILATION_FAN` | Ventilation fan (exhaust, bathroom fan, whole-house fan, attic fan, ERV, HRV) |
| `HVAC` | Other HVAC (fallback when no more specific tag applies) |

### Kitchen

| Tag | Description |
|---|---|
| `OVEN_RANGE` | Oven & range (stove, cooktop, induction, convection — combined unit) |
| `OVEN` | Oven (when separate from cooktop) |
| `RANGE` | Range / cooktop (when separate from oven) |
| `MICROWAVE` | Microwave |
| `DISHWASHER` | Dishwasher |
| `DISPOSAL` | Garbage disposal |
| `HOOD` | Range hood / exhaust |

### Laundry

| Tag | Description |
|---|---|
| `WASHER` | Washer (front-load, top-load, clothes) |
| `DRYER` | Dryer (gas, vented electric, condenser, heat pump) |

### Refrigeration

| Tag | Description |
|---|---|
| `FRIDGE` | Refrigerator |
| `FREEZER` | Freezer (ice maker, chest, upright) |
| `FRIDGE_FREEZER` | Combined fridge & freezer |

### Other

| Tag | Description |
|---|---|
| `SURGE_PROTECTOR` | Surge protector |
| `DOWNSTREAM_PANEL` | Another distribution enclosure (downstream in a multi-enclosure chain) |
| `SUBPANEL` | Conventional sub-panel |
| `ELEVATOR` | Elevator / lift |
| `SMOKE_CO_DETECTOR` | Smoke / CO detectors (carbon monoxide, fire, sprinkler) |
| `SECURITY_SYSTEM` | Security system (alarm, burglar) |
| `GARAGE_DOOR_OPENER` | Garage door opener |
| `ELECTRIC_GATE` | Electric gate |
| `IRRIGATION` | Irrigation (sprinkler, landscape) |
| `OTHER` | Generic appliance / load that does not match any other tag in this registry |

## Multi-tag usage

A circuit serving multiple categorized loads carries multiple tags. Example: a circuit feeding both a wall oven and a microwave on the same breaker would publish `info/tags = "OVEN,MICROWAVE"`. The order of tags within the comma-separated list is not significant.

For a circuit with one dedicated load, the tag list typically has one entry. For a circuit with mixed loads where some are unmarked, only the known load types are tagged.

## Reserved enum values not used as tag values

**`UNKNOWN` is NOT a valid `info/tags` value.** A circuit with no known load type conveys that condition by omitting the `info/tags` property entirely (per the "absent = unknown / not applicable" convention). Publishing `info/tags = "UNKNOWN"` is non-conformant.

`OTHER` IS a valid tag value, but with a specific meaning: "we know there is a load here, it is not in the registry, and we have nothing more specific to say." Producers SHOULD prefer `OTHER` over omitting the property only when the load was deliberately surveyed but does not fit any registered category. The distinction:

- `info/tags` omitted → no load type information available (could be mixed-load, unsurveyed, or simply unknown)
- `info/tags = "OTHER"` → a specific load is on this circuit, but it does not match any registered tag

## Out of scope for `info/tags`

Additional tagging dimensions are NOT currently represented in `info/tags`. They are recorded here for awareness:

- **Circuit Type** — `Lights`, `Outlets / Receptacles`. These describe the general electrical role of a circuit, distinct from the appliances it serves. They are not appliance categories and are not in `info/tags` at this time. If they become useful to expose, they would likely warrant a separate property (e.g., `info/circuit-type`) rather than being mixed into the appliance-type tag space.
- **Location** — `Basement`, `Bathroom`, `Bedroom`, `Kitchen`, `Garage`, etc. These describe where the circuit serves loads within the home. The existing `info/name` property already carries homeowner-assigned location labels in free-text form, so a separate structured location tag is not currently needed.

These dimensions are not in scope here; they are documented so future readers understand that the broader tagging space is larger than this registry.

## Adding new tags

New tag values may be added to this registry as the integrator ecosystem identifies categories that are not yet covered. The process:

1. The proposed tag follows the format rules above (SCREAMING_SNAKE_CASE).
2. The proposed tag does not duplicate an existing tag's meaning (or, if it does, the duplicate is resolved before merging — by either renaming or retiring one).
3. The proposed tag is added to this document with a description in an appropriate category.
4. Document version is bumped. The data-model spec's `info/tags` description does not change (it points at this registry).

Producers and consumers SHOULD treat unknown tag values as opaque strings — present them in UIs without categorization, persist them, but do not error. This permits forward-compatibility: a new tag may appear in a panel's `info/tags` before older consumer code knows about it, and that consumer continues to function.
