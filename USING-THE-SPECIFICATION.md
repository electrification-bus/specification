# Using the Electrification Bus Specification

*Informative. This guide shows how to use the specification, and especially its machine-readable property definitions, to build eBus device publishers, simulators, and tooling. The normative documents are [`framework.md`](framework.md), the capability catalogs, and the data models; this guide is a map for developers, not a normative contract.*

## Guidelines, not rules

Electrification Bus is a shared, vendor-neutral vocabulary and a set of conventions. It is permissive by design (see [`framework.md` §Conformance Latitude](framework.md#conformance-latitude)):

- It describes what a device **can** and **should** publish, and **how**, not a fixed set every device must publish.
- A publisher publishes the subset it supports and omits the rest. Absent means "unknown" or "not applicable," never a sentinel.
- A publisher **may** publish properties the spec does not define, and **may** publish a property with a wider or redefined datatype or value set, as long as it advertises the shape it publishes in its Homie 5 `$description` / `$format`.
- A device's runtime `$description` is the authority for what it actually publishes.

So the specification is the reference a device is published *against*; it is not a checklist a device must match. That framing is what makes the machine-readable definitions below useful without being a straitjacket.

## The two machine-readable families

Every capability catalog and data model has a co-located `.json` sibling, generated from the prose (see [`conventions/property-json.md`](conventions/property-json.md)). There are two kinds, and you use them together.

A **capability catalog** (`capabilities/<name>.json`) is the recommended, extensible vocabulary for one capability: for each property, how to publish it if you publish it.

```json
// capabilities/meter.json (excerpt)
"properties": {
  "active-power":    { "datatype": "float", "unit": "W",  "req": "MAY" },
  "imported-energy": { "datatype": "float", "unit": "Wh", "req": "MAY" },
  "power-factor":    { "datatype": "float", "req": "MAY", "format": "-1.0:1.0" }
}
```

A **device profile** (`data-models/<name>.json`) is a light, advisory composition: which capabilities each device type in the model typically publishes.

```json
// data-models/bess.json (excerpt)
"device_types": {
  "energy.ebus.device.bess": {
    "role": "parent",
    "capabilities": {
      "info":  { "catalog": "energy.ebus.capability.info",  "catalog_version": "0.1", "req": "MUST" },
      "meter": { "catalog": "energy.ebus.capability.meter", "catalog_version": "0.2", "req": "MUST" }
    }
  }
}
```

**The join:** a profile tells you *which capabilities* a device type composes; each capability's catalog tells you *which properties* it offers and *how* to publish them. A device then publishes whatever subset of that it supports. The recommended vocabulary (the "how") is in the catalog; the composition is in the profile; the actual published surface is the device's own choice, declared at runtime.

## Building a device publisher

Use the profile and catalogs to scaffold the Homie structure, then wire each property to your device's internal data. An eBus SDK for your language reads the JSON and does the scaffolding; you fill in the back end.

```text
profile = load("data-models/bess.json")
for device_type, dt in profile.device_types:
    for cap_id, use in dt.capabilities:
        catalog = load("capabilities/" + cap_id + ".json")
        for prop_id, prop in catalog.properties:
            declare Homie property  {device_type}/{cap_id}/{prop_id}
                $datatype = prop.datatype
                $unit     = prop.unit       # if numeric
                $format   = prop.format      # if present
                $settable = prop.settable    # if true
            # TODO(you): read {prop_id} from your device's internal API
```

Two things to note. The scaffolder generates the *full* catalog property set for each composed capability (all MAY); you then keep the subset your device actually supports and delete or ignore the rest, because publishing is opt-in (principle 3). And if your device exposes something the catalog does not cover, publish it anyway with your own `$format`: that is legal (see §Guidelines, not rules).

## Simulating a device

A simulator is the same join, but instead of wiring a real back end it publishes plausible values of the right type and format. Because it consumes the spec JSON directly, a simulator cannot drift from the spec.

```text
for prop_id, prop in catalog.properties:
    publish  {device_type}/{cap_id}/{prop_id}  =  fake_value(prop.datatype, prop.unit, prop.format)
```

This makes it cheap to stand up a simulated distribution enclosure, BESS, or meter for a controller or dashboard to develop against. The simulator's "back end" (making up values) is far easier than a real device's.

## Tracking how your device follows the spec

Two related checks help you stay aligned as both your device and the spec evolve.

**Drift against the spec.** Compare what your device actually publishes (read its live `$description`) against the profile and catalogs, at the capability *and* the property level:

```text
published  = read $description from the running device
spec_caps  = profile.device_types[my_type].capabilities

for cap_id in published.capabilities:
    if cap_id not in spec_caps:                      note "capability not in the spec"
    catalog = load("capabilities/" + cap_id + ".json")
    for prop_id, p in published[cap_id].properties:
        if prop_id not in catalog.properties:         note "property not in the catalog"
        elif p.datatype != catalog[prop_id].datatype: note "datatype differs from the recommendation"
```

Purposeful deviations are fine, and they are the point of a permissive spec: you might publish `status/fault-state` as an open `string` rather than the catalog's `enum`, or add a vendor-specific property. Declare those intentional deviations (see the next section) so the drift check annotates them as intended rather than flagging them as accidental drift.

**Snapshot before and after a change.** Capture your device's full Homie/MQTT representation, make a code change, capture it again, and diff. This catches unintended changes to your published surface (a renamed property, a dropped node, a changed datatype) that a spec-level check would not, because it compares your device to *itself*.

The version-level companion to both is the [`.ebus-spec.json`](conventions/spec-provenance.md) lockfile, which pins the artifact *versions* your implementation builds against; the checks above go one level deeper, to the capabilities and properties within them.

## Declaring your own instance

The specification stays vendor-neutral: it does not carry any particular product's published subset or deviations. Those are facts about *your* device, so they live in *your* declaration, referencing the spec:

- the artifact versions you build against, in your [`.ebus-spec.json`](conventions/spec-provenance.md);
- the capabilities and properties you actually publish, and any intentional deviations (a widened datatype, an added property), in your own instance description, which your drift check reads so intended deviations are noted rather than flagged.

This keeps the boundary clean: vendor-neutral vocabulary and composition upstream in the spec, product-specific instance downstream in your repository.

## Where the pieces live

- **This repository** publishes the vendor-neutral data (catalogs and profiles) and checks its own internal consistency in CI. It carries no product's instance.
- **Language SDKs** read the JSON, hydrate it into native structures, and provide the scaffolding used to build publishers and simulators (optionally with subset-pruning filters). The [Python SDK](https://github.com/electrification-bus/python-sdk) is the first; SDKs for other languages will follow.
- **Drift and snapshot tooling** compares a running device against the spec, and a device against its former self.
- **Simulators** pick an SDK and scaffold from the profiles.

## See also

- [`framework.md`](framework.md) and its [Conformance Latitude](framework.md#conformance-latitude) and [Design Principles](framework.md#design-principles).
- [`conventions/property-json.md`](conventions/property-json.md): the structure, generation, and versioning of the machine-readable JSON.
- [`conventions/spec-provenance.md`](conventions/spec-provenance.md): the `.ebus-spec.json` version lockfile.
- The capability catalogs in [`capabilities/`](capabilities/) and the data models in [`data-models/`](data-models/), each with its `.json` sibling.
