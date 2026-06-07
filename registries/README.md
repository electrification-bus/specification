# Registries

Canonical registries used across all eBus data models.

- [`device-types.md`](device-types.md) — registered values for `energy.ebus.device.*`
- [`capability-types.md`](capability-types.md) — registered values for `energy.ebus.capability.*`
- [`circuit-tags.md`](circuit-tags.md) — controlled vocabulary for `info/tags` properties on connection-point devices. Currently used by the per-circuit `info/tags` property in the distribution-enclosure data model; reusable by other data models with connection-point devices that benefit from categorical downstream classification.
- [`external-id-schemes.md`](external-id-schemes.md) — registered scheme prefixes for the per-circuit `info/external-ids` property (e.g., `matter:`, `zigbee:`, `mac:`, `vendor:`), naming the foreign systems that issue the identifiers.

Registries grow as new device categories and capabilities are defined in the data-model documents. The registries are the authoritative reference for which identifiers are reserved; data-model documents must use registered identifiers, and new identifiers are added to the registries when a data-model document introduces them.
