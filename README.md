# Electrification Bus Specification

**Electrification Bus** (**eBus** for short) is an open framework that enables Home Energy Infrastructure devices — distribution enclosures, battery energy storage systems, electric vehicle supply equipment, photovoltaic inverters, microgrid interconnect devices, and similar — to discover one another, communicate, and coordinate using open, standard protocols. The project's home is at [ebus.energy](https://ebus.energy); this repository holds the specification documents.

**Intended audience:** HEI device OEMs implementing eBus on their own hardware; third-party developers building proxy publishers or integration tooling; and consumer-application developers building controllers, dashboards, and energy-management apps that read and write to eBus brokers.

## What's in this repository

- **[`framework.md`](framework.md)** — the framework spec. Defines how devices participate in the bus: network architecture, discovery (mDNS), messaging (MQTT/Homie), broker hosting, credentials and TLS (including mTLS client authentication), proxy publishers, design principles, and the device-and-node-type taxonomy that data-model documents build on.
- **`data-models/`** — vendor-neutral data models for specific device categories. Each data-model document defines the canonical Homie device structure (parent device + child devices, capabilities, properties) for that category. Data-model documents reference the framework but stand on their own — vendors implementing a specific device category will read the relevant data-model document directly.
- **`registries/`** — canonical registries for device-type identifiers (`energy.ebus.device.*`) and capability-type identifiers (`energy.ebus.capability.*`) used across all data models. Registries grow as new device categories are added.
- **`capabilities/`** — canonical property-catalog documents for cross-cutting `energy.ebus.capability.*` capabilities (metering, overcurrent protection, remote relay control, and similar). Each capability is defined once and referenced by the data models that use it, rather than restated in each; the capability-type registry indexes them.
- **`integration-guides/`** — informative guides describing how two or more data-model surfaces compose at runtime. Integration guides reference the relevant data-model documents but do not redefine their normative contracts; they describe the end-to-end flow (subscription topology, value transformations, commissioning, failure handling) when both sides of an integration are present together.
- **`examples/`** — reference snippets, reference implementations, and integration examples. *Currently empty; content will be added as the framework and data-model specifications stabilize.*
- **[`CHANGELOG.md`](CHANGELOG.md)** — a dated, artifact-tagged log of notable specification changes. The project is in rapid development and does not yet cut formal releases, so changes are grouped by date rather than by release tag.
- **`conventions/`** — conventions for *consuming* the specification, including the [`.ebus-spec.json`](conventions/spec-provenance.md) provenance lockfile a downstream implementation carries to pin and track which specification version it built against.
- **`spec-manifest.json`** — a machine-readable manifest of every versioned artifact and its current version, generated from the document headers (the same data the status table below renders for humans); downstream drift checks read it.

## Where to start

- **Implementing eBus on your own HEI device** → read [`framework.md`](framework.md) first, then the relevant data-model document (e.g., [`data-models/bess.md`](data-models/bess.md) for BESS vendors, [`data-models/distribution-enclosure.md`](data-models/distribution-enclosure.md) for panel vendors, [`data-models/utility-meter.md`](data-models/utility-meter.md) for meter vendors).
- **Building a proxy publisher** that bridges a non-eBus device into eBus (e.g., a Python service that polls a vendor cloud API and republishes as eBus) → [`framework.md`](framework.md) → [`data-models/proxy.md`](data-models/proxy.md) → the data-model for the device class you're proxying.
- **Building a controller, dashboard, or energy-management app** that consumes eBus data → [`framework.md`](framework.md) → the data-model documents for the device classes you'll consume → the integration guides in [`integration-guides/`](integration-guides/) for any cross-device flows you need.
- **Reviewing the spec** (standards committee, prospective adopter, curious reader) → start with [`framework.md`](framework.md); the data-models illustrate the framework applied to concrete device classes.

## Relationship to Homie

