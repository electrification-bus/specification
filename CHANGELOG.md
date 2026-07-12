# Changelog

All notable changes to the Electrification Bus specification: the data models, capability catalogs, registries, and framework.

**This project is in rapid development and does not yet cut formal releases.** Changes are grouped by **date, not by release tag**. Each artifact (capability catalog, data model, registry) carries its own `Version:` in its document header, and those **per-artifact versions are the unit downstream implementations depend on** (see the [README status table](README.md#status) for the current set, and [`conventions/spec-provenance.md`](conventions/spec-provenance.md) for how a downstream pins them). This changelog records what changed and when, so an implementer can answer "what moved since I last synced?" without reading raw git history.

Entries are tagged with the affected artifact and a category (Added / Changed / Renamed / Deprecated / Removed / Fixed). The commit hash in parentheses links each entry to git history. Formal releases and version tags will begin once the specification stabilizes.

## 2026-07-11

### Fixed

- **capability/meter** — corrected the reactive-power and reactive-energy unit strings from `VAR` / `VARh` to the lowercase `var` / `varh`: the IEC 80000-6 standardized symbol, and the casing the [Homie convention](https://github.com/electrification-bus/convention)'s recommended-unit list uses for SI symbols (`W`, `Hz`, `Pa`, ...). This also removes an internal inconsistency: `data-models/bess.md` already used the lowercase `var` (its Enphase mapping notes the source is "already var"). Apparent power/energy (`VA` / `VAh`) were already correct and are unchanged. In-place DRAFT fix: `$unit` is an advisory display attribute (consumers dispatch on property ID and datatype, not the unit string), so the artifact version stays 0.1 and no downstream lockfile re-pin is required; only the document Date header moved (manifest + README status table regenerated).

### Added

- **capability/soc** 0.1 and **capability/status** 0.1 — canonicalized these cross-cutting capabilities into standalone versioned catalogs. They were defined only inline in the data models, so they could not be pinned in a downstream lockfile or tracked for drift. `soc` reconciles the BESS electrical reservoir and the water-heater thermal reservoir; `status` defines the `fault-state` / `communication-state` / `active-alerts` core plus device-specific diagnostics.
- **capability/load-shed** 0.1 — canonicalized and **corrected a stale registry entry**: the circuit load-shed capability was registered as `energy.ebus.capability.priority` and listed properties (`relay-controllable`, PCS metadata) that had since moved to `switch` / `pcs`. Registered the real `energy.ebus.capability.load-shed` node (its topic is `load-shed/priority`), retired the `priority` entry, and authored the catalog.
- **capability/door** 0.1, **capability/output-island** 0.1, **capability/demand** 0.1, **capability/power-quality** 0.1 — canonicalized into versioned catalogs (completeness backlog).
- **capability/grid-forming** 0.1, **capability/power-flows** 0.1, **capability/shed-forecast** 0.1 — canonicalized into versioned catalogs (completeness backlog).
- **capability/grid** 0.1 — canonicalized the grid-boundary capability (grid-tied versus islanded, sensed utility-supply health, and the grid-forming-entity) into a versioned catalog; a MID publishes the islanding subset, a utility meter the supply-health subset (framework principle #7).
- **capability-catalog completeness policy** — every capability is potentially cross-cutting, so every capability now has (or requires) a standalone versioned catalog; a *device-defining* capability (e.g. `water-heater`) is the allowlisted exception. Added `tools/check-capability-catalogs.py` to enforce this and surface the remaining canonicalization backlog, and documented the policy in `capabilities/README.md`.

### Renamed

- **data-model/bess** 0.8 → 0.9 — normalized the `status` property names to the canonical catalog core: `communication` → `communication-state`, `device-fault` → `fault-state` (value sets aligned to `OK`/`DEGRADED`/`LOST`/`UNKNOWN` and `OK`/`FAULT`/`UNKNOWN`). **Breaking for BESS publishers and consumers.**

### Changed

- **data-model/water-heater** 0.2 → 0.3, **data-model/distribution-enclosure** 0.3 → 0.4, **data-model/utility-meter** 0.3 → 0.4 — the `soc` / `status` sections now reference the new catalogs, keeping only device-specific properties.
- **registry/capability-types** → 0.12 — `soc` / `status` re-pointed to their catalogs.
- **data-model/bess** 0.9 → 0.10, **data-model/distribution-enclosure** 0.4 → 0.5, **data-model/utility-meter** 0.4 → 0.5, **registry/capability-types** → 0.13 — the `grid` sections / row now reference `capabilities/grid.md`.
- **data-model/bess** 0.10 → 0.11, **data-model/distribution-enclosure** 0.5 → 0.6, **registry/capability-types** → 0.14 — `grid-forming` / `power-flows` / `shed-forecast` re-pointed to their catalogs.
- **data-model/bess** 0.11 → 0.12, **data-model/distribution-enclosure** 0.6 → 0.7, **data-model/utility-meter** 0.5 → 0.6, **registry/capability-types** → 0.15 — `door` / `output-island` / `demand` / `power-quality` re-pointed to their catalogs.
- **data-model/circuit** 0.1 → 0.2, **registry/capability-types** → 0.16, **framework** 0.5 → 0.6 — `load-shed` re-pointed to its catalog; the stale `capability.priority` identifier corrected to `capability.load-shed` in the registry and the framework capability list.

## 2026-07-10

### Added

- **capability/grid-event** 0.1 — new catalog: the grid's demand-response asks and grid-condition alerts (conservation, critical-peak, grid emergency) as one site-level, publish-only signal, parallel to `price` and `doe`. Anchored on OpenADR 3, IEEE 2030.5 DRLC, CTA-2045-B, and the CAISO Flex Alert / EEA hierarchy. (`4e752e7`)
- **capability/voltage-response** 0.1 — new catalog: the load-side undervoltage current-reduction (a Volt-Watt analog). Static undervoltage setpoint as the primary form, optional proportional curve; enforced through a new `pcs` `undervoltage-import-limit` slot. (`58415de`)
- **capability/flex** 0.1 — new canonical catalog for the flexible-load control-and-feedback surface (broken out of `water-heater.md`). (`a03fba6`)
- **process** — added `CHANGELOG.md`, the `conventions/` area with the `.ebus-spec.json` provenance-lockfile convention (`conventions/spec-provenance.md`), a generated `spec-manifest.json`, and `tools/gen-spec-manifest.py` (which generates the manifest and the README status table from document headers). Added `tools/drift-report.py`, which checks downstream `.ebus-spec.json` lockfiles against the manifest on the artifact, framework, and feature axes; the manifest now also carries the framework feature list.

### Renamed

- **capability/price** (was `tariff`) — the capability reports the price *value*, not the rate *structure* (rate structure is out of scope). Identifier is now `energy.ebus.capability.price`. (`b11ae8c`)
- **capability/flex** (was `dr`) — canonicalized and renamed. `event` → `request`, `dr-response` → `response`, `opted-out` boolean → `opt-out` four-way enum (NONE/LOCAL/GRID/ALL); `throttle-granularity` removed in favor of the device advertising its control surface in the `request` `$format` JSONSchema; added optional `request.cause`. **Breaking for publishers/controllers of the former `dr` capability.** (`a03fba6`)

### Changed

- **data-model/distribution-enclosure** 0.2 → 0.3 — may now publish `doe` (the acting-on envelope), `price`, `grid-event`, and `voltage-response`; the `pcs` import-limit family gains the `undervoltage-import-limit` slot. (`f663073`, `4e752e7`, `58415de`, `a03fba6`)
- **data-model/utility-meter** 0.2 → 0.3 — added the `price` section; trimmed `doe` to reference the catalog. (`b11ae8c`)
- **data-model/water-heater** 0.1 → 0.2 — the `dr` section is replaced by a reference to `capabilities/flex.md`, keeping only the water-heater-specific `LOAD_UP` thermal refinements. (`a03fba6`)
- **registry/capability-types** → 0.11 — rows added / repointed for `doe`, `price`, `grid-event`, `voltage-response`, and `flex`; `pcs` retermed.
- **framework** 0.4 → 0.5 — added the **Framework Features** list: canonical identifiers for the reusable framework mechanisms (parent-child model, `json` datatype, `$format` JSONSchema, settable properties, discovery, mTLS, proxy publishers), which downstream libraries declare via their provenance lockfile `supports`.

### Deferred

- **capability/policy-envelope** and **capability/settlement-proof** (CSIP3 PSSN) — deferred pending PSSN ratification. `settlement-proof` is to be rescoped to a lightweight compliance report, not a settlement-grade cryptographic proof.

## 2026-07-09

### Added

- **capability/doe** 0.1 — canonicalized the dynamic operating envelope into a catalog, and made it **publisher-agnostic**: a distribution enclosure may now publish it (the envelope it is acting on), not only a utility meter. (`f663073`, `4b308b6`)

### Changed

- **capability/pcs** — retired the coined "CSL" umbrella term; anchored on UL 3141 PIL / PEL and IEEE 2030.5 DOE. The import-limit family composes by `min()` (most-restrictive-wins). (`a409d43`)

## 2026-07-05

### Added

- **capabilities/ area** — introduced canonical cross-cutting capability catalogs (defined once, referenced by many data models); piloted **breaker** 0.1 and **switch** 0.1. (`71ee1ce`)
- **capability/meter** 0.1 — canonical metering catalog; reconciled the metering divergence across device types. (`a4fe552`)
- **capability/info** 0.1 — canonical shared-identity catalog. (`9c2cf02`)
- **capability/connection** 0.1 — canonical wiring-topology catalog; filled topology gaps (backup boundary, `feeds-role`, service / protection ratings). (`f6b7f77`)
- **data-model/circuit** 0.1 — extracted the circuit as its own container-neutral data model; models tandem / quad breakers as a feed circuit over per-load circuits. (`e0b9980`, `3af661a`)

### Changed

- **data-models (all)** — de-SPAN audit: demoted baked-in SPAN smart-panel MUSTs (metered / switchable invariants) to optional. (`9d48cca`)
- **data-model/distribution-enclosure** — PV / EVSE / MID identity profiles and the proxied BESS child now reference `capabilities/info.md` and `bess.md`. (`3178701`, `96fbca3`)

## 2026-07-04

### Added

- **extensions/ area** — added the extensions area and the `energy.ebus.imported` Homie extension; promoted `extensions/imported.md` to STABLE 1.0.0. (`7264ff3`, `a2ce6da`, `9ee4afd`)

## 2026-07-01

### Changed

- **capability/doe** — modeled the operating envelope as per-direction `json` arrays. (`a1cd3bd`)
- **data-model/distribution-enclosure** — redesigned the shed override as a bidirectional `asserted-islanding-state` enum; shed-override acceptance is comm-loss only. (`c01a0b1`, `201f535`)
- **data-model/bess** — modeled a coordinated multi-unit BESS on N circuits. (`b7c37c6`)
- **data-model/water-heater** — documented why the demand-response event uses the `json` datatype (atomicity). (`8cbb9af`)

## 2026-06-27

### Added

- **data-model/water-heater** 0.1 — new data model: a storage water heater as a controllable, grid-flexible load and dispatchable thermal-storage resource, with CTA-2045-B / Rheem-EcoNet / Matter / Cala worked example bindings. (`f6ad9cc`, `db0ae8e`)
- **data-model/pdu** 0.1 and **data-model/outlet** 0.1 — new data models for plug-in power distribution units and their outlets. (`d46fe7f`)

### Changed

- **data-model/bess** — modeled plug-in batteries and UPS devices (the device-output island). (`d46fe7f`)

## 2026-06-08

### Changed

- **integration-guide/utility-meter-and-distribution-enclosure** — honour the DOE valid-until window by default. (`dbb4755`)
- **data-model/utility-meter** — `doe` power-limit properties are integers, not floats. (`7d6c120`)

## 2026-06-07

### Added

- **data-model/bess** 0.6 — landed the BESS (battery energy storage system) data model. (`f78b754`, `040f479`)
- **device.bridge** — added `energy.ebus.device.bridge`, a device type for standalone proxy hosts. (`e8d4949`, `6b3bd05`)
- Repository governance: added `CONTRIBUTING.md`; expanded the README Governance section and status table. (`336eefe`, `42b239d`)

### Changed

- Established **"Electrification Bus"** as the canonical project name, with "eBus" as the nickname. (`a553c4c`)
- Pre-public audit pass and `NOTICES.md` trademark section. (`38a35b9`, `84bd449`)

## 2026-06-06

### Added

- **framework** 0.3.0 — landed the framework specification on main (renamed from `specification.md`): network architecture, discovery (mDNS, with an `auth_methods` TXT record), messaging (MQTT / Homie), broker hosting, TLS / mTLS client authentication, proxy publishers, and design principles. (`893e8c7`, `26c636f`, `a9f142d`, `b1233d7`)
- **data-model/utility-meter** — landed the utility-meter data model and the utility-meter ↔ distribution-enclosure integration guide; registered its capability types. (`1cbd614`, `eb50d04`)
- **registry/external-id-schemes** 0.1 — new registry. (`4e3dac9`)
- **capability/doe** — added to the utility meter for utility-signaled service limits, with the doe → pcs integration guide. (`27d44c9`, `f5386d9`)

### Changed

- **registry/circuit-tags** — broadened applicability beyond circuits. (`657d75b`)
- Dropped the `capability.` prefix from Homie node IDs across the spec; pinned the Homie node-ID character set. (`392390b`, `43a2413`)

## 2026-06-05

### Added

- **data-model/utility-meter** 0.1 (exploratory) — first draft of the utility-meter data model. (`7462fe9`)

## Earlier

The earliest framework working draft predates this window; see `git log` for full detail.
