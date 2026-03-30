# Feasibility Analysis: Adapting Homie to Zenoh for Microcontroller-based HEI Devices

## The Problem

MQTT requires a broker. Running a broker on a microcontroller (RTOS, limited RAM/flash) is impractical. So today, every eBus deployment needs a Linux box just to host the MQTT broker — even if all the actual HEI devices are microcontrollers.

## What is Zenoh?

Zenoh (Zero Network OverHead) is an open-source protocol and middleware under the Eclipse Foundation that unifies three concerns into a single stack:

- **Data in motion** (pub/sub)
- **Data at rest** (geo-distributed storage)
- **Computations** (queryables / triggered computations)

The core implementation is in Rust, with a separate pure-C implementation called **zenoh-pico** for constrained devices. Zenoh reached its 1.0 stable release in October 2024 and is currently at version 1.7.x.

### Three Operating Modes

| Mode | Description | Broker Required? |
|---|---|---|
| **Peer** | Nodes discover each other via multicast; direct peer-to-peer communication | No |
| **Client** | Node connects to a Zenoh router (lower resource usage) | Router needed |
| **Router** (`zenohd`) | Routes data between clients and peer subnetworks | N/A (is the infrastructure) |

Unlike MQTT where the broker is mandatory, Zenoh routers are **optional infrastructure**. A fully functional Zenoh network can operate with zero routers in peer mode.

## Why Zenoh Changes the Equation

Zenoh's **peer mode** eliminates the broker entirely. Two microcontrollers running zenoh-pico can talk directly over TCP — no central process needed.

### zenoh-pico Resource Footprint

**Raspberry Pi Pico (ARM Cortex-M0+, 256 KB RAM, 2 MB flash):**
- Flash: ~80 KB (20% of Pico, 10% of Pico 2)
- RAM: ~12 KB (5% of Pico, 2% of Pico 2)

Tailored builds (e.g., publisher-only) can be as small as ~15 KB flash.

### Supported RTOS Platforms

| Platform | Status |
|----------|--------|
| Zephyr | Supported |
| FreeRTOS-Plus-TCP | Supported |
| ESP-IDF (ESP32) | Supported |
| MbedOS | Supported |
| Arduino (8-bit and 32-bit) | Supported |
| STM32 ThreadX | Supported |
| Raspberry Pi Pico / Pico 2 | Supported |

For comparison, a minimal MQTT *client* library on a microcontroller is similar in size — but you still need the broker elsewhere. With Zenoh, the peer *is* the infrastructure.

### Peer Mode Performance on Microcontrollers

- Up to 70% lower latency than client mode
- Over 4x throughput for small messages vs. client mode
- Sub-20 microsecond round-trip times for packets under 16 KiB

## Zenoh vs. MQTT

| Aspect | MQTT | Zenoh |
|--------|------|-------|
| Architecture | Always requires a broker | Broker optional; peer-to-peer supported |
| Wire overhead | ~2 bytes min (plus topic strings) | 5 bytes min; resource ID mapping reduces topics to 1 byte |
| QoS | 3 levels (0, 1, 2) | Reliability (best-effort / reliable), congestion control, 5 priority levels |
| Retained messages | Built-in retained flag | Via storages and queryables (more flexible but explicit) |
| Request-response | Not native (built on pub/sub) | Native `get`/`queryable` pattern |
| Wildcards | `+` (single level), `#` (multi-level) | `*` (single chunk), `**` (multi-chunk) |
| Discovery | N/A (connect to broker) | Automatic via multicast scouting |
| Constrained devices | Many lightweight clients available | zenoh-pico: ~12 KB RAM, ~80 KB flash |
| Ecosystem maturity | Very mature, decades of tooling | Younger (1.0 in Oct 2024), rapidly growing |
| MQTT interop | Native | Via zenoh-plugin-mqtt (router becomes MQTT v3/v5 broker) |

### Performance (Published Benchmarks)

| Metric | Zenoh (peer) | MQTT |
|--------|-------------|------|
| Throughput (8B payload) | ~4M msg/s | ~33-38K msg/s |
| Latency (single machine) | 10 us | 27 us |
| Latency (multi machine) | 16 us | 45 us |

## Mapping Homie Concepts to Zenoh

### Topic / Key Expression Mapping

The Homie MQTT topic structure maps naturally to Zenoh key expressions:

| Homie MQTT Topic | Zenoh Key Expression |
|---|---|
| `homie/5/{device-id}/$state` | `homie/5/{device-id}/$state` |
| `homie/5/{device-id}/$description` | `homie/5/{device-id}/$description` |
| `homie/5/{device-id}/{node}/{prop}` | `homie/5/{device-id}/{node}/{prop}` |
| `homie/5/{device-id}/{node}/{prop}/set` | `homie/5/{device-id}/{node}/{prop}/set` |
| Wildcard: `homie/5/+/$state` | `homie/5/*/$state` |
| Wildcard: `homie/5/#` | `homie/5/**` |

The key expression syntax is nearly identical — just `*` instead of `+` and `**` instead of `#`.

### Feature-by-Feature Feasibility

