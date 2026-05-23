# Data Models

Vendor-neutral data models for specific Home Energy Infrastructure device categories.

Each data-model document in this directory defines the canonical Homie device structure (parent device + child devices, capabilities, properties) for one device category. Data-model documents reference the [eBus framework spec](../../../tree/wip/framework) but stand on their own — vendors implementing a specific device category read the relevant data-model document directly.

See the [main README](../README.md) for the current status of each data-model document.

## Design Principles

The following principles guide the structure of every eBus data model. Individual data-model documents may extend or clarify them but should not contradict them.

1. **Homie devices represent physical things** — if it could maintain its own independent Homie representation, it is a Homie device.
2. **Homie nodes represent capabilities** — what a Homie device can do (meter, switch, sense), not what physical component it is.
3. **Publish what you have, omit what you don't** — absent properties mean "unknown" or "not applicable," not a sentinel-encoded value.
4. **Parent aggregates children** — the parent device exposes system-level aggregates; per-component detail lives on the relevant child.
5. **Standard capability types are reused** across device classes.
6. **Proxying is first-class.** eBus supports *proxying* — publication of an eBus representation by a publisher other than the device itself — as a peer to native publishing. The consumer-facing surface is identical for both forms, and capability and property contracts are written so that any conformant publisher (native or proxy) can satisfy them. See [proxy.md](proxy.md) for the full proxy specification (disambiguation between proxied and native representations, device-ID convention, and where proxy-side knowledge lives).
7. **Properties belong on the device that authoritatively knows them** — even when proxying makes other placements convenient. A property that could not be populated by a non-proxying publisher belongs elsewhere. This is a direct consequence of principle 6: the property contract must be satisfiable by *any* conformant publisher, native or proxy, and a property smuggled onto an adjacent device because only the proxy happens to know it breaks the contract for the native publisher.
8. **Forward compatibility is a design goal** — the data model defines slots for richer data than current implementations capture. Properties are MAY-level by default; datatypes are chosen for extensibility (open-vocabulary strings, not hardcoded enums where the value space is open); capabilities accept new properties additively. The model serves as a contract for the evolving ecosystem, not as a transcript of any one current feature set.
9. **Multi-instance from the outset** — identifying attributes and inter-device relationships are recorded per-device rather than enumerated as class-level properties on a containing parent, so N instances of any class can coexist without model changes (for example, multiple BESSs, PV inverters, or EVSEs in a single distribution enclosure).
