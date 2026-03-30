# Electrification Bus (eBus) Specification

**Version:** 0.1.0 (Draft)
**Date:** 2026-02-20
**Status:** Working Draft

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Terminology and Definitions](#2-terminology-and-definitions)
3. [Conformance Language](#3-conformance-language)
4. [Architecture Overview](#4-architecture-overview)
5. [Networking](#5-networking)
6. [mDNS Discovery and Advertisement](#6-mdns-discovery-and-advertisement)
7. [MQTT Messaging](#7-mqtt-messaging)
8. [eBus Conventions for Homie](#8-ebus-conventions-for-homie)
9. [REST API and Configuration](#9-rest-api-and-configuration)
10. [Security](#10-security)
11. [OTA Firmware Updates](#11-ota-firmware-updates)
12. [Adapters](#12-adapters)
13. [References](#13-references)

---

## 1. Introduction

### 1.1 Purpose

The Electrification Bus (eBus) is an open interoperability framework that enables Home Energy Infrastructure (HEI) devices to discover, communicate, and coordinate using open, standard protocols on a local network.

This specification defines how eBus entities use existing protocols — MQTT, the Homie Convention, mDNS, HTTP/REST, and TLS — in combination to achieve automatic discovery, self-describing publish/subscribe messaging, and local-first coordination among HEI devices.

### 1.2 Scope

eBus targets the devices that provide and support a home's electrical infrastructure:

- Smart electric panels
- Energy storage systems (BESS)
- Solar PV inverters
- Home Energy Management Systems (HEMS)
- Energy meters
- Generators
- Microgrid Interconnect Devices (MIDs) and transfer switches
- EV chargers (including V2H/V2G)

eBus is *not* a general-purpose IoT framework. General smart home devices (lighting, locks, appliances) are out of scope — those are served by standards like Matter. However, eBus defines an adapter pattern that enables bridging between eBus and other protocols (see [Section 12](#12-adapters)).

### 1.3 Design Principles

1. **Local-first** — All communication occurs on the local network. eBus devices MUST function without internet connectivity.
2. **Publish/subscribe first** — MQTT pub/sub is the primary communication pattern; REST is complementary.
3. **Self-documenting** — Devices describe their own capabilities via the Homie Convention; no external documentation is required for integration.
4. **Automatic discovery** — Devices find each other and the MQTT broker via mDNS, requiring zero manual configuration in the common case.
5. **Standard protocols** — eBus composes existing, proven standards rather than inventing new ones.
6. **Adapter-friendly** — Non-eBus devices can be integrated through adapters that publish to the eBus broker on their behalf.

### 1.4 Referenced Standards

This specification relies on and references the following standards. Where possible, eBus adopts these standards as-is and this specification describes only the eBus-specific usage and constraints.

| Standard | Version | Reference |
|----------|---------|-----------|
| MQTT | 3.1.1 / 5.0 | [OASIS MQTT][mqtt] |
| Homie Convention | 5.0 | [Homie Convention v5.0][homie5] |
| mDNS | RFC 6762 | [Multicast DNS][rfc6762] |
| DNS-SD | RFC 6763 | [DNS-Based Service Discovery][rfc6763] |
| TLS | 1.2 / 1.3 | [RFC 8446][rfc8446] |
| HTTP | 1.1 / 2 | [RFC 9110][rfc9110] |
| OpenAPI | 3.x | [OpenAPI Specification][openapi] |
| JSON | RFC 8259 | [The JSON Data Interchange Format][rfc8259] |

---

## 2. Terminology and Definitions

**eBus entity** — A network host that implements the device role, the controller role, or both (see [Section 2.1](#21-entity-roles)).

**HEI device** — A physical Home Energy Infrastructure device (e.g., a smart panel, battery, inverter).

**MQTT broker** — An MQTT server that routes messages between eBus entities.

**Homie device** — A logical representation of a physical device, published to the MQTT broker following the Homie Convention. A single eBus entity may publish one or more Homie devices.

**Node** — A functional grouping of properties within a Homie device (e.g., a circuit within a smart panel).

**Property** — An individual data point within a node (e.g., voltage, power, relay state).

**Adapter** — An eBus entity that bridges a non-eBus device into the eBus ecosystem by translating its native protocol to eBus/Homie messages.

### 2.1 Entity Roles

An eBus entity implements one or both of the following roles:

**Device role** — The entity publishes one or more Homie devices to the MQTT broker, representing the state and capabilities of physical HEI devices. A device-role entity publishes property values and accepts `/set` commands from controllers.

**Controller role** — The entity discovers and subscribes to Homie devices on the broker, reads their state, and may issue `/set` commands to control settable properties. Examples include HEMS, home automation systems, and monitoring dashboards.

An entity MAY implement both roles simultaneously. For example, a smart panel may publish its own device data (device role) while also subscribing to battery state to coordinate load management (controller role).

---

## 3. Conformance Language

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this specification are to be interpreted as described in [RFC 2119][rfc2119].

---

## 4. Architecture Overview

The eBus architecture consists of four layers:

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

### 4.1 Lifecycle

Once an eBus entity has obtained an IP address and claimed its mDNS hostname, it discovers (or provides) an MQTT broker via mDNS and connects. From that point, the entity follows the [Homie device lifecycle][homie5] for publishing state and coordinating with other entities.

---

## 5. Networking

### 5.1 Network Interfaces

An eBus entity MUST support at least one IP network interface. Common interface types include:

- **Ethernet** — Preferred for reliability and bandwidth.
- **Wi-Fi** — Provides flexibility for devices without wired connectivity.
- **Thread** — MAY be supported for low-power mesh networking scenarios.

An eBus entity with both an active Ethernet interface and a Wi-Fi interface SHOULD disable Wi-Fi when Ethernet is connected, unless its configuration specifies otherwise.

### 5.2 Network Configuration

An eBus entity SHOULD support network configuration through its configuration mechanism (see [Section 9](#9-rest-api-and-configuration)). Configurable parameters include but are not limited to:

- Wi-Fi SSID and credentials
- Static IP address or DHCP preference
- Interface priority (Ethernet vs. Wi-Fi)

### 5.3 Fallback AP Mode

An eBus entity with only an unconfigured Wi-Fi interface MAY provide a hosted access point (AP) for initial Wi-Fi configuration (SSID and password provisioning). The AP SHOULD be disabled once the entity successfully connects to a configured network.

---

## 6. mDNS Discovery and Advertisement

All eBus entities use mDNS (RFC 6762) and DNS-SD (RFC 6763) for hostname resolution, service advertisement, and service discovery. This section specifies the required mDNS behavior.

### 6.1 Hostname

Every eBus entity MUST claim a unique `.local` mDNS hostname.

The hostname SHOULD incorporate a device-unique identifier, such as a MAC address or serial number, to help ensure uniqueness. The non-unique portion of the hostname SHOULD be derived from the entity's configuration (e.g., a device type or user-assigned name).

**Example:** `span-nt-2025-c123y.local`

### 6.2 All eBus Entities

Every eBus entity, regardless of role, MUST publish the following mDNS service advertisements:

#### 6.2.1 eBus Metadata Service (`_ebus._tcp`)

Every eBus entity MUST advertise a `_ebus._tcp` service. This advertisement enables eBus-aware entities and applications to discover all eBus participants on the network.

**Required TXT records:**

| Key | Description | Example |
|-----|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `ebus_version` | eBus specification version supported | `0.1` |
| `roles` | Comma-separated list of roles: `device`, `controller` | `device` |
| `device_id` | Unique device identifier | `nt-2025-c123y` |

**Recommended TXT records:**

| Key | Description | Example |
|-----|-------------|---------|
| `device_type` | Manufacturer device type identifier | `span-panel` |
| `name` | Human-readable device name | `Main Panel` |
| `manufacturer` | Device manufacturer | `SPAN` |
| `model` | Device model identifier | `MAIN-32` |
| `fw_version` | Firmware version | `24.5.1` |

#### 6.2.2 Device Info Metadata Service (`_device-info._tcp`)

Every eBus entity MUST advertise a `_device-info._tcp` service. The `_device-info._tcp` name is [reserved by IANA](https://www.iana.org/assignments/service-names-port-numbers/service-names-port-numbers.xhtml?search=device-info) for DNS-SD device info but has no formal specification for TXT record keys. eBus defines the following TXT records for this service:

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

### 6.3 Device-Role Entities

A device-role entity that offers an HTTP REST API or GUI MUST advertise it via mDNS.

#### 6.3.1 HTTP API (`_http._tcp` and/or `_https._tcp`)

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `path` | API base path | `/api/v1` |
| `version` | API version | `1.0` |
| `device_id` | Device identifier | `nt-2025-c123y` |
| `device_type` | Device type | `span-panel` |
| `openapi` | Path to OpenAPI spec | `/api/v1/docs` |

The `openapi` TXT record is RECOMMENDED; it enables automatic API discovery by controllers and tools.

A device-role entity that does not self-host an MQTT broker MUST attempt to discover a broker via mDNS (see [Section 6.5](#65-broker-discovery)).

### 6.4 Controller-Role Entities

A controller-role entity that offers an HTTP REST API or GUI SHOULD advertise it via mDNS using the same `_http._tcp` / `_https._tcp` service types described in [Section 6.3.1](#631-http-api-_http_tcp-andor-_https_tcp).

A controller-role entity that does not self-host an MQTT broker MUST attempt to discover a broker via mDNS (see [Section 6.5](#65-broker-discovery)).

### 6.5 MQTT Broker Advertisements

An eBus entity that hosts an MQTT broker MUST advertise it via mDNS so that other entities can discover it. A broker SHOULD advertise one or more of the following service types, depending on the transports it supports:

#### 6.5.1 Secure MQTT (`_secure-mqtt._tcp`)

Advertised when the broker offers MQTT over TLS (port 8883).

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `protocol` | MQTT protocol version | `mqtt-v5` or `mqtt-v3.1.1` |
| `broker` | Broker hostname | `span-nt-2025-c123y.local` |
| `device_id` | Broker host device ID | `nt-2025-c123y` |

#### 6.5.2 MQTT over WebSocket (`_mqtt-ws._tcp`)

Advertised when the broker offers MQTT over WebSocket (typically port 9001).

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `protocol` | MQTT protocol version | `mqtt-v5` or `mqtt-v3.1.1` |
| `path` | WebSocket endpoint path | `/mqtt` |
| `subprotocol` | WebSocket subprotocol | `mqtt` |

#### 6.5.3 MQTT over Secure WebSocket (`_mqtt-wss._tcp`)

Advertised when the broker offers MQTT over WebSocket with TLS (typically port 9002).

TXT records are the same as `_mqtt-ws._tcp`.

#### 6.5.4 Plain MQTT (`_mqtt._tcp`)

Advertised when the broker offers unencrypted MQTT (port 1883). This SHOULD only be used when TLS is not feasible.

| TXT Key | Description | Example |
|---------|-------------|---------|
| `txtvers` | TXT record version | `1` |
| `protocol` | MQTT protocol version | `mqtt-v5` or `mqtt-v3.1.1` |

### 6.6 Broker Discovery

An eBus entity that does not self-host an MQTT broker MUST attempt to discover an eBus-supporting broker via mDNS, by browsing for one or more of the following service types:

1. `_secure-mqtt._tcp` (preferred)
2. `_mqtt-wss._tcp`
3. `_mqtt-ws._tcp`
4. `_mqtt._tcp` (fallback)

The entity SHOULD prefer TLS-secured transports over unencrypted transports.

If multiple brokers are discovered, the entity SHOULD connect to the first broker that responds and successfully authenticates. The entity MAY use configuration to specify a preferred broker or to restrict discovery to brokers matching certain criteria.

If no broker is discovered and no broker URL is configured, the entity SHOULD retry discovery periodically. The entity MAY use exponential backoff for retry intervals.

### 6.7 Broker Configuration Override

An eBus entity's configuration (see [Section 9](#9-rest-api-and-configuration)) SHOULD include the following MQTT broker settings:

- **Broker URL** — An MQTT broker URL (e.g., `mqtts://broker.local:8883`).
- **Broker mode** — One of:
  - `configured-only` — Use the configured URL unconditionally; do not perform mDNS discovery.
  - `discovery-with-fallback` — Attempt mDNS discovery first; use the configured URL only if discovery fails.
  - `discovery-only` — Use only mDNS discovery; ignore the configured URL. This is the default if no broker URL is configured.

---

## 7. MQTT Messaging

eBus uses MQTT as its primary messaging protocol. All eBus MQTT communication follows the [Homie Convention v5.0][homie5], which defines the topic hierarchy, message semantics, and device lifecycle. The Homie Convention specification is normative for MQTT topic structure and message format; this section specifies only the eBus-specific choices.

### 7.1 MQTT Version

eBus entities SHOULD use MQTT version 5.0. Entities MAY use MQTT 3.1.1 where MQTT 5.0 support is not available.

### 7.2 Topic Domain

eBus uses `ebus` as the Homie topic domain (replacing the default `homie` prefix). The root topic structure is:

```
ebus/5/{device-id}/...
```

Where:
- `ebus` — The eBus domain prefix.
- `5` — The Homie Convention major version.
- `{device-id}` — A unique identifier for the Homie device, conforming to the Homie Convention topic ID rules. The device ID SHOULD be derived from a hardware identifier (e.g., serial number) to ensure uniqueness.

### 7.3 Quality of Service

eBus entities SHOULD use QoS 2 (Exactly Once) for property value publications and subscriptions. Entities SHOULD use QoS 0 for `/set` command messages (controller to device).

### 7.4 Homie Convention Compliance

eBus entities implementing the device role MUST comply with the [Homie Convention v5.0][homie5] for device description, device lifecycle, property publication, datatypes, formats, and retained message semantics. The Homie Convention specification is the normative reference for all of these mechanisms.

---

## 8. eBus Conventions for Homie

eBus adopts the [Homie Convention v5.0][homie5] as its data model and topic structure. This section specifies only the eBus-specific conventions that extend or constrain the Homie Convention. The [Homie Convention specification][homie5] is normative for all other aspects.

### 8.1 Device and Node Types

The Homie Convention `type` attribute on devices and nodes uses a hierarchical, reverse-domain-style naming convention. The `energy.ebus.device` prefix is reserved for eBus-standard types.

**Example type hierarchy:**

```
energy.ebus.device.distribution-enclosure
energy.ebus.device.distribution-enclosure.lugs.upstream
energy.ebus.device.distribution-enclosure.lugs.downstream
energy.ebus.device.distribution-enclosure.circuit
energy.ebus.device.distribution-enclosure.core
energy.ebus.device.distribution-enclosure.pcs
energy.ebus.device.distribution-enclosure.evse
energy.ebus.device.distribution-enclosure.bess
energy.ebus.device.distribution-enclosure.pv
energy.ebus.device.bess
energy.ebus.device.inverter
energy.ebus.device.meter
energy.ebus.device.evse
energy.ebus.device.generator
energy.ebus.device.mid
energy.ebus.device.hems
```

Device type definitions — including the required and optional nodes and properties for each type — will be specified in a companion document: **eBus Device Type Registry**.

Manufacturers MAY define custom types using their own namespace prefix (e.g., `com.acme.device.widget`).

### 8.2 Units

Properties that represent physical measurements MUST include a `unit` attribute. eBus uses the units defined by the [Homie Convention specification][homie5].

### 8.3 Controller Discovery of Devices

A controller-role entity discovers Homie devices on the eBus broker by subscribing to:

```
ebus/5/+/$state
```

Upon receiving a `$state` message for an unknown device, the controller retrieves the device's `$description` and subscribes to property topics as needed. See the [Homie Convention specification][homie5] for details on device description and lifecycle semantics.

---

## 9. REST API and Configuration

### 9.1 REST vs. MQTT: Complementary Roles

MQTT (via the Homie Convention) is the primary protocol for real-time state publication and device control. REST is complementary, serving administrative and configuration operations that are better suited to a request/response pattern.

REST is appropriate for operations that:

- Are performed infrequently (initial setup, occasional reconfiguration).
- Require request/response semantics (authentication, file uploads/downloads).
- Must work before an MQTT connection is established (bootstrap, credential provisioning).
- Involve large payloads (certificate files, firmware images, OpenAPI specifications).
- Benefit from browser accessibility (configuration GUIs, API documentation).

MQTT is appropriate for operations that:

- Involve continuous or frequent state updates (sensor readings, power measurements).
- Require fan-out to multiple subscribers (one publish, many consumers).
- Benefit from retained messages (new subscribers receive current state immediately).
- Require device lifecycle tracking (LWT for disconnect detection).

### 9.2 Configuration Model

An eBus entity uses a layered configuration model:

1. **Baked-in defaults** — Configuration compiled into the entity's firmware. These provide sensible defaults for standalone operation.
2. **Dynamic configuration** — Configuration applied at runtime via the REST API. Dynamic configuration SHOULD override baked-in defaults.

A future option: an entity's baked-in configuration MAY include a configuration server URL. The entity would query this URL (with a unique identifier as a query parameter) and apply the JSON response as dynamic configuration. The configuration server MAY also be discovered via mDNS.

### 9.3 HTTP Server

An eBus entity SHOULD provide an HTTP server for REST API and (optionally) GUI access.

The HTTP server:

- SHOULD be offered on both HTTP (port 80) and HTTPS/TLS (port 443), when TLS is supported.
- SHOULD be advertised via mDNS as `_http._tcp` and/or `_https._tcp` (see [Section 6.4](#64-http-service-advertisements)).
- MUST use JSON ([RFC 8259][rfc8259]) for REST API request and response bodies.

Offering both HTTP and HTTPS is a deliberate tradeoff: HTTPS provides transport security, but HTTP ensures accessibility in situations where TLS certificate configuration is an obstacle (e.g., during a power outage when a homeowner needs immediate access via a browser).

### 9.4 REST API

An eBus entity SHOULD provide an HTTP REST API for configuration and administration.

#### 9.4.1 API Documentation (OpenAPI)

The REST API SHOULD be documented using an [OpenAPI][openapi] specification. The entity SHOULD serve this specification via HTTP so that controllers and tools can discover available endpoints programmatically.

**Example:** `GET /api/v1/docs`

The mDNS `_http._tcp` / `_https._tcp` advertisement SHOULD include an `openapi` TXT record containing the path to the OpenAPI specification (see [Section 6.4](#64-http-service-advertisements)).

#### 9.4.2 Authentication and Registration

An eBus entity that requires authentication for its REST API and/or MQTT broker SHOULD provide a registration endpoint. This endpoint exchanges a device-specific passphrase (e.g., printed on the device label or displayed on an on-device screen) for:

- An access token for subsequent REST API requests.
- MQTT broker connection details (host, ports, username, password).

This pattern is important because it provides a single bootstrap mechanism that grants access to both REST and MQTT interfaces. The MQTT broker credentials included in the response are a convenience — they can also be obtained via mDNS — but are essential for browser-based JavaScript applications that may not have access to mDNS.

**Example:**

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

Authenticated REST API requests SHOULD use the access token as a Bearer token in the HTTP `Authorization` header.

#### 9.4.3 Configuration Endpoints

The following REST API endpoint categories are RECOMMENDED for eBus entities:

| Category | Methods | Description |
|----------|---------|-------------|
| **Authentication** | `POST` | Registration and credential provisioning (see above) |
| **Device information** | `GET` | Serial number, firmware version, hardware version, uptime, network addresses |
| **Network configuration** | `GET`, `PUT` | Wi-Fi SSID/password, static IP / DHCP, interface priority and selection |
| **MQTT broker configuration** | `GET`, `PUT` | Broker URL, broker mode, credentials (see [Section 6.7](#67-broker-configuration-override)) |
| **Device identity** | `GET`, `PUT` | Device name, location, user-assigned labels |
| **TLS certificate management** | `GET`, `POST` | Download entity's CA certificate; upload broker CA certificate (see [Section 10](#10-security)) |
| **Firmware update** | `GET`, `POST` | OTA update server URL configuration; initiate update (see [Section 11](#11-ota-firmware-updates)) |

Configuration `GET` endpoints SHOULD NOT require authentication, or MAY return a limited subset of non-sensitive information to unauthenticated clients.

Configuration `PUT`/`POST` endpoints that modify state SHOULD require authentication.

#### 9.4.4 Certificate Download Endpoint

An eBus entity that supports TLS SHOULD serve its self-signed CA certificate via an unauthenticated REST endpoint. This allows clients to download and trust the certificate for subsequent TLS connections to both the entity's REST API and MQTT broker.

**Example:** `GET /api/v1/certificate/ca`

This endpoint SHOULD NOT require authentication, since clients need the CA certificate before they can establish trusted TLS connections.

### 9.5 HTTP GUI

An eBus entity MAY provide an HTTP-based graphical user interface (GUI) for configuration and management.

If provided, the GUI:

- SHOULD use the entity's REST API to implement all configuration operations (i.e., the GUI is a client of the REST API, not a separate interface to the device).
- SHOULD be served by the entity over HTTP and HTTPS.
- SHOULD be advertised via mDNS.

---

## 10. Security

### 10.1 Transport Security

An eBus entity SHOULD use TLS for MQTT and HTTP connections. An entity MAY fall back to non-TLS native protocols if TLS is not implemented or is not feasible for the platform.

When TLS is supported:

- MQTT connections SHOULD use port 8883 (MQTTS) or 9002 (WSS).
- HTTP connections SHOULD use HTTPS (port 443 or as advertised via mDNS).
- TLS 1.2 or later MUST be used. TLS 1.3 is RECOMMENDED.

### 10.2 Certificate Management

An eBus entity hosting a broker or REST API with TLS will typically use self-signed certificates, since these devices operate on a local network without access to public certificate authorities.

The entity SHOULD:

- Generate a self-signed certificate containing Subject Alternative Names (SANs) for the entity's mDNS hostname and all of its IP addresses.
- Regenerate the certificate when IP addresses change.
- Serve the CA certificate via an unauthenticated REST endpoint (e.g., `GET /api/v1/certificate/ca`) to allow clients to download and trust it.

### 10.3 CA Certificate Upload

An eBus entity supporting TLS SHOULD provide a REST endpoint for uploading a CA certificate for the eBus MQTT broker. This allows the entity to validate the broker's TLS certificate when connecting to a broker hosted by another entity.

**Example:**

```
POST /api/v1/certificate/ca
Content-Type: application/x-pem-file

<PEM-encoded CA certificate>
```

### 10.4 MQTT Authentication

An eBus entity connecting to a broker that requires authentication MUST authenticate using the credentials obtained via the broker host's registration endpoint (see [Section 9.4.2](#942-authentication-and-registration)) or from its configuration.

### 10.5 Client Certificate Roles

An eBus deployment MAY use mutual TLS (mTLS) with client certificates for fine-grained access control. The following predefined client roles are defined:

| Role | Description |
|------|-------------|
| `observer` | Read-only access to published data |
| `sensor` | May publish sensor/measurement data |
| `controller` | May publish and issue commands to settable properties |
| `automation` | May execute automation rules and coordinate devices |
| `admin` | Full access including configuration and certificate management |

Client certificate role enforcement is OPTIONAL and depends on the broker and deployment configuration.

---

## 11. OTA Firmware Updates

### 11.1 Update Endpoint

An eBus entity SHOULD support a REST endpoint that initiates an over-the-air (OTA) firmware update.

The OTA firmware update server URL SHOULD be obtained from the entity's configuration. The URL MAY be updated via the REST API.

### 11.2 Update Process

The OTA endpoint:

- SHOULD accept a POST request specifying the firmware URL, or initiate an update check against the configured update server.
- SHOULD validate the firmware image (e.g., via cryptographic signature) before applying it.
- SHOULD report update progress and status via the REST API and/or MQTT property updates.
- MUST NOT render the device permanently inoperable if the update fails (i.e., the entity SHOULD support rollback or dual-partition boot).

---

## 12. Adapters

### 12.1 Adapter Concept

An adapter is an eBus entity (implementing the device role) that bridges a non-eBus device into the eBus ecosystem. The adapter communicates with the non-eBus device using its native protocol and publishes its state as a Homie device on the eBus broker.

From the perspective of other eBus entities, an adapter's Homie device is indistinguishable from a device with native eBus support.

### 12.2 Adapter Responsibilities

An adapter MUST:

- Publish a Homie device description for the bridged device.
- Translate native protocol data into Homie property values.
- Manage the Homie device lifecycle (`$state`) to accurately reflect the bridged device's availability.

An adapter SHOULD:

- Translate `/set` commands into the native protocol's command format, if the bridged device supports writable properties.
- Republish data promptly to minimize latency between the native device's state change and the eBus property update.

### 12.3 Common Adapter Types

| Adapter Type | Native Protocol | Examples |
|-------------|-----------------|----------|
| REST/JSON | HTTP polling | Tesla Powerwall, Enphase Envoy |
| Modbus TCP | Modbus TCP | SolarEdge inverter, Fronius inverter |
| Modbus RTU | RS-485 serial | Industrial meters, older inverters |
| Matter | Matter protocol | Thermostats, smart plugs |
| CTA-2045 | CTA-2045 / EcoPort | Water heaters, demand-response appliances |
| Cloud API | Vendor cloud API | Sense Energy Monitor, Emporia Vue |

Adapters for cloud APIs SHOULD cache data locally and continue to serve the last-known state when cloud connectivity is unavailable.

---

## 13. References

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

- **MQTT** — OASIS Standard. https://mqtt.org/mqtt-specification/
- **Homie Convention v5.0** — https://homieiot.github.io/specification/
- **RFC 6762** — Multicast DNS. https://www.rfc-editor.org/rfc/rfc6762
- **RFC 6763** — DNS-Based Service Discovery. https://www.rfc-editor.org/rfc/rfc6763
- **RFC 8446** — The Transport Layer Security (TLS) Protocol Version 1.3. https://www.rfc-editor.org/rfc/rfc8446
- **RFC 9110** — HTTP Semantics. https://www.rfc-editor.org/rfc/rfc9110
- **RFC 8259** — The JSON Data Interchange Format. https://www.rfc-editor.org/rfc/rfc8259
- **RFC 2119** — Key words for use in RFCs to Indicate Requirement Levels. https://www.rfc-editor.org/rfc/rfc2119
- **OpenAPI Specification** — https://spec.openapis.org/oas/latest.html
- **Matter** — Connectivity Standards Alliance. https://csa-iot.org/all-solutions/matter/
- **CTA-2045** — ANSI/CTA Standard. https://shop.cta.tech/products/cta-2045
- **OpenADR 3.0** — Open Automated Demand Response. https://www.openadr.org/openadr-3-0
- **IEEE 2030.5** — IEEE Standard for Smart Energy Profile Application Protocol. https://standards.ieee.org/ieee/2030.5/11216/

---

*This specification is a working draft. Device type definitions, detailed property schemas, and conformance test procedures will be addressed in companion documents.*
