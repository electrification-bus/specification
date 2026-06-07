# Electrification Bus Specification

**Electrification Bus** (**eBus** for short) is an open framework that enables Home Energy Infrastructure devices — distribution enclosures, battery energy storage systems, electric vehicle supply equipment, photovoltaic inverters, microgrid interconnect devices, and similar — to discover one another, communicate, and coordinate using open, standard protocols. The project's home is at [ebus.energy](https://ebus.energy); this repository holds the specification documents.

**Intended audience:** HEI device OEMs implementing eBus on their own hardware; third-party developers building proxy publishers or integration tooling; and consumer-application developers building controllers, dashboards, and energy-management apps that read and write to eBus brokers.

## What's in this repository

- **[`framework.md`](framework.md)** — the framework spec. Defines how devices participate in the bus: network architecture, discovery (mDNS), messaging (MQTT/Homie), broker hosting, credentials and TLS (including mTLS client authentication), proxy publishers, design principles, and the device-and-node-type taxonomy that data-model documents build on.
- **`data-models/`** — vendor-neutral data models for specific device categories. Each data-model document defines the canonical Homie device structure (parent device + child devices, capabilities, properties) for that category. Data-model documents reference the framework but stand on their own — vendors implementing a specific device category will read the relevant data-model document directly.
- **`registries/`** — canonical registries for device-type identifiers (`energy.ebus.device.*`) and capability-type identifiers (`energy.ebus.capability.*`) used across all data models. Registries grow as new device categories are added.
- **`integration-guides/`** — informative guides describing how two or more data-model surfaces compose at runtime. Integration guides reference the relevant data-model documents but do not redefine their normative contracts; they describe the end-to-end flow (subscription topology, value transformations, commissioning, failure handling) when both sides of an integration are present together.
- **`examples/`** — reference snippets, reference implementations, and integration examples. *Currently empty; content will be added as the framework and data-model specifications stabilize.*

## Where to start

- **Implementing eBus on your own HEI device** → read [`framework.md`](framework.md) first, then the relevant data-model document (e.g., [`data-models/bess.md`](data-models/bess.md) for BESS vendors, [`data-models/distribution-enclosure.md`](data-models/distribution-enclosure.md) for panel vendors, [`data-models/utility-meter.md`](data-models/utility-meter.md) for meter vendors).
- **Building a proxy publisher** that bridges a non-eBus device into eBus (e.g., a Python service that polls a vendor cloud API and republishes as eBus) → [`framework.md`](framework.md) → [`data-models/proxy.md`](data-models/proxy.md) → the data-model for the device class you're proxying.
- **Building a controller, dashboard, or energy-management app** that consumes eBus data → [`framework.md`](framework.md) → the data-model documents for the device classes you'll consume → the integration guides in [`integration-guides/`](integration-guides/) for any cross-device flows you need.
- **Reviewing the spec** (standards committee, prospective adopter, curious reader) → start with [`framework.md`](framework.md); the data-models illustrate the framework applied to concrete device classes.

## Relationship to Homie

Electrification Bus builds on three well-known protocols — MQTT (with the [Homie Convention](https://homieiot.github.io/specification/), currently version 5, layered on top), mDNS, and HTTP/REST — specialized for Home Energy Infrastructure. See [`framework.md` §Relationship to Homie](framework.md#relationship-to-homie) for the precise division of responsibilities between what eBus defines and what the Homie Convention defines.

## Status

| Document | Status |
|---|---|
| **Framework** | |
| [`framework.md`](framework.md) | DRAFT v0.3 (2026-06-06) |
| **Data Models** | |
| [`data-models/proxy.md`](data-models/proxy.md) | DRAFT v0.1 (2026-05-22) |
| [`data-models/distribution-enclosure.md`](data-models/distribution-enclosure.md) | DRAFT v0.1 (2026-05-17) |
| [`data-models/utility-meter.md`](data-models/utility-meter.md) | DRAFT v0.1 (2026-06-06) |
| [`data-models/bess.md`](data-models/bess.md) | DRAFT v0.6 (2026-06-06) |
| `data-models/mid.md` | Planned — see standalone-MID note in [`data-models/bess.md`](data-models/bess.md) §Device Hierarchy |
| **Registries** | |
| [`registries/device-types.md`](registries/device-types.md) | DRAFT v0.2 (2026-06-06) |
| [`registries/capability-types.md`](registries/capability-types.md) | DRAFT v0.2 (2026-06-06) |
| [`registries/circuit-tags.md`](registries/circuit-tags.md) | DRAFT v0.1 (2026-05-23) |
| [`registries/external-id-schemes.md`](registries/external-id-schemes.md) | DRAFT v0.1 (2026-05-16) |
| **Integration Guides** | |
| [`integration-guides/utility-meter-and-distribution-enclosure.md`](integration-guides/utility-meter-and-distribution-enclosure.md) | DRAFT v0.1 (2026-06-06) |

## Long-term direction

The Electrification Bus initiative aims to roll into an established open-standards organization (for example, [LF Energy](https://lfenergy.org)) once the framework and core data models stabilize. License and contribution structure are chosen with that path in mind.

## Contributing

Detailed contribution guidance will be added as the project takes on additional contributors. For now, please open an issue to discuss proposed changes.

## License

This specification is licensed under the **[Community Specification License 1.0](LICENSE.md)**. The CSL 1.0 is designed for community-developed specifications and is structured for compatibility with open-standards organizations including the Linux Foundation. See [`NOTICES.md`](NOTICES.md) for implementer notifications and patent exclusions.
