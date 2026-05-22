# Electrification Bus (eBus) Specification

**Version:** 0.2.0 (Draft)
**Date:** 2026-03-29
**Status:** Working Draft

---

## What is eBus?

eBus is an open interoperability framework for Home Energy Infrastructure (HEI) devices — smart panels, batteries, inverters, HEMS, meters, generators, and transfer switches.

eBus composes existing, well-known protocols — **mDNS**, **MQTT** (with the **Homie Convention**), and **HTTP/REST** — in a structured way that enables automatic discovery, self-describing messaging, and local-first coordination. Most developers already know these protocols; eBus defines how to use them together so that devices from different manufacturers can interoperate without custom integration work.

### Terminology

- **eBus entity** — A network host implementing the device role, the controller role, or both.
- **Device role** — Publishes Homie devices to the MQTT broker, representing HEI device state and capabilities.
- **Controller role** — Discovers and subscribes to Homie devices, reads state, and issues `/set` commands.
- **Adapter** — An eBus entity (device role) that bridges a non-eBus device by translating its native protocol to Homie/MQTT.

### Conformance Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" are to be interpreted as described in [RFC 2119][rfc2119].

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
14. eBus device and node types use the `energy.ebus.device.*` namespace; manufacturers MAY use their own prefix.

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

### TLS and Security

23. An eBus entity SHOULD use TLS for MQTT and HTTP connections; MAY fall back to non-TLS if not feasible.
24. When TLS is supported, TLS 1.2 or later MUST be used; TLS 1.3 is RECOMMENDED.
25. An eBus entity supporting TLS SHOULD provide a REST endpoint to download its CA certificate (unauthenticated).
26. An eBus entity supporting TLS SHOULD provide a REST endpoint to upload a CA certificate for the MQTT broker.

### OTA Firmware Updates

27. An eBus entity SHOULD support a REST endpoint to initiate OTA firmware updates.
28. The OTA update server URL SHOULD be obtained from configuration.
29. An OTA update MUST NOT permanently brick the device (rollback or dual-partition boot SHOULD be supported).

### Adapters

30. An adapter is an eBus entity (device role) that bridges a non-eBus device by translating its native protocol to Homie/MQTT.
31. An adapter's Homie device MUST be indistinguishable from a native eBus device to other eBus entities.
32. Adapters for cloud APIs SHOULD cache data locally and serve last-known state when connectivity is lost.

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
| `roles` | Comma-separated: `device`, `controller` | `device` |
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

If multiple brokers are discovered, the entity SHOULD connect to the first that responds and authenticates successfully. If no broker is found, the entity SHOULD retry periodically (MAY use exponential backoff).

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

The Homie `type` attribute uses a hierarchical, reverse-domain-style naming convention. The `energy.ebus.device` prefix is reserved for eBus-standard types.

**Example type hierarchy:**

```
energy.ebus.device.distribution-enclosure
energy.ebus.device.distribution-enclosure.circuit
energy.ebus.device.distribution-enclosure.core
energy.ebus.device.distribution-enclosure.pcs
energy.ebus.device.bess
energy.ebus.device.inverter
energy.ebus.device.meter
energy.ebus.device.evse
energy.ebus.device.generator
energy.ebus.device.mid
energy.ebus.device.hems
```

Device type definitions — required and optional nodes and properties for each type — will be specified in a companion document: **eBus Device Type Registry**.

Manufacturers MAY define custom types using their own namespace prefix (e.g., `com.acme.device.widget`).

### Units

Properties representing physical measurements MUST include a `unit` attribute, using units defined by the [Homie Convention specification][homie5].

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

eBus entities on a local network will typically use self-signed certificates. The entity SHOULD:

- Generate a self-signed certificate with SANs for its mDNS hostname and all IP addresses.
- Regenerate the certificate when IP addresses change.
- Serve the CA certificate via an unauthenticated REST endpoint (e.g., `GET /api/v1/certificate/ca`).

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

An entity connecting to a broker requiring authentication MUST use credentials from the broker host's registration endpoint or from its configuration.

### Client Certificate Roles (Optional)

An eBus deployment MAY use mTLS with client certificates for access control:

| Role | Description |
|------|-------------|
| `observer` | Read-only access to published data |
| `sensor` | May publish sensor/measurement data |
| `controller` | May publish and issue commands to settable properties |
| `automation` | May execute automation rules and coordinate devices |
| `admin` | Full access including configuration and certificate management |

---

## Detail: OTA Firmware Updates

An eBus entity SHOULD support a REST endpoint to initiate OTA firmware updates. The update server URL SHOULD come from configuration and MAY be updated via the REST API.

The OTA endpoint:

- SHOULD accept a POST request specifying the firmware URL, or initiate an update check against the configured server.
- SHOULD validate the firmware image (e.g., cryptographic signature) before applying.
- SHOULD report progress via REST API and/or MQTT property updates.
- MUST NOT permanently brick the device (dual-partition boot or rollback SHOULD be supported).

---

## Detail: Adapters

An adapter is an eBus entity (device role) that bridges a non-eBus device into the eBus ecosystem. It communicates with the non-eBus device using its native protocol and publishes its state as a Homie device on the eBus broker. From other eBus entities' perspective, an adapter's Homie device is indistinguishable from a native eBus device.

### Adapter Responsibilities

An adapter MUST:
- Publish a Homie device description for the bridged device.
- Translate native protocol data into Homie property values.
- Manage the Homie device lifecycle (`$state`) to reflect the bridged device's availability.

An adapter SHOULD:
- Translate `/set` commands into the native protocol's command format.
- Republish data promptly to minimize latency.

### Common Adapter Types

| Adapter Type | Native Protocol | Examples |
|-------------|-----------------|----------|
| REST/JSON | HTTP polling | Tesla Powerwall, Enphase Envoy |
| Modbus TCP | Modbus TCP | SolarEdge inverter, Fronius inverter |
| Modbus RTU | RS-485 serial | Industrial meters, older inverters |
| Matter | Matter protocol | Thermostats, smart plugs |
| CTA-2045 | CTA-2045 / EcoPort | Water heaters, demand-response appliances |
| Cloud API | Vendor cloud API | Sense Energy Monitor, Emporia Vue |

Adapters for cloud APIs SHOULD cache data locally and continue to serve last-known state when cloud connectivity is unavailable.

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

[mqtt]: https://mqtt.org/mqtt-specification/
[mqtt5]: https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html
[homie5]: https://homieiot.github.io/specification/
[rfc6762]: https://www.rfc-editor.org/rfc/rfc6762
[rfc6763]: https://www.rfc-editor.org/rfc/rfc6763
[rfc8446]: https://www.rfc-editor.org/rfc/rfc8446
[rfc9110]: https://www.rfc-editor.org/rfc/rfc9110
[rfc8259]: https://www.rfc-editor.org/rfc/rfc8259
[rfc2119]: https://www.rfc-editor.org/rfc/rfc2119
[openapi]: https://spec.openapis.org/oas/latest.html
