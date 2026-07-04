# Homie Extensions

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-04
**Authors:** Don Jackson

Electrification Bus defines [Homie 5](../framework.md#relationship-to-homie) extensions under its reverse-domain namespace. Per the Homie convention, every extension is identified by a unique ID of the form `energy.ebus.<suffix>` (the reverse domain `energy.ebus` plus a freely chosen suffix) and is documented in its own file in this directory. This is distinct from device types (`energy.ebus.device.*`) and capability types (`energy.ebus.capability.*`), which are controlled vocabularies in [registries/](../registries/).

Extension documents are published under [CC-BY 4.0](https://homieiot.github.io/license), the license Homie recommends for extensions and uses for its own. This is a deliberate per-file exception to the repository's overall [LICENSE.md](../LICENSE.md) (Community Specification License 1.0), so that an extension can be listed in the official Homie convention without relicensing.

A device advertises an extension by adding its versioned entry, `<id>:<version>:[<homie-versions>]`, to the `extensions` array of its device `$description`. In Homie 5 a device is described by a single JSON `$description` document, and an extension MAY define additional fields in that document. The Homie forward-compatibility rule requires a controller to ignore unknown fields within an object but keep the object, so extension-defined fields are safe for controllers that do not implement the extension.

See the [main README](../README.md) for the status of each document.

## Published extensions

| ID | Version | Status | Document | Summary |
|----|---------|--------|----------|---------|
| `energy.ebus.imported` | 1.0.0 | DRAFT | [imported.md](imported.md) | Marks a device that was bridged in from another ecosystem, and records the source ecosystem. |

## Adding an extension

1. Choose an ID `energy.ebus.<suffix>`, where `<suffix>` is lowercase kebab-case and distinct from the `energy.ebus.device.*` and `energy.ebus.capability.*` type namespaces.
2. Write `extensions/<suffix>.md` based on the [Homie extension template](https://github.com/homieiot/convention/blob/develop/extensions/extension_template.md), adapted for Homie 5's JSON `$description` (extension attributes are fields of the description document, not `$`-prefixed MQTT topics).
3. Add a row to the table above, and add the document to the [main README](../README.md) status table.
4. Optionally submit the extension to the official Homie convention for listing (fork [`homieiot/convention`](https://github.com/homieiot/convention), add the document to `extensions/documents/`, open a pull request), following the precedent of third-party extensions such as `eu.epnw.meta`.
