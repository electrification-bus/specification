# Contributing to the Electrification Bus Specification

Thanks for your interest in contributing! This repo holds the [Electrification Bus](https://ebus.energy) (eBus) specification documents — the framework spec, per-device-class data models, registries of device types / capability types / circuit tags / external-id schemes, and informative integration guides.

## How to contribute

### Discussions

Use [Discussions](https://github.com/electrification-bus/specification/discussions) for:

- Open-ended questions about the spec's design or intent
- Proposed new device types, capability types, or registry entries (worth discussing before drafting a data-model document)
- Cross-spec design questions (how should X interact with Y? what does the spec say about Z?)
- Asking other implementers how they're handling a specific case
- Thinking out loud about a proposed change before scoping it

Discussions are open-ended — a good place to align on direction before something becomes a concrete change. Aligned outcomes from a Discussion often turn into one or more Issues or pull requests.

### Issues

Use [Issues](https://github.com/electrification-bus/specification/issues) for actionable changes:

- Specification errors, omissions, ambiguities, or contradictions
- Stale cross-references, outdated examples, or links that no longer resolve
- Property contracts that don't reflect implementation reality, where a concrete behavior change is intended
- Discussion outcomes that have alignment and a clear scope

If you're not sure whether something is an Issue or a Discussion, start with a Discussion — we can convert it later.

### Pull requests

Pull requests are welcome.

- For small fixes (typos, broken links, version bumps, status-table updates, clarifying prose tweaks), open a PR directly.
- For substantive changes (new data-model documents, new capability types, new registries, normative changes to existing specs), open a Discussion or Issue first so we can align on scope before you invest the effort.
- Match the existing tone and structure. Normative spec prose uses IETF-style language (MUST / SHOULD / MAY per [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119)) and avoids vendor-specific terminology. Concrete vendor examples are welcome in non-normative sections (illustrative examples, integration guides) as long as they're clearly labeled and the normative property contracts remain vendor-neutral.
- New capability types and device types should follow the format rules and addition process documented in the relevant registry (`registries/device-types.md`, `registries/capability-types.md`).
- One commit per logical change is fine; we don't require squash or any particular branch naming.

## Versioning, the changelog, and generated files

Each versioned document (data model, capability catalog, registry, framework, integration guide, convention) carries a `**Status:**` / `**Version:**` / `**Date:**` header. **Those headers are the single source of truth for artifact versions.**

When you change a document's content:

1. Bump its `**Version:**` and `**Date:**` (during the current rapid-development phase, any notable change warrants at least a minor bump).
2. Add an entry to [`CHANGELOG.md`](CHANGELOG.md), tagged with the affected artifact and a category (Added / Changed / Renamed / Deprecated / Removed / Fixed).
3. Regenerate the derived files, which are **generated, not hand-edited**: [`spec-manifest.json`](spec-manifest.json) (the machine-readable version manifest) and the [README status table](README.md#status) (between its generated-content markers):

   ```bash
   python3 tools/gen-spec-manifest.py          # regenerate both from the headers
   python3 tools/gen-spec-manifest.py --check  # verify they are current (non-zero if stale)
   ```

4. If you maintain downstream implementations, check them for drift before wrapping up: `python3 tools/drift-report.py --scan <your repo roots>` (see [`tools/README.md`](tools/README.md)). It reports which downstreams are now behind on the artifacts, framework version, or features you changed, so you can file or update their sync issues. Your fleet is a runtime argument (scan roots or a private `--config` file), never committed here.

Do not edit `spec-manifest.json` or the README status table by hand; run `--check` before pushing (and in CI once configured) so neither drifts from the document headers. Downstream implementations record which versions they build against via the [`.ebus-spec.json`](conventions/spec-provenance.md) provenance lockfile.

## Code of conduct

Be respectful and constructive. Electrification Bus is an open-standards project that depends on contributions from vendors, integrators, and consumers across the home-energy-infrastructure ecosystem. We appreciate everyone who takes the time to file an issue, start a discussion, or send a pull request.

## Maintenance posture

The Electrification Bus specification is an active draft. Updates and maintenance, including responses to issues filed on GitHub, will take place on an "as time and resources permit" basis. The specification's long-term home is intended to be an established open-standards organization — see the [main README's §Governance](README.md#governance) for context, including the criteria the project applies when evaluating potential homes.
