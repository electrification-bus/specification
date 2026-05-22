# Electrification Bus (eBus) Specification

The **Electrification Bus**, or **eBus**, is an open framework that enables Home Energy Infrastructure devices — distribution enclosures, battery energy storage systems, electric vehicle supply equipment, photovoltaic inverters, microgrid interconnect devices, and similar — to discover one another, communicate, and coordinate using open, standard protocols.

This repository holds the eBus specification documents.

## What's in this repository

- **Framework spec** — defines how devices participate in the bus: network architecture, discovery (mDNS), messaging (MQTT/Homie), credentials, security (TLS), updates, and adapter conventions. *Currently a working draft on the [`wip/framework`](../../tree/wip/framework) branch as `specification.md`; will land on `main` as `framework.md` when ready for review.*
- **`data-models/`** — vendor-neutral data models for specific device categories. Each data-model document defines the canonical Homie device structure (parent device + child devices, capabilities, properties) for that category. Data-model documents reference the framework but stand on their own — vendors implementing a specific device category will read the relevant data-model document directly.
- **`registries/`** — canonical registries for device-type identifiers (`energy.ebus.device.*`) and capability-type identifiers (`energy.ebus.capability.*`) used across all data models. Registries grow as new device categories are added.
- **`examples/`** — reference snippets, reference implementations, and integration examples.

## Status

| Document | Status |
|---|---|
| Framework spec | Draft, in progress (see [`wip/framework`](../../tree/wip/framework) branch) |
| `data-models/distribution-enclosure.md` | Planned (forthcoming) |
| `data-models/bess.md` | Planned |
| `data-models/mid.md` | Planned |
| `registries/device-types.md` | Planned |
| `registries/capability-types.md` | Planned |

## Long-term direction

The Electrification Bus initiative aims to roll into an established open-standards organization (for example, [LF Energy](https://lfenergy.org)) once the framework and core data models stabilize. License and contribution structure are chosen with that path in mind.

## Contributing

Detailed contribution guidance will be added as the project takes on additional contributors. For now, please open an issue to discuss proposed changes.

## License

This specification is licensed under the **[Community Specification License 1.0](LICENSE.md)**. The CSL 1.0 is designed for community-developed specifications and is structured for compatibility with open-standards organizations including the Linux Foundation. See [`NOTICES.md`](NOTICES.md) for implementer notifications and patent exclusions.
