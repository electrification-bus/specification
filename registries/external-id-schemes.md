# External ID Scheme Registry

**Status:** DRAFT v0.1
**Date:** 2026-05-16
**Authors:** Don Jackson

## Purpose

The eBus distribution enclosure data model includes a per-circuit `info/external-ids` property on circuit child devices — a multi-valued, comma-separated list of opaque identifiers from external systems that reference the load(s) on a circuit. Each list item is of the form `<scheme>:<identifier>` where the scheme prefix names the foreign system that issued the identifier. See the [eBus distribution enclosure data model](../data-models/distribution-enclosure.md) for the property definition.

This document is the registry of currently-defined scheme prefixes. It is descriptive, not exhaustive: new schemes may be added here as integrators identify external systems that need representation, without requiring a schema change. Consumers MUST tolerate unknown scheme prefixes (e.g., persist the value, ignore for scheme-specific handling).

## Format rules (recap from data-model spec)

- An `info/external-ids` value is a comma-separated list. Items are separated by commas.
- Each item is of the form `<scheme>:<identifier>` where `<scheme>` is a known scheme name from this registry and `<identifier>` is the value within that namespace.
- Parsing rule: items are split on the **first** `:` only — scheme is everything before the first colon, identifier is everything after.
- Identifier values MUST NOT contain literal commas (percent-encode if needed).
- Scheme names are kebab-case ASCII, lowercase, no internal colons.
- Scheme names are case-sensitive when compared.

The single-split-on-first-colon rule preserves identifiers that natively contain colons (such as a Zigbee EUI-64 in its conventional `00:11:22:33:44:55:66:77` form).

## Currently-defined schemes

| Scheme | Identifier shape | Description |
|---|---|---|
| `matter` | Per Matter specification | A Matter device identifier — typically the operational node identifier or the vendor/product/serial composite. Producers SHOULD use a stable identifier that survives Matter fabric re-commissioning where the specification supports one. |
| `zigbee` | EUI-64, conventionally 8 colon-separated hex bytes (e.g., `00:11:22:33:44:55:66:77`) | A Zigbee 64-bit IEEE extended address. |
| `mac` | EUI-48, conventionally 6 colon-separated hex bytes (e.g., `AA:BB:CC:DD:EE:FF`) | A MAC / EUI-48 hardware address. Useful for WiFi- or Ethernet-connected smart loads where no higher-protocol identifier is known. |
| `manufacturer-serial` | Opaque manufacturer-defined string | A raw manufacturer serial number, with no further protocol scope. Useful when no other identifier is available and only the physical-device serial has been captured. |
| `vendor` | `<vendor-name>:<vendor-specific-identifier>` | A vendor-scoped identifier. The identifier portion itself begins with a kebab-case vendor name, then a single `:`, then the vendor's own identifier format. Example: `vendor:tesla:abc123`. Consumers that handle vendor-specific identifiers further-parse the identifier portion. |

## Examples

A circuit feeding a Matter-commissioned smart appliance whose Matter node identifier is `0x123ABC`:

```
info/external-ids = "matter:0x123ABC"
```

A circuit feeding a Zigbee-connected EVSE with EUI-64 `00:11:22:33:44:55:66:77`:

```
info/external-ids = "zigbee:00:11:22:33:44:55:66:77"
```

A circuit feeding a Tesla-vendor device whose Tesla-specific identifier is `wall-connector-42`:

```
info/external-ids = "vendor:tesla:wall-connector-42"
```

A circuit feeding a smart load known by both its Matter ID and a manufacturer serial:

```
info/external-ids = "matter:0x123ABC,manufacturer-serial:SN-12345"
```

## Adding new schemes

New scheme prefixes may be added to this registry as integrators identify external systems that warrant representation. The process:

1. The proposed scheme name follows the format rules above (kebab-case, lowercase, no internal colons).
2. The proposed scheme does not duplicate an existing scheme's meaning. If the new system's identifiers could fit under an existing scheme (e.g., a new vendor under `vendor`), prefer extension over a new top-level scheme.
3. The proposed scheme is added to this document with a description of the expected identifier shape.
4. Document version is bumped. The data-model spec's `info/external-ids` description does not change (it points at this registry).

Producers and consumers SHOULD treat unknown scheme prefixes as opaque — persist the value, present it in UIs without scheme-specific behavior, and do not error. This permits forward-compatibility: new schemes may appear in a panel's `info/external-ids` before older consumer code knows about them, and that consumer continues to function.

## Out of scope

- **Identifier-format standardization within a scheme.** The registry names schemes and gives the expected identifier shape, but does not specify how identifiers within a scheme are constructed — that is owned by the entity that defines the scheme (the Matter Connectivity Standards Alliance for `matter`, the Connectivity Standards Alliance for `zigbee`, individual vendors for `vendor:<name>`).
- **Resolution / dereferencing.** The registry does not define how a consumer uses an external identifier to communicate with the foreign system. That is a property of the consumer's own integration with that system.
- **Persistence guarantees.** An external identifier in `info/external-ids` may or may not be stable across re-commissioning, factory reset, hardware replacement, or fabric changes in the foreign system. Producers SHOULD use the most stable identifier the foreign system provides, but the registry does not guarantee stability and consumers SHOULD treat external identifiers as advisory rather than primary keys.
