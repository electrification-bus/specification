# Electrification Bus Specification

**Electrification Bus** (**eBus** for short) is an open framework that enables Home Energy Infrastructure devices — distribution enclosures, battery energy storage systems, electric vehicle supply equipment, photovoltaic inverters, microgrid interconnect devices, and similar — to discover one another, communicate, and coordinate using open, standard protocols.

This repository holds the eBus specification documents.

## Relationship to Homie

eBus is built on top of [Homie 5](https://homieiot.github.io/) (a general-purpose IoT convention) plus complementary conventions like mDNS and REST/OpenAPI, specialized for Home Energy Infrastructure (HEI). The eBus value-add is HEI specialization: HEI-specific device types (`energy.ebus.device.*`), capability types (`energy.ebus.capability.*`), and the property catalogs within them. Homie features (the parent-child device model, the `$state` lifecycle, the `$description` mutability rules, the `$settable` attribute, retained-message semantics) belong to Homie and are credited to Homie, not to eBus. Schema vocabulary defined by eBus is vendor-neutral; vendor trademarks and product-specific terminology are explicitly excluded from the schema. The Homie `name` string attribute on each property is implementation-defined and may carry vendor-specific labels — its contents are presentation, not part of the standard.

## What's in this repository

- **[`framework.md`](framework.md)** — the framework spec. Defines how devices participate in the bus: network architecture, discovery (mDNS), messaging (MQTT/Homie), broker hosting, credentials and TLS (including mTLS client authentication), proxy publishers, design principles, and the device-and-node-type taxonomy that data-model documents build on.
- **`data-models/`** — vendor-neutral data models for specific device categories. Each data-model document defines the canonical Homie device structure (parent device + child devices, capabilities, properties) for that category. Data-model documents reference the framework but stand on their own — vendors implementing a specific device category will read the relevant data-model document directly.
- **`registries/`** — canonical registries for device-type identifiers (`energy.ebus.device.*`) and capability-type identifiers (`energy.ebus.capability.*`) used across all data models. Registries grow as new device categories are added.
- **`integration-guides/`** — informative guides describing how two or more data-model surfaces compose at runtime. Integration guides reference the relevant data-model documents but do not redefine their normative contracts; they describe the end-to-end flow (subscription topology, value transformations, commissioning, failure handling) when both sides of an integration are present together.
- **`examples/`** — reference snippets, reference implementations, and integration examples.

## Status

| Document | Status |
|---|---|
| [`framework.md`](framework.md) | Working Draft v0.3.0 (2026-06-06) |
| [`data-models/proxy.md`](data-models/proxy.md) | DRAFT v0.1 (2026-05-22) |
| [`data-models/distribution-enclosure.md`](data-models/distribution-enclosure.md) | DRAFT v0.1 (2026-05-17) |
| [`data-models/utility-meter.md`](data-models/utility-meter.md) | DRAFT v0.1 (2026-06-06) |
| [`data-models/bess.md`](data-models/bess.md) | DRAFT v0.6 (2026-06-06) |
| `data-models/mid.md` | Planned |
| [`registries/device-types.md`](registries/device-types.md) | DRAFT v0.1 (2026-05-22) |
| [`registries/capability-types.md`](registries/capability-types.md) | DRAFT v0.2 (2026-06-06) |
| [`registries/circuit-tags.md`](registries/circuit-tags.md) | DRAFT v0.1 (2026-05-23) |
| [`registries/external-id-schemes.md`](registries/external-id-schemes.md) | DRAFT v0.1 (2026-05-16) |
| [`integration-guides/utility-meter-and-distribution-enclosure.md`](integration-guides/utility-meter-and-distribution-enclosure.md) | DRAFT v0.1 (2026-06-06) |

## Long-term direction

The Electrification Bus initiative aims to roll into an established open-standards organization (for example, [LF Energy](https://lfenergy.org)) once the framework and core data models stabilize. License and contribution structure are chosen with that path in mind.

## Contributing

Detailed contribution guidance will be added as the project takes on additional contributors. For now, please open an issue to discuss proposed changes.

## License

This specification is licensed under the **[Community Specification License 1.0](LICENSE.md)**. The CSL 1.0 is designed for community-developed specifications and is structured for compatibility with open-standards organizations including the Linux Foundation. See [`NOTICES.md`](NOTICES.md) for implementer notifications and patent exclusions.
