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

## Code of conduct

Be respectful and constructive. Electrification Bus is an open-standards project that depends on contributions from vendors, integrators, and consumers across the home-energy-infrastructure ecosystem. We appreciate everyone who takes the time to file an issue, start a discussion, or send a pull request.

## Maintenance posture

The Electrification Bus specification is an active draft. Updates and maintenance, including responses to issues filed on GitHub, will take place on an "as time and resources permit" basis. The specification's long-term home is intended to be an established open-standards organization — see the [main README's §Governance](README.md#governance) for context, including the criteria the project applies when evaluating potential homes.