Electrification Bus builds on three well-known protocols — MQTT (with the [Homie Convention](https://homieiot.github.io/specification/), currently version 5, layered on top), mDNS, and HTTP/REST — specialized for Home Energy Infrastructure. See [`framework.md` §Relationship to Homie](framework.md#relationship-to-homie) for the precise division of responsibilities between what eBus defines and what the Homie Convention defines.

## Status

<!-- BEGIN generated status table (run: python3 tools/gen-spec-manifest.py) -->
| Document | Status |
|---|---|
| **Framework** | |
| [`framework.md`](framework.md) | DRAFT v0.5 (2026-07-10) |
| **Data Models** | |
| [`data-models/bess.md`](data-models/bess.md) | DRAFT v0.10 (2026-07-11) |
| [`data-models/circuit.md`](data-models/circuit.md) | DRAFT v0.1 (2026-07-04) |
| [`data-models/distribution-enclosure.md`](data-models/distribution-enclosure.md) | DRAFT v0.5 (2026-07-11) |
| [`data-models/outlet.md`](data-models/outlet.md) | DRAFT v0.1 (2026-06-26) |
| [`data-models/pdu.md`](data-models/pdu.md) | DRAFT v0.1 (2026-06-26) |
| [`data-models/proxy.md`](data-models/proxy.md) | DRAFT v0.1 (2026-05-22) |
| [`data-models/utility-meter.md`](data-models/utility-meter.md) | DRAFT v0.5 (2026-07-11) |
| [`data-models/water-heater.md`](data-models/water-heater.md) | DRAFT v0.3 (2026-07-11) |
| `data-models/mid.md` | Planned (see the standalone-MID note in [`data-models/bess.md`](data-models/bess.md) §Device Hierarchy) |
| **Registries** | |
| [`registries/capability-types.md`](registries/capability-types.md) | DRAFT v0.13 (2026-07-11) |
| [`registries/circuit-tags.md`](registries/circuit-tags.md) | DRAFT v0.1 (2026-05-23) |
| [`registries/device-types.md`](registries/device-types.md) | DRAFT v0.4 (2026-06-27) |
| [`registries/external-id-schemes.md`](registries/external-id-schemes.md) | DRAFT v0.1 (2026-05-16) |
| **Capabilities** | |
| [`capabilities/breaker.md`](capabilities/breaker.md) | DRAFT v0.1 (2026-07-05) |
| [`capabilities/connection.md`](capabilities/connection.md) | DRAFT v0.1 (2026-07-05) |
| [`capabilities/doe.md`](capabilities/doe.md) | DRAFT v0.1 (2026-07-09) |
| [`capabilities/flex.md`](capabilities/flex.md) | DRAFT v0.1 (2026-07-10) |
| [`capabilities/grid.md`](capabilities/grid.md) | DRAFT v0.1 (2026-07-11) |
| [`capabilities/grid-event.md`](capabilities/grid-event.md) | DRAFT v0.1 (2026-07-10) |
| [`capabilities/info.md`](capabilities/info.md) | DRAFT v0.1 (2026-07-05) |
| [`capabilities/meter.md`](capabilities/meter.md) | DRAFT v0.1 (2026-07-11) |
| [`capabilities/price.md`](capabilities/price.md) | DRAFT v0.1 (2026-07-10) |
| [`capabilities/soc.md`](capabilities/soc.md) | DRAFT v0.1 (2026-07-11) |
| [`capabilities/status.md`](capabilities/status.md) | DRAFT v0.1 (2026-07-11) |
| [`capabilities/switch.md`](capabilities/switch.md) | DRAFT v0.1 (2026-07-05) |
| [`capabilities/voltage-response.md`](capabilities/voltage-response.md) | DRAFT v0.1 (2026-07-10) |
| **Integration Guides** | |
| [`integration-guides/utility-meter-and-distribution-enclosure.md`](integration-guides/utility-meter-and-distribution-enclosure.md) | DRAFT v0.2 (2026-07-01) |
| **Extensions** | |
| [`extensions/imported.md`](extensions/imported.md) | STABLE v1.0.0 (2026-07-04) |
| **Conventions** | |
| [`conventions/spec-provenance.md`](conventions/spec-provenance.md) | DRAFT v0.1 (2026-07-10) |
| [`conventions/version-single-source.md`](conventions/version-single-source.md) | DRAFT v0.1 (2026-07-11) |
<!-- END generated status table -->
## Governance

Electrification Bus aims to be a vendor-neutral framework for Home Energy Infrastructure integration and interoperability. The schema vocabulary excludes vendor trademarks and product-specific terminology; participation in the spec's development and consumption of the spec are intended to be open and free.

**Today**, the project is a small-scale, early-stage open-standards effort led by Don Jackson (Clark Communications) acting in a benevolent-dictator capacity. This is a workable starting posture for early-stage spec development but is acknowledged to be unsustainable at scale — a single-person dependency is a fragile foundation for a standard that aspires to broad adoption, and one steward's preferences should not be the long-term arbiter of an open specification.

**Long-term**, the intent is to roll the project into an established open-standards organization once the framework and core data models have stabilized enough to make the transition meaningful. The license ([Community Specification License 1.0](LICENSE.md)) and the contribution workflow ([`CONTRIBUTING.md`](CONTRIBUTING.md)) are chosen for compatibility with that path.

Criteria the project applies when evaluating potential homes:

- **Open and free participation in the technical work.** Anyone interested in HEI interoperability should be able to contribute substantively without paying for the privilege.
- **Vendor neutrality.** No single vendor or vendor consortium should hold structural control over the spec's direction.
- **Continuity.** Succession planning visible from the outside; the project's bus factor should grow as it matures.
- **Technical fit.** Compatible with the framework's foundations (the Homie Convention, MQTT, mDNS, HTTP/REST).

[LF Energy](https://lfenergy.org) is the current leading candidate. Direct experience with LF Energy's hosted projects suggests that participation in a project's technical work is open and free regardless of LF Energy membership tier — membership is required for participation in LF Energy's own governance, but not for contributing to the technical work of an individual hosted project. Other paths remain under consideration.

## Contributing

Issues, Discussions, and pull requests are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the workflow. In short:

- **Questions, ideas, proposed new device or capability types** → [Discussions](https://github.com/electrification-bus/specification/discussions)
- **Confirmed errors, omissions, or agreed-upon changes** → [Issues](https://github.com/electrification-bus/specification/issues)
- **Patches** → pull requests; please open a Discussion or Issue first for non-trivial changes

## License

This specification is licensed under the **[Community Specification License 1.0](LICENSE.md)**. The CSL 1.0 is designed for community-developed specifications and is structured for compatibility with open-standards organizations including the Linux Foundation. See [`NOTICES.md`](NOTICES.md) for implementer notifications and patent exclusions.