| Homie Feature | MQTT Mechanism | Zenoh Equivalent | Feasibility |
|---|---|---|---|
| **Device discovery** | Subscribe to `+/5/+/$state` with retained messages | Subscribe to `*/5/*/$state` + `get()` to query storage or queryable | Achievable; requires explicit storage setup |
| **Retained messages** | Built-in `retained` flag | **Storage** (on router) or **queryable** (on device) | Feasible but more complex — see below |
| **Last Will (LWT)** | Broker publishes `$state → lost` on disconnect | **Liveliness tokens** — peers declare tokens, others subscribe to changes | Feasible; available in zenoh-pico |
| **QoS 2 (exactly once)** | Built-in | Zenoh `reliable` mode (hop-to-hop or end-to-end) | Comparable |
| **Settable properties** (`/set`) | Non-retained publish to `/set` topic | Zenoh `put()` to the `/set` key expression | Direct mapping |
| **`$target` transitions** | Retained publish | Storage-backed or queryable-backed | Feasible |
| **Broadcasts** | `homie/5/$broadcast/{subtopic}` | Same key expression | Direct mapping |
| **UTF-8 string payloads** | Native | Native (Zenoh payloads are arbitrary bytes; UTF-8 by convention) | Direct mapping |

## The Two Hard Problems

### 1. Retained Messages

This is the biggest gap. Homie relies heavily on MQTT retained messages for device state, descriptions, and property values. When a new controller comes online, it immediately gets the last-known state of every device from the broker's retained message store.

In Zenoh, the options are:

- A **memory storage** running on a Zenoh router (requires a Linux box — but at least it's optional infrastructure, not a mandatory broker)
- A **queryable** on each device that responds to `get()` requests with its current state (this *does* work on microcontrollers and is the more interesting option)
- Combining both: devices are queryable for their own state, and an optional router with storage provides persistence across device reboots

The queryable approach is actually **better** than MQTT retained messages in some ways — the device always returns its *current* state, not a stale retained message from a previous session.

### 2. Last Will and Testament (LWT)

MQTT's LWT is a broker feature: the broker publishes a pre-configured message when a client disconnects ungracefully. Zenoh has no direct equivalent because there may be no central process watching connections.

Options:

- **Liveliness tokens** — Zenoh has a liveliness subsystem where peers can declare tokens and others can subscribe to liveliness changes. This maps well to Homie's `$state` lifecycle. When a peer's liveliness token disappears, subscribers get notified. Available in zenoh-pico.
- **Application-level heartbeats** — devices periodically publish; absence triggers "lost" state
- **Router-assisted** — if a router is present, it can detect client disconnects

## Proposed Architecture: Homie-over-Zenoh

```
┌─────────────────────────────────────────────────┐
│  Peer Mode (no broker needed)                   │
│                                                 │
│  ┌──────────┐    TCP    ┌──────────┐            │
│  │ HEI MCU  │◄────────►│ HEI MCU  │            │
│  │ zenoh-   │  direct   │ zenoh-   │            │
│  │ pico     │  peer     │ pico     │            │
│  │ peer     │           │ peer     │            │
│  └──────────┘           └──────────┘            │
│       ▲                      ▲                  │
│       │ multicast            │                  │
│       │ discovery            │                  │
│       ▼                      ▼                  │
│  ┌──────────────────────────────────────┐       │
│  │ Optional: Linux SBC (RPi, gateway)  │       │
│  │ zenohd router                        │       │
│  │  + memory storage (retained equiv)   │       │
│  │  + zenoh-plugin-mqtt (bridge)        │       │
│  │  + REST API plugin                   │       │
│  └──────────────────────────────────────┘       │
└─────────────────────────────────────────────────┘
```

Key points:

- MCU peers discover each other via multicast and communicate directly
- Each device implements a **queryable** for its own description and property values (retained message equivalent)
- Each device declares a **liveliness token** (LWT equivalent)
- An optional Linux gateway runs `zenohd` with storage (for persistence) and the MQTT bridge plugin (for backward compatibility with existing Homie/MQTT devices)

## Migration Path

The `zenoh-plugin-mqtt` plugin is critical — it makes a Zenoh router act as a full MQTT v3/v5 broker. This enables incremental adoption:

1. **Phase 1**: Existing Homie/MQTT devices connect to the Zenoh router's MQTT interface. New Zenoh-native devices connect as peers. Both see each other's data through the router.
2. **Phase 2**: Gradually migrate devices to native Zenoh as firmware is updated.
3. **Phase 3**: Once all devices are Zenoh-native, the router becomes optional infrastructure (storage, WAN bridging) rather than a mandatory broker.

## Zenoh Ecosystem and Maturity

### Adoption

- **ROS 2**: Selected as the official alternate middleware to DDS
- **Volvo**: Early adopter for automotive
- **General Motors**: Adopted via the uProtocol initiative
- Growing adoption in robotics, automotive, manufacturing, and industrial automation

### Language Bindings

| Language | Status |
|----------|--------|
| Rust | Stable (reference implementation) |
| C | Stable (zenoh-c bindings to Rust) |
| C (embedded) | Stable (zenoh-pico, independent native C implementation) |
| C++ | Stable |
| Python | Stable |
| Kotlin/Java | Beta |
| TypeScript | Alpha |

### License

Eclipse Public License 2.0 / Apache License 2.0 (dual-licensed)

## Verdict

**Feasible, with caveats.**

The core pub/sub mapping is straightforward — Zenoh key expressions are nearly identical to MQTT topics. The hard parts are replacing retained messages (solvable via queryables + optional storage) and LWT (solvable via liveliness tokens). Both solutions are arguably *better* than the MQTT equivalents for the eBus use case.

The real win: **microcontrollers can participate as first-class peers** without any broker infrastructure. For a home energy system where the grid is down and the Linux gateway has lost power, the MCU-based battery controller and solar inverter can still coordinate directly. That's a meaningful resilience improvement.

The main risk is **ecosystem maturity** — Zenoh hit 1.0 in October 2024 and the tooling is younger than MQTT's decades-old ecosystem. But the Eclipse Foundation backing, ROS 2 adoption, and automotive industry usage suggest it's on a solid trajectory.
