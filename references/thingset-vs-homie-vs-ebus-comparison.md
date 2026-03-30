# ThingSet vs. Homie vs. eBus — Comparison Summary

## What Each Is

| | **ThingSet** | **Homie** | **eBus** |
|---|---|---|---|
| **Type** | Transport-agnostic application-layer protocol | MQTT convention | Interoperability framework for home energy |
| **Focus** | Resource-constrained device communication | Standardized IoT device representation over MQTT | Home energy infrastructure (HEI) device coordination |
| **Origin** | Energy management (Libre Solar) | General IoT | Home electrification |
| **License** | CC BY-SA 4.0 | CC BY-SA 4.0 | Open |

## Data Model

Both ThingSet and Homie use **hierarchical trees**, but structure them differently:

- **Homie**: Device → Node → Property. Properties have typed values (string, int, float, bool, enum, color, datetime, duration, JSON). All values are UTF-8 strings on the wire.
- **ThingSet**: Flat tree with Groups, Subsets, Records, and Data Items. Items identified by naming prefixes (`r` = read-only, `s` = stored config, `x` = executable, etc.). Supports both JSON (text) and CBOR (binary) encoding.
- **eBus**: Adopts Homie's data model directly.

## Transport & Discovery

| | **ThingSet** | **Homie** | **eBus** |
|---|---|---|---|
| **Primary transport** | Any (serial, CAN, BLE, LoRa, MQTT, CoAP, HTTP, WebSocket) | MQTT only | MQTT + HTTP REST |
| **Discovery** | Self-describing tree traversal, metadata URLs | MQTT retained messages + `$state` wildcards | mDNS + Homie self-description |
| **Binary mode** | Yes (CBOR) — critical for CAN, LoRa | No — UTF-8 strings only | No |
| **Device lifecycle** | Stateless (no session) | Explicit states: init → ready → disconnected/sleeping/lost | Inherits Homie lifecycle |

## Key Differences

### ThingSet strengths

- **Transport-agnostic** — works over CAN bus (8-64 bytes), LoRaWAN, serial UART, BLE, and MQTT/CoAP/HTTP
- **Binary mode (CBOR)** — essential for extremely constrained networks (CAN, LoRa)
- **Targets Class 0 devices** — << 10 KiB RAM, << 100 KiB Flash
- **Built-in CRUD semantics** — GET, FETCH, UPDATE, CREATE, DELETE, EXEC with CoAP-style status codes
- **Units baked into naming** — `rTemp_degC`, `rVoltage_V` (SI-only, URI-safe)
- **Desires** — fire-and-forget async updates for M2M control loops

### Homie strengths

- **Mature MQTT convention** — well-defined topic structure with QoS 2 reliability
- **Rich device lifecycle** — init/ready/disconnected/sleeping/lost states with Last Will
- **Settable + target mechanism** — commands via `/set` topics, gradual transitions via `$target`
- **Extensions system** — pluggable additional capabilities (stats, firmware, metadata)
- **Parent-child device hierarchy** — bridges/gateways can expose child devices
- **Broader datatype support** — color (RGB/HSV/XYZ), datetime, duration, JSON

### eBus strengths

- **Domain-specific** — purpose-built for home energy (solar, batteries, panels, meters, MIDs)
- **Full stack** — combines mDNS discovery + MQTT/Homie messaging + REST APIs + TLS security
- **Adapter architecture** — bridges non-eBus protocols (Matter, CTA-2045, Modbus) into the ecosystem
- **Local-first** — no cloud dependency; works during grid outages

## Where They Overlap & Diverge

ThingSet and Homie solve a **similar problem** (standardized IoT device communication) but from different angles:
- ThingSet starts from **embedded/constrained devices** and maps upward to MQTT/CoAP
- Homie starts from **MQTT** and defines conventions for IP-capable devices

eBus is a **higher-level framework** that chose Homie as its communication layer. ThingSet could theoretically serve as an alternative foundation, but:

1. **ThingSet's MQTT mapping** uses a different topic structure (`rpt/{node-id}/{group}`) than Homie (`homie/5/{device-id}/{node}/{property}`), so they're **not directly compatible** on the wire
2. ThingSet's strength in **CAN/serial/LoRa** is less relevant to eBus's target (home energy devices typically have Ethernet/Wi-Fi)
3. ThingSet's **naming convention** (prefixed data items like `rVoltage_V`) encodes semantics differently than Homie's typed properties with separate `$unit` attributes
4. ThingSet is still **pre-1.0** (v0.6) with breaking changes between versions

## Bottom Line

ThingSet is an interesting protocol, especially for deeply embedded energy devices (it originated from Libre Solar's charge controllers). If eBus ever needed to support **CAN bus or serial-connected devices** directly (not through an adapter), ThingSet's binary mode would be valuable. However, for the current eBus use case — IP-networked home energy devices coordinating over MQTT — Homie is a more natural fit with a more mature ecosystem and clearer device lifecycle management.

The two aren't mutually exclusive: a ThingSet-to-Homie **adapter** (an eBus "rider") could bridge CAN-connected devices (like battery BMSes or solar charge controllers using ThingSet) into the eBus ecosystem.
