# Electrification Bus Specification

**Status:** DRAFT
**Version:** 0.4
**Date:** 2026-07-01

---

## What is Electrification Bus?

Electrification Bus (eBus for short) is an open interoperability framework for Home Energy Infrastructure (HEI) devices — smart panels, batteries, inverters, HEMS, meters, generators, and transfer switches.

Electrification Bus composes existing, well-known protocols — **mDNS**, **MQTT** (with the **Homie Convention**), and **HTTP/REST** — in a structured way that enables automatic discovery, self-describing messaging, and local-first coordination. Most developers already know these protocols; eBus defines how to use them together so that devices from different manufacturers can interoperate without custom integration work.

### Terminology

- **eBus entity** — A network host implementing the device role, the controller role, the broker-host role, or any combination.
- **Device role** — Publishes Homie devices to the MQTT broker, representing HEI device state and capabilities.
- **Controller role** — Discovers and subscribes to Homie devices, reads state, and issues `/set` commands.
- **Broker-host role** — Provides an MQTT broker for eBus entities to publish to and subscribe through. May implement device or controller roles in addition (co-resident broker host — typical for products like a SPAN panel that hosts its own broker), or stand alone (a dedicated broker host that is not itself a device — e.g., a NUC or Raspberry Pi running just the broker).
- **Native publisher** — A device-role entity that publishes a Homie device representing itself (or, for a vendor-built publisher, representing one of the vendor's own products).
- **Proxy publisher** — A device-role entity that publishes a Homie device on behalf of a non-eBus-native device — typically bridging from the device's native protocol (Modbus, Matter, CTA-2045, vendor cloud API, etc.). The published representation is a *proxy*. Disambiguation between proxy and native publication is defined in [`data-models/proxy.md`](data-models/proxy.md).
- **eBus consumer** (or just **consumer**): a controller-role entity that consumes eBus data (it discovers and subscribes to Homie devices, reads their state, and may issue `/set` commands). Includes controllers, dashboards, energy-management systems (EMS / HEMS), DERMS adapters, and analytics jobs. This is distinct from the energy-domain sense of *consumer* (the ratepayer or homeowner), which is not an eBus role; where confusion with that sense is likely, the specifications write **eBus consumer**.

### Conformance Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" are to be interpreted as described in [RFC 2119][rfc2119].

---

## Relationship to Homie

Electrification Bus uses three well-known protocols — MQTT for messaging, mDNS for discovery, and HTTP/REST for configuration — and layers the [Homie Convention](https://homieiot.github.io/specification/) (currently version 5; a general-purpose IoT convention for self-describing devices) on top of MQTT to provide structured device representations. Within that stack, the eBus value-add is HEI specialization: HEI-specific device types (`energy.ebus.device.*`), capability types (`energy.ebus.capability.*`), and the property catalogs within them. Homie features (the parent-child device model, the `$state` lifecycle, the `$description` mutability rules, the `$settable` attribute, retained-message semantics) belong to the Homie Convention and are credited to Homie, not to eBus.

Schema vocabulary defined by eBus is vendor-neutral; vendor trademarks and product-specific terminology are explicitly excluded from the schema. The Homie `name` string attribute on each property is implementation-defined and may carry vendor-specific labels — its contents are presentation, not part of the standard.

This division of responsibilities is the precise normative line. Any concept named in the eBus device-type or capability-type registries is eBus's responsibility; anything in the Homie Convention itself is Homie's. Where the two interact (the way eBus device structures are encoded as Homie `$description` trees, the way Homie's `$type` attribute carries eBus type identifiers, the way Homie lifecycle states cascade across eBus parent / child relationships), the encoding follows the Homie Convention with the eBus specialization adding only the HEI-specific vocabulary.

Beyond specializing the Homie vocabulary, Electrification Bus MAY also define **Homie extensions** under its `energy.ebus.<suffix>` namespace (distinct from the `energy.ebus.device.*` and `energy.ebus.capability.*` type namespaces). Each extension is documented in [`extensions/`](extensions/README.md) following the Homie extension convention; a device advertises an extension by adding its versioned entry (`<id>:<version>:[<homie-versions>]`) to the `extensions` array of its Homie `$description`. Extensions are the mechanism by which eBus contributes reusable, Homie-general capabilities back to the broader Homie ecosystem, and extension documents are individually licensed to permit that (see [`extensions/README.md`](extensions/README.md)).

---

## Requirements

This section is the normative core of the eBus specification. Each requirement is identified by section for cross-reference with the detailed guidance that follows.

### Networking

1. An eBus entity MUST support at least one IP network interface (Ethernet or Wi-Fi).
2. An eBus entity with active Ethernet SHOULD disable Wi-Fi, unless configured otherwise.
3. An eBus entity SHOULD support network configuration through its configuration mechanism.
4. An eBus entity with only an unconfigured Wi-Fi interface MAY provide a hosted AP for Wi-Fi provisioning.

### mDNS Discovery

5. An eBus entity MUST claim a unique `.local` mDNS hostname (SHOULD incorporate a unique identifier such as a MAC address or serial number).
6. An eBus entity MUST advertise `_ebus._tcp` and `_device-info._tcp` metadata services.
7. An eBus entity that hosts an MQTT broker MUST advertise it via mDNS (`_secure-mqtt._tcp`, `_mqtt._tcp`, `_mqtt-ws._tcp`, `_mqtt-wss._tcp` as applicable).
8. An eBus entity that offers an HTTP REST API MUST advertise it via mDNS (`_http._tcp` and/or `_https._tcp`).
9. An eBus entity that does not self-host a broker MUST discover a broker via mDNS.

### MQTT / Homie

10. An eBus entity SHOULD use MQTT 5.0; MAY use MQTT 3.1.1.
11. eBus uses `ebus` as the Homie topic domain: `ebus/5/{device-id}/...`
12. An eBus device-role entity MUST comply with the Homie Convention v5.0 for device description, lifecycle, property publication, datatypes, and retained message semantics.
13. An eBus entity SHOULD use QoS 2 for property value publications; QoS 0 for `/set` commands.
14. eBus device types use the `energy.ebus.device.*` namespace; eBus capability types (the `$type` attribute on Homie nodes) use the parallel `energy.ebus.capability.*` namespace. Manufacturers MAY use their own namespace prefix for either.

### REST API and Configuration

15. MQTT is the primary protocol for real-time state and control; REST is complementary for configuration, administration, and bootstrap.
16. An eBus entity SHOULD have baked-in default configuration; dynamic configuration via REST SHOULD override defaults.
17. An eBus entity SHOULD provide an HTTP REST API for configuration and administration.
18. An eBus entity's REST API SHOULD be documented via OpenAPI, served by the entity over HTTP.
19. An eBus entity's OpenAPI spec SHOULD tag endpoints that serve eBus-defined functions with the corresponding `ebus:*` tag so that clients can discover how to call them programmatically.
20. An eBus entity SHOULD provide a registration endpoint that exchanges a device passphrase for API credentials and MQTT broker connection details.
21. An eBus entity MAY provide an HTTP GUI; the GUI SHOULD use the REST API as its backend.

### MQTT Broker Configuration

22. An eBus entity's configuration SHOULD include a broker URL and a broker mode: `configured-only`, `discovery-with-fallback`, or `discovery-only` (the default).

### Broker-Host

23. A broker-host entity MUST include `broker-host` in the `roles` TXT record of its `_ebus._tcp` mDNS advertisement, in addition to any other roles it implements.
24. A broker-host entity SHOULD authenticate clients connecting to its broker. The authentication mechanism is implementation-defined; common patterns are a REST registration endpoint hosted by the broker host (same shape as §"Registration Endpoint"), pre-configured credentials, or mTLS client-certificate authentication (per §"mTLS Client Authentication (Optional)").

### TLS and Security

25. An eBus entity SHOULD use TLS for MQTT and HTTP connections; MAY fall back to non-TLS if not feasible.
26. When TLS is supported, TLS 1.2 or later MUST be used; TLS 1.3 is RECOMMENDED.
27. An eBus entity whose TLS certificate is not publicly verifiable (typically self-signed) SHOULD provide a REST endpoint to download its CA certificate (unauthenticated).
28. An eBus entity that connects to an MQTT broker whose TLS certificate is not publicly verifiable SHOULD provide a REST endpoint to upload that broker's CA certificate.
29. An eBus entity that supports mTLS client-certificate authentication SHOULD provide an authenticated REST endpoint to upload trust-anchor CA certificates against which inbound client certificates are validated.

### OTA Firmware Updates

30. An eBus entity SHOULD support a REST endpoint to initiate OTA firmware updates.
31. The OTA update server URL SHOULD be obtained from configuration.
32. An OTA update MUST NOT permanently brick the device (rollback or dual-partition boot SHOULD be supported).

### Proxy Publishers

33. A proxy publisher is a device-role entity that publishes a Homie device representation on behalf of a non-eBus-native device.
34. A proxy publisher's Homie device MUST be functionally equivalent to a native eBus publication of the same device (same property contracts, same `$state` lifecycle, same discovery) and MAY be discoverable as a proxy via its `root.$type` per [`data-models/proxy.md`](data-models/proxy.md).
35. A proxy publisher that bridges from a vendor cloud API SHOULD cache data locally and serve last-known state when cloud connectivity is unavailable.

---

## Architecture Overview

```
┌───────────────────────────────────────────────────┐
│          Application / Coordination               │
│ (HEMS, automation rules, energy optimization)     │
├─────────────────────────┬─────────────────────────┤
│ Messaging & Data Model  │ REST / HTTP API         │
│ (Homie/MQTT)            │ (configuration,         │
│ pub/sub, commands,      │  administration,        │
│ self-describing topics  │  OpenAPI, OTA)          │
├─────────────────────────┴─────────────────────────┤
│          Discovery (mDNS / DNS-SD)                │
│ (broker, device & service advertisement/discovery)│
├───────────────────────────────────────────────────┤
│               IP Networking                       │
│ (Ethernet, Wi-Fi, Thread)                         │
└───────────────────────────────────────────────────┘
```

**Lifecycle:** Once an eBus entity has an IP address and has claimed its mDNS hostname, it discovers (or provides) an MQTT broker via mDNS and connects. From there, the entity follows the Homie device lifecycle for publishing state and coordinating with other entities.

---

## Design Principles

The following principles guide the structure of every eBus data model and the framework itself. Individual data-model documents may extend or clarify them but should not contradict them. Data-model documents reference these principles by number.

1. **Homie devices represent physical things.** If it could maintain its own independent Homie representation, it is a Homie device.
2. **Homie nodes represent capabilities.** A node carries what a Homie device *can do* (meter, switch, sense), not what physical component it is.
3. **Publish what you have, omit what you don't.** Absent properties mean "unknown" or "not applicable," not a sentinel-encoded value.
4. **Parent aggregates children.** The parent device exposes system-level aggregates; per-component detail lives on the relevant child.
5. **Standard capability types are reused** across device classes.
6. **Proxying is first-class.** eBus supports *proxying* — publication of an eBus representation by a publisher other than the device itself — as a peer to native publishing. The consumer-facing surface is identical for both forms, and capability and property contracts are written so that any conformant publisher (native or proxy) can satisfy them. See [`data-models/proxy.md`](data-models/proxy.md) for the full proxy specification (disambiguation between proxied and native representations, device-ID convention, and where proxy-side knowledge lives).
7. **Properties belong on the device that authoritatively knows them**, even when proxying makes other placements convenient. A property that could not be populated by a non-proxying publisher belongs elsewhere. This is a direct consequence of principle 6: the property contract must be satisfiable by *any* conformant publisher, native or proxy, and a property smuggled onto an adjacent device because only the proxy happens to know it breaks the contract for the native publisher.
8. **Forward compatibility is a design goal.** The data model defines slots for richer data than current implementations capture. Properties are MAY-level by default; datatypes are chosen for extensibility (open-vocabulary strings, not hardcoded enums where the value space is open); capabilities accept new properties additively. The model serves as a contract for the evolving ecosystem, not as a transcript of any one current feature set.
9. **Multi-instance from the outset.** Identifying attributes and inter-device relationships are recorded per-device rather than enumerated as class-level properties on a containing parent, so N instances of any class can coexist without model changes (for example, multiple BESSs, PV inverters, or EVSEs in a single distribution enclosure).
10. **Scalars by default; `json` only for atomic compounds.** Property values use scalar datatypes (`float`, `integer`, `enum`, `datetime`, and so on) by default: they are directly readable, chartable, and validatable by generic Homie tooling. The `json` datatype is used sparingly, and only where a value is a compound whose parts must be read or applied as a single atomic unit. Splitting such a value across separately-retained scalar topics would let a consumer observe a torn state: parts from different updates, with no way to tell which belong together, or when each was published. Current uses: the water-heater `dr` event and the utility-meter `doe` per-direction envelope.

---

## Detail: Networking

### Network Interfaces

Common interface types:

- **Ethernet** — Preferred for reliability and bandwidth.
- **Wi-Fi** — Flexibility for devices without wired connectivity.
- **Thread** — MAY be supported for low-power mesh networking.

### Fallback AP Mode

An entity with only an unconfigured Wi-Fi interface MAY provide a hosted access point (AP) for initial SSID and password provisioning. The AP SHOULD be disabled once the entity connects to a configured network.

---

## Detail: mDNS Discovery

### Hostname

Every eBus entity MUST claim a unique `.local` mDNS hostname. The hostname SHOULD incorporate a device-unique identifier (MAC address, serial number) and MAY include a device type or user-assigned name.

**Example:** `span-nt-2025-c123y.local`

### `_ebus._tcp` Service

Every eBus entity MUST advertise this service to make itself discoverable.

**Required TXT records:**

| Key | Description | Example |
|-----|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `ebus_version` | eBus spec version | `0.2` |
| `roles` | Comma-separated: `device`, `controller`, `broker-host` | `device,broker-host` |
| `device_id` | Unique device identifier | `nt-2025-c123y` |

**Recommended TXT records:**

| Key | Description | Example |
|-----|-------------|---------|
| `device_type` | Manufacturer device type | `span-panel` |
| `name` | Human-readable name | `Main Panel` |
| `manufacturer` | Manufacturer | `SPAN` |
| `model` | Model identifier | `MAIN-32` |
| `fw_version` | Firmware version | `24.5.1` |
| `register` | REST endpoint to exchange a device secret for API token and/or MQTT broker credentials | `/api/v1/auth/register` |
| `broker_ca` | Authenticated REST endpoint to download the MQTT broker's self-signed CA certificate | `/api/v1/certificate/broker-ca` |
| `auth_methods` | Comma-separated list of authentication methods this entity supports. Defined values: `passphrase` (REST registration endpoint, see `register` TXT record and §"Registration Endpoint"); `preconfigured` (credentials managed out-of-band — admin UI, config file, vendor onboarding); `mtls` (mTLS client-certificate authentication — see §"mTLS Client Authentication (Optional)"). An entity MAY publish multiple values when it supports more than one method concurrently. Lets a controller pick a supported method without round-tripping to the OpenAPI spec. | `passphrase,mtls` |

### `_device-info._tcp` Service

Every eBus entity MUST advertise this service. The `_device-info._tcp` name is [reserved by IANA](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=device-info) for DNS-SD device info.

**Required TXT records:**

| Key | Description | Example |
|-----|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `manufacturer` | Device manufacturer | `SPAN` |
| `model` | Device model | `MAIN-32` |
| `serial_number` | Device serial number | `nt-2025-c123y` |

**Recommended TXT records:**

| Key | Description | Example |
|-----|-------------|---------|
| `fw_version` | Firmware version | `24.5.1` |
| `hw_version` | Hardware version | `2.0` |
| `os_version` | OS or platform version | `esp-idf 5.1` |
| `mac` | Primary MAC address (no colons) | `a0b1c2d3e4f5` |

### HTTP API Advertisement (`_http._tcp` / `_https._tcp`)

An entity offering an HTTP REST API or GUI MUST advertise it.

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `path` | API base path | `/api/v1` |
| `version` | API version | `1.0` |
| `device_id` | Device identifier | `nt-2025-c123y` |
| `device_type` | Device type | `span-panel` |
| `openapi` | Path to OpenAPI spec (RECOMMENDED) | `/api/v1/docs` |

### MQTT Broker Advertisement

An entity hosting an MQTT broker MUST advertise it. Advertise one or more of the following:

**`_secure-mqtt._tcp`** (MQTT over TLS, port 8883):

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `protocol` | MQTT protocol version | `mqtt-v5` or `mqtt-v3.1.1` |
| `broker` | Broker hostname | `span-nt-2025-c123y.local` |
| `device_id` | Broker host device ID | `nt-2025-c123y` |

**`_mqtt-ws._tcp`** (MQTT over WebSocket, typically port 9001) and **`_mqtt-wss._tcp`** (MQTT over secure WebSocket, typically port 9002):

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `protocol` | MQTT protocol version | `mqtt-v5` or `mqtt-v3.1.1` |
| `path` | WebSocket endpoint path | `/mqtt` |
| `subprotocol` | WebSocket subprotocol | `mqtt` |

**`_mqtt._tcp`** (plain MQTT, port 1883 — use only when TLS is not feasible):

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `protocol` | MQTT protocol version | `mqtt-v5` or `mqtt-v3.1.1` |

### Broker Discovery

An entity that does not self-host a broker MUST browse mDNS for brokers, preferring secured transports:

1. `_secure-mqtt._tcp` (preferred)
2. `_mqtt-wss._tcp`
3. `_mqtt-ws._tcp`
4. `_mqtt._tcp` (fallback)

If multiple brokers are discovered, automatic selection between them is **out of scope for this specification**. Entities in multi-broker deployments SHOULD be configured with the URL of the intended broker (see §"MQTT Broker Configuration"). Implementations MAY apply vendor-specific selection heuristics in the absence of configuration, but consumers MUST NOT assume a particular automatic-resolution behavior. If no broker is found, the entity SHOULD retry periodically (MAY use exponential backoff).

---

## Detail: MQTT / Homie

### Topic Domain

eBus uses `ebus` as the Homie topic domain:

```
ebus/5/{device-id}/...
```

Where `ebus` is the domain prefix, `5` is the Homie major version, and `{device-id}` is a unique identifier conforming to Homie topic ID rules (SHOULD be derived from a hardware identifier).

### Homie Convention Compliance

Device-role entities MUST comply with the [Homie Convention v5.0][homie5] for all aspects: device description, device lifecycle, property publication, datatypes, formats, and retained message semantics. The Homie Convention specification is the normative reference.

### Controller Discovery

A controller discovers devices by subscribing to:

```
ebus/5/+/$state
```

Upon receiving a `$state` message for an unknown device, the controller retrieves the device's `$description` and subscribes to property topics as needed.

### Device and Node Types

The Homie `$type` attribute on devices and nodes uses a flat, reverse-domain-style naming convention. eBus reserves two prefixes:

- `energy.ebus.device.*` — eBus-standard **device** types (the `$type` of the root or child device).
- `energy.ebus.capability.*` — eBus-standard **capability** types (the `$type` of a Homie node).

**Example device types:**

```
energy.ebus.device.distribution-enclosure
energy.ebus.device.circuit
energy.ebus.device.lugs
energy.ebus.device.mid
energy.ebus.device.bess
energy.ebus.device.pv
energy.ebus.device.evse
energy.ebus.device.utility-meter
energy.ebus.device.generator
energy.ebus.device.hems
```

Device types are flat — a circuit is `energy.ebus.device.circuit`, not `energy.ebus.device.distribution-enclosure.circuit`. Containment is expressed via the Homie 5 parent-child topology (see §"Device Topology" below), not via dotted sub-typing of the device-type identifier.

**Example capability types:**

```
energy.ebus.capability.info
energy.ebus.capability.meter
energy.ebus.capability.status
energy.ebus.capability.connection
energy.ebus.capability.grid
energy.ebus.capability.soc
energy.ebus.capability.switch
energy.ebus.capability.power-flows
energy.ebus.capability.pcs
energy.ebus.capability.priority
energy.ebus.capability.door
energy.ebus.capability.shed
energy.ebus.capability.shed-forecast
```

Both registries — device types and capability types — are maintained as canonical lists in this repository under [`registries/`](registries/) (specifically [`registries/device-types.md`](registries/device-types.md) and [`registries/capability-types.md`](registries/capability-types.md)). Per-device-class data-model documents under [`data-models/`](data-models/) define the required and optional capabilities and properties for each device type (e.g., [`data-models/distribution-enclosure.md`](data-models/distribution-enclosure.md), [`data-models/utility-meter.md`](data-models/utility-meter.md), [`data-models/proxy.md`](data-models/proxy.md)).

Manufacturers MAY define custom types using their own namespace prefix (e.g., `com.acme.device.widget`, `com.acme.capability.thermal-zone`).

**Node IDs vs. node types.** A node's *type* is the value of its Homie `$type` attribute and uses the dotted reverse-domain form above (e.g., `energy.ebus.capability.meter`). A node's *ID* — the segment that appears in the MQTT topic path between the device-id and the property-id (`ebus/5/<device-id>/<node-id>/<property-id>`) — MUST conform to Homie 5's topic-ID character set: lowercase ASCII letters, digits, and hyphens; the `.` character is NOT permitted. The conventional choice is to use the rightmost segment of the type as the ID (e.g., a node of type `energy.ebus.capability.meter` has node-ID `meter`). Data-model authors MUST follow this convention; reviewers MUST reject node IDs containing `.` (the dotted form is for `$type` values, not IDs).

### Device Topology

eBus devices form a parent-child hierarchy using Homie 5's `$description.children`, `$description.root`, and `$description.parent` attributes. A parent (root) device represents a physical container (e.g., a distribution enclosure); its child devices represent meaningful sub-components (e.g., individual circuits, lugs, an integrated MID) or related devices the parent publishes on behalf of (e.g., a proxied BESS that the enclosure publishes from its own internal integration).

Children of a root device share the root's MQTT connection and lifecycle: the root's Last Will and Testament cascades a `lost` `$state` to every child in its tree per Homie 5. Consumers determine effective child state by consulting both the child's own `$state` and its root's `$state`.

The Homie 5 specification is the normative reference for the parent-child mechanics. eBus data-model documents specify the device-class-specific topology rules — which sub-components are children, what their device types are, how the root aggregates them. The canonical worked example is [`data-models/distribution-enclosure.md`](data-models/distribution-enclosure.md) (enclosure as root; circuits, lugs, MID as children; proxied DERs as additional children).

### Units

Properties representing physical measurements MUST include a `unit` attribute, using units defined by the [Homie Convention specification][homie5].

---

## Detail: Broker Hosts

The broker-host role provides an MQTT broker for eBus entities. A broker host may be **co-resident** with a device-role entity (the common pattern: a SPAN panel hosts its own broker alongside publishing its own enclosure device), or **standalone** (a dedicated broker host on a NUC, Raspberry Pi, NAS, or similar — useful in deployments where multiple eBus devices share one broker, or where the participating device-role entities cannot themselves host a broker).

### Discovery

A broker host advertises itself like any other eBus entity:

- An mDNS `.local` hostname (per §"Hostname" above).
- An `_ebus._tcp` service whose `roles` TXT record includes `broker-host`. Standalone broker hosts publish `roles=broker-host`; co-resident broker hosts publish e.g. `roles=device,broker-host`.
- A `_device-info._tcp` service (manufacturer, model, serial).

And, per §"MQTT Broker Advertisement," advertises the broker itself via `_secure-mqtt._tcp` (preferred) and/or `_mqtt-wss._tcp`, `_mqtt-ws._tcp`, `_mqtt._tcp` as applicable.

### Client Authentication

A broker host SHOULD authenticate clients connecting to its broker. Three patterns are conventional, each suited to a different deployment shape:

**Broker-issued credentials.** The broker host runs its own REST registration endpoint with the same shape as §"Registration Endpoint" above. Clients exchange a broker-host-issued bootstrap secret (a passphrase printed on the enclosure, a token shown on a setup screen, a value handed out during vendor onboarding, etc.) for MQTT credentials. The specific bootstrap-secret format and provisioning flow are implementation-defined; only the registration-endpoint shape (`POST /…/auth/register` returning `accessToken`, `ebusBrokerUsername`, `ebusBrokerPassword`, broker host and ports) is specified. Best fit for homeowner-installable broker hosts where each home has its own setup flow.

**Pre-configured credentials.** The broker host's accounts are managed out-of-band (admin UI, config file, vendor onboarding portal). Clients are configured with their credentials at provisioning time. Best fit for enterprise / professional-installer scenarios where credentials can be distributed via a managed deployment system.

**mTLS client-certificate authentication.** The broker host validates inbound client certificates against one or more configured trust-anchor CAs (per §"mTLS Client Authentication (Optional)" below). Best fit for cross-OEM integration scenarios where two or more OEMs have arranged a CA trust relationship and want partner devices to authenticate to the broker without homeowner-mediated provisioning.

A broker host MAY support more than one of these patterns concurrently.

### Authorization (Broker-Side ACLs)

When a broker host enforces topic-level access controls (subscribe / publish ACLs), it SHOULD use the role taxonomy defined in §"mTLS Client Authentication (Optional)" (`observer`, `sensor`, `controller`, `automation`, `admin`). The mapping from authenticated identity to role is broker-implementation-defined. Reusing the same taxonomy across mTLS and broker ACLs lets consumers reason about access control with one vocabulary regardless of where it is enforced.

### Standalone vs. Co-Resident

In a **co-resident** deployment, the broker host also implements the device role (e.g., the SPAN panel hosts a broker AND publishes its own enclosure device). A single REST registration endpoint typically serves both roles — one exchange of the broker host's bootstrap secret yields both REST API credentials and MQTT credentials.

In a **standalone** deployment, the broker host implements only the broker-host role. It publishes no Homie device of its own. Its REST endpoint surface is narrower — primarily a registration endpoint for MQTT credentials, plus credential-management endpoints for ongoing administration. From a consumer's perspective the mDNS discovery flow is identical to the co-resident case: browse for brokers via `_secure-mqtt._tcp` (et al.) and for entities via `_ebus._tcp`. A controller need not know whether the broker host is also a device-role entity.

### Multi-Broker LANs

A LAN MAY host more than one broker — for example, three SPAN panels in a single home each running their own co-resident broker; a single-vendor install plus a separate standalone broker for a different set of devices; or a cross-vendor install where each vendor's gateway runs its own broker for its own devices.

This specification does not attempt to define automatic resolution between multiple brokers on a LAN (see §"Broker Discovery"). Entities in multi-broker deployments SHOULD be configured with the URL of their intended broker. Each broker is its own Homie tree — a controller that needs to observe devices across multiple brokers connects to each broker separately and stitches the per-broker views together in its application layer. Cross-broker federation (a single logical Homie tree spanning multiple brokers) is a possible future direction but is not in scope here.

---

## Detail: REST API and Configuration

### When to Use REST vs. MQTT

**Use REST for:**

- Infrequent operations (initial setup, reconfiguration)
- Request/response semantics (authentication, file uploads/downloads)
- Pre-MQTT bootstrap (credential provisioning)
- Large payloads (certificates, firmware, OpenAPI specs)
- Browser accessibility (configuration GUIs, API docs)

**Use MQTT for:**

- Continuous/frequent state updates (sensor readings, power measurements)
- Fan-out to multiple subscribers
- Retained messages (new subscribers get current state immediately)
- Device lifecycle tracking (LWT for disconnect detection)

### Configuration Model

1. **Baked-in defaults** — Compiled into firmware; sensible defaults for standalone operation.
2. **Dynamic configuration** — Applied at runtime via REST API; overrides baked-in defaults.

### HTTP Server

An eBus entity SHOULD provide an HTTP server on both HTTP (port 80) and HTTPS (port 443) when TLS is supported. JSON ([RFC 8259][rfc8259]) MUST be used for REST API request and response bodies.

Offering both HTTP and HTTPS is deliberate: HTTPS provides security, but HTTP ensures accessibility when TLS certificate configuration is an obstacle (e.g., during a power outage when a homeowner needs immediate browser access).

### OpenAPI Documentation

The REST API SHOULD be documented using an [OpenAPI][openapi] specification, served by the entity via HTTP (e.g., `GET /api/v1/docs`). The mDNS HTTP advertisement SHOULD include an `openapi` TXT record pointing to this path.

### OpenAPI Tags for eBus Endpoints

An eBus entity's OpenAPI spec SHOULD use `ebus:*` tags on operations that serve eBus-defined functions. This complements mDNS discovery: the mDNS TXT records tell a client *where* the endpoint is, and the OpenAPI tags tell it *how* to call the endpoint (method, request body, auth requirements, response schema).

**Standard eBus tags:**

| Tag | Purpose |
|-----|---------|
| `ebus:register` | Exchange a device secret for API token and/or MQTT broker credentials |
| `ebus:broker-ca` | Download the MQTT broker's self-signed CA certificate |
| `ebus:device-info` | Retrieve device identity and status information |
| `ebus:network-config` | Network interface configuration |
| `ebus:broker-config` | MQTT broker connection configuration |
| `ebus:certificate` | TLS certificate management (upload/download) |
| `ebus:ota` | OTA firmware update initiation |

Tags MUST be declared in the top-level `tags` array of the OpenAPI document. A client can fetch the OpenAPI spec, filter operations by `ebus:*` tags, and programmatically construct the correct API calls without any eBus-specific client code.

**Example (OpenAPI fragment):**

```json
{
  "tags": [
    {
      "name": "ebus:register",
      "description": "Exchange device secret for API token and MQTT broker credentials"
    },
    {
      "name": "ebus:broker-ca",
      "description": "Download MQTT broker's self-signed CA certificate"
    }
  ],
  "paths": {
    "/api/v1/auth/register": {
      "post": {
        "tags": ["ebus:register"],
        "summary": "Register and obtain credentials",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "password": { "type": "string" }
                },
                "required": ["password"]
              }
            }
          }
        }
      }
    },
    "/api/v1/certificate/broker-ca": {
      "get": {
        "tags": ["ebus:broker-ca"],
        "summary": "Download broker CA certificate",
        "security": [{ "bearerAuth": [] }]
      }
    }
  }
}
```

### Registration Endpoint

An entity requiring authentication SHOULD provide a registration endpoint that exchanges a device-specific passphrase (printed on the device label or shown on an on-device screen) for credentials. The path to this endpoint is discoverable via the `register` TXT record in the entity's `_ebus._tcp` mDNS advertisement.

```
POST /api/v1/auth/register
Content-Type: application/json

{"password": "<device-passphrase>"}
```

**Response:**

```json
{
  "accessToken": "<bearer-token>",
  "tokenType": "bearer",
  "serialNumber": "nt-2025-c123y",
  "ebusBrokerUsername": "nt-2025-c123y",
  "ebusBrokerPassword": "<mqtt-password>",
  "ebusBrokerHost": "span-nt-2025-c123y.local",
  "ebusBrokerMqttsPort": 8883,
  "ebusBrokerWsPort": 9001,
  "ebusBrokerWssPort": 9002
}
```

This provides a single bootstrap mechanism granting access to both REST and MQTT interfaces. The MQTT credentials are essential for browser-based JavaScript applications that may not have mDNS access.

### Recommended REST Endpoints

| Category | Methods | Description |
|----------|---------|-------------|
| **Authentication** | `POST` | Registration and credential provisioning |
| **Device information** | `GET` | Serial number, firmware version, hardware version, uptime, network addresses |
| **Network configuration** | `GET`, `PUT` | Wi-Fi SSID/password, static IP / DHCP, interface priority |
| **MQTT broker configuration** | `GET`, `PUT` | Broker URL, broker mode, credentials |
| **Device identity** | `GET`, `PUT` | Device name, location, user-assigned labels |
| **TLS certificate management** | `GET`, `POST` | Download CA certificate; upload broker CA certificate |
| **Firmware update** | `GET`, `POST` | OTA update server URL; initiate update |

Configuration `GET` endpoints SHOULD NOT require authentication (or MAY return limited non-sensitive info to unauthenticated clients). Configuration `PUT`/`POST` endpoints that modify state SHOULD require authentication.

### Broker Configuration

An eBus entity's configuration SHOULD include:

- **Broker URL** — e.g., `mqtts://broker.local:8883`
- **Broker mode** — One of:
  - `configured-only` — Use configured URL; no mDNS discovery.
  - `discovery-with-fallback` — mDNS first; configured URL if discovery fails.
  - `discovery-only` — mDNS only (default if no URL configured).

### HTTP GUI

An eBus entity MAY provide an HTTP-based GUI. If provided, the GUI SHOULD use the entity's REST API as its backend and SHOULD be served over HTTP and HTTPS.

---

## Detail: TLS and Security

### Transport Security

When TLS is supported:

- MQTT: port 8883 (MQTTS) or 9002 (WSS).
- HTTP: HTTPS on port 443 or as advertised via mDNS.
- TLS 1.2 or later MUST be used; TLS 1.3 is RECOMMENDED.

### Certificate Management

eBus entities on a local network typically use self-signed certificates because publicly-trusted CA certificates depend on infrastructure (publicly-resolvable DNS, periodic renewal) that LAN-local devices usually don't have. An entity using a self-signed (or otherwise non-publicly-verifiable) TLS certificate SHOULD:

- Generate the certificate with SANs for its mDNS hostname and all IP addresses.
- Regenerate the certificate when IP addresses change.
- Serve its CA certificate via an unauthenticated REST endpoint (e.g., `GET /api/v1/certificate/ca`) so that clients can establish trust.

An entity using a publicly-trusted certificate (e.g., a cloud-hosted gateway with a Let's Encrypt cert) need not provide a CA-download endpoint; standard CA-chain validation suffices.

### Broker CA Certificate Download

An entity hosting an MQTT broker with TLS SHOULD provide an authenticated REST endpoint for clients to download the broker's self-signed CA certificate. The path to this endpoint is discoverable via the `broker_ca` TXT record in the entity's `_ebus._tcp` mDNS advertisement.

**Example:** `GET /api/v1/certificate/broker-ca` (requires Bearer token from registration)

This allows a client that has registered with the broker host to obtain the CA certificate needed to establish trusted TLS connections to the broker.

### CA Certificate Upload

An entity SHOULD accept a broker CA certificate upload so it can validate the broker's TLS certificate:

```
POST /api/v1/certificate/ca
Content-Type: application/x-pem-file

<PEM-encoded CA certificate>
```

### MQTT Authentication

An entity connecting to a broker requiring authentication MUST use credentials from the broker host's registration endpoint or from its configuration. When a broker is configured for mTLS client-certificate authentication (see §"mTLS Client Authentication (Optional)" below), presenting a valid client certificate chained to one of the broker's configured trust anchors is an alternative — or addition — to credential-based authentication.

### mTLS Client Authentication (Optional)

An eBus deployment MAY use mutual TLS (mTLS) with client certificates as a client-authentication mechanism — independent of, or in addition to, the passphrase-based registration flow defined in §"Registration Endpoint" above. With mTLS, the entity (typically a device hosting an MQTT broker or REST endpoint) validates the inbound client's certificate against one or more configured trust-anchor CAs, and accepts the connection if validation succeeds.

**Trust-anchor configuration.** An entity supporting mTLS is configured with the CA certificate(s) it should trust for inbound client validation. These are managed via the authenticated trust-anchor REST endpoint required by requirement 29. Trust anchors are distinct from the entity's own CA cert (covered by requirement 27 and §"Certificate Management" above), which clients use to trust the entity; trust anchors are the CAs the entity uses to validate inbound clients.

**Identity assertion.** A successfully-authenticated client's identity is the subject of its certificate — typically the certificate's Subject DN, but a publisher MAY use a SAN or other configured attribute. The mapping from cert subject to authorization role is publisher-defined and out of scope for this specification.

**Role taxonomy.** When a publisher uses mTLS for both authentication and authorization, the following role values are conventional:

| Role | Description |
|------|-------------|
| `observer` | Read-only access to published data |
| `sensor` | May publish sensor/measurement data |
| `controller` | May publish and issue commands to settable properties |
| `automation` | May execute automation rules and coordinate devices |
| `admin` | Full access including configuration and certificate management |

**OEM-federated trust.** A deployment pattern emerging in the eBus ecosystem: two or more eBus-supporting OEMs arrange a trust relationship by direct or cross-signed CA certificates. Each participating device is configured with the partner OEM(s) trust anchor(s). When a client signed by a partner OEM connects to a device, its certificate validates against the configured trust anchor — no per-device passphrase registration is needed. This pattern is well-suited to direct device-to-device integration scenarios where the involved OEMs have an operational relationship and want to avoid placing the homeowner in the credential-provisioning path. PKI mechanics (key ceremony, chain construction, revocation handling) are standard CA-management practice and out of scope here.

---

## Detail: OTA Firmware Updates

An eBus entity SHOULD support a REST endpoint to initiate OTA firmware updates. The update server URL SHOULD come from configuration and MAY be updated via the REST API.

The OTA endpoint:

- SHOULD accept a POST request specifying the firmware URL, or initiate an update check against the configured server.
- SHOULD validate the firmware image (e.g., cryptographic signature) before applying.
- SHOULD report progress via REST API and/or MQTT property updates.
- MUST NOT permanently brick the device (dual-partition boot or rollback SHOULD be supported).

---

## Detail: Proxy Publishers

A **proxy publisher** is an eBus entity (device role) that publishes a Homie device representation on behalf of a non-eBus-native device. It communicates with the underlying device using whatever native protocol the device offers (Modbus, Matter, CTA-2045, vendor cloud API, etc.) and publishes the resulting Homie device on the eBus broker. The published representation is called a *proxy*.

A proxy is **functionally equivalent** to a native eBus publication of the same device: same property contracts, same `$state` lifecycle, same discovery. Consumers that need to distinguish proxy from native publication can do so via the proxy device's `root.$type` — this is the canonical mechanism, defined in [`data-models/proxy.md`](data-models/proxy.md). A publisher MAY also publish an explicit `proxied = true` boolean on the proxy's `info` capability when it wants the distinction to be unambiguous; the implicit `root.$type` mechanism is sufficient on its own.

This pattern is principle 6 of the design principles above ("Proxying is first-class"): an eBus consumer treats native and proxy publications equivalently; the data-model property contracts are written so that any conformant publisher — native or proxy — can satisfy them.

### Proxy Publisher Responsibilities

A proxy publisher MUST:

- Publish a Homie `$description` for the proxied device.
- Translate native-protocol data into Homie property values, populating the property contracts defined by the relevant data-model document for the proxied device class.
- Manage the proxy's Homie `$state` to reflect the underlying device's availability.

A proxy publisher SHOULD:

- Translate `/set` commands into the native protocol's command format where the underlying device supports control.
- Republish data promptly to minimize observable latency.
- Stop publishing a given proxied device once an eBus-native publisher for that device is detected (so the eBus tree converges on a single representation per physical device). Coexistence during the detection window is expected; see [`data-models/proxy.md`](data-models/proxy.md) for consumer-side dedup.

### Common Bridge Protocols

Proxy publishers commonly bridge from these underlying protocols:

| Protocol | Description | Examples |
|-------------|-----------------|----------|
| REST/JSON | HTTP polling | Tesla Powerwall, Enphase Envoy |
| Modbus TCP | Modbus TCP | SolarEdge inverter, Fronius inverter |
| Modbus RTU | RS-485 serial | Industrial meters, older inverters |
| Matter | Matter protocol | Thermostats, smart plugs |
| CTA-2045 | CTA-2045 / EcoPort | Water heaters, demand-response appliances |
| Cloud API | Vendor cloud API | Sense Energy Monitor, Emporia Vue |

A proxy publisher that bridges from a vendor cloud API SHOULD cache data locally and continue to serve last-known state when cloud connectivity is unavailable.

### Standalone Proxy Hosts (Bridges)

A proxy publisher is most often embedded in another eBus device (a distribution enclosure proxies a BESS; a smart panel proxies an EVSE). The framework also accommodates a **standalone proxy host** — an entity whose only purpose is to bridge one or more non-eBus-native devices into eBus. A standalone proxy host implements the device role exclusively in its proxy-publisher capacity; it does not represent any HEI device of its own. Common examples: a Raspberry Pi or Linux service that polls a Tesla cloud API and publishes the resulting Powerwall as a proxy; a vendor-provided Modbus-to-eBus appliance; a developer's Python service bridging a CTA-2045 water heater.

A standalone proxy host publishes itself as a Homie device of type **`energy.ebus.device.bridge`** — the eBus device type reserved for hosts whose role is solely to bridge non-eBus-native devices into the eBus tree. The bridge device is the root of the Homie tree; the proxied devices it publishes are its children, named per the `{proxier-id}-{proxied-id}` convention in [`data-models/proxy.md`](data-models/proxy.md).

The bridge device's `info` capability carries the bridge's own identity (vendor of the bridge, model, firmware version of the bridge software). The bridge does not publish HEI-device capabilities of its own — no `meter`, no `grid`, no `pcs`. Its sole function is to anchor the proxied children in the Homie tree and provide an mDNS-discoverable host for them.

This pattern keeps proxy disambiguation working via the primary `root.$type` mechanism: a consumer that finds two BESS devices with the same `info/serial-number` distinguishes them by inspecting each root — one BESS's root has `$type = energy.ebus.device.bess` (the BESS publishing itself natively), the other has `$type = energy.ebus.device.bridge` (the BESS being proxied by a bridge). Without the bridge device type, a standalone proxy host would have to rely on the explicit `proxied = true` boolean (a secondary mechanism) — the bridge device type lets the primary mechanism work uniformly across both embedded-proxy and standalone-proxy scenarios.

The semantic shape parallels Matter's *Bridge* device type (a Matter node that aggregates non-Matter devices into a Matter fabric). A developer building an eBus bridge can think of `energy.ebus.device.bridge` as the eBus analogue.

---

## Referenced Standards

| Standard | Version | Reference |
|----------|---------|-----------|
| MQTT | 3.1.1 / 5.0 | [OASIS MQTT](https://mqtt.org/mqtt-specification/) |
| Homie Convention | 5.0 | [Homie Convention v5.0](https://homieiot.github.io/specification/) |
| mDNS | RFC 6762 | [Multicast DNS](https://www.rfc-editor.org/rfc/rfc6762) |
| DNS-SD | RFC 6763 | [DNS-Based Service Discovery](https://www.rfc-editor.org/rfc/rfc6763) |
| TLS | 1.2 / 1.3 | [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446) |
| HTTP | 1.1 / 2 | [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) |
| OpenAPI | 3.x | [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) |
| JSON | RFC 8259 | [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) |
| RFC 2119 | — | [Key words for use in RFCs](https://www.rfc-editor.org/rfc/rfc2119) |
| Matter | — | [Connectivity Standards Alliance](https://csa-iot.org/all-solutions/matter/) |
| CTA-2045 | — | [ANSI/CTA Standard](https://shop.cta.tech/products/cta-2045) |
| OpenADR | 3.0 | [Open Automated Demand Response](https://www.openadr.org/openadr-3-0) |
| IEEE 2030.5 | — | [Smart Energy Profile](https://standards.ieee.org/ieee/2030.5/11216/) |

---

## Adjacent Standards (non-normative)

The standards listed below are *not* referenced normatively by eBus — an implementation is conformant without touching any of them — but they describe systems that meet eBus at the edges of its scope. Integrators building bridges, gateways, or translation layers between an eBus premises and the wider grid will encounter these models, and the eBus design has been informed by where its boundary falls relative to each one.

### Grid-side: IEC Common Information Model (CIM)

The IEC Common Information Model (IEC 61970 for transmission/EMS, IEC 61968 for distribution/DMS/OMS/CIS, IEC 62325 for markets) is the canonical data model on the *utility* side of the service drop. CIM describes the grid — substations, feeders, transformers, switches, capacitor banks, protection relays — and the operational IT systems that manage it. Its customer-facing leaf, `EnergyConsumer`, represents an entire service point as a single aggregate load characterized by active/reactive power and (optionally) a customer count; CIM does not categorize what is *behind* that point into branch circuits or end-use loads.

Electrification Bus is the mirror image: it models the *premises* side of the service drop — the panel, the branch circuits, the appliances and DERs connected to them — at per-circuit and per-device resolution. The two models are complementary, and the natural seam is the service entrance / revenue meter. An integrator publishing aggregated premises data into a utility DERMS, OMS, or DR platform will typically translate from eBus models on one side of that seam to CIM (often CIM's DER profile, IEC 61968-5) on the other.

Practical entry points to the CIM model:

- **Zepben Evolve CIM100 documentation** — [https://zepben.github.io/evolve/docs/cim/cim100/](https://zepben.github.io/evolve/docs/cim/cim100/) — browsable class reference for the CIM 100 distribution profile, maintained alongside the open-source [Zepben Evolve](https://github.com/zepben/evolve-sdk-jvm) implementation. More readable than the IEC source documents for getting oriented.
- **CIM Users Group** — [https://cimug.ucaiug.org/](https://cimug.ucaiug.org/) — community, working groups, profile registry.

[homie5]: https://homieiot.github.io/specification/
[rfc8259]: https://www.rfc-editor.org/rfc/rfc8259
[rfc2119]: https://www.rfc-editor.org/rfc/rfc2119
[openapi]: https://spec.openapis.org/oas/latest.html
