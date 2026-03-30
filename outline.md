# eBus Specification Outline

An "eBus entity" is a network host that implements the Homie/eBus device-role, the controller-role, or both.

## Networking
- An eBus entity MUST support at least one IP network interface (Ethernet or Wi-Fi)
- An eBus entity with active Ethernet SHOULD disable Wi-Fi, unless configured otherwise
- An eBus entity SHOULD use its configuration to configure network interfaces
- An eBus entity with only an unconfigured Wi-Fi interface MAY provide a hosted AP for Wi-Fi provisioning

## TLS
- An eBus entity SHOULD use TLS for MQTT and HTTP connections
- An eBus entity MAY fall back to non-TLS if TLS is not implemented/feasible
- An eBus entity supporting TLS SHOULD provide a REST endpoint to download its CA certificate (unauthenticated)
- An eBus entity supporting TLS SHOULD provide a REST endpoint to upload a CA certificate for the MQTT broker

## mDNS
- An eBus entity MUST claim a unique `.local` mDNS hostname (SHOULD incorporate a unique identifier such as MAC address or serial number)
- An eBus entity MUST advertise `_ebus._tcp` and `_device-info._tcp` metadata services
- An eBus entity that hosts an MQTT broker MUST advertise it via mDNS (`_secure-mqtt._tcp`, `_mqtt._tcp`, etc.)
- An eBus entity that offers an HTTP REST API MUST advertise it via mDNS (`_http._tcp` / `_https._tcp`)
- An eBus entity that does not self-host a broker MUST attempt mDNS discovery of an eBus MQTT broker

## MQTT / Homie
- An eBus entity SHOULD use MQTT 5.0; MAY use MQTT 3.1.1
- eBus uses `ebus` as the Homie topic domain: `ebus/5/{device-id}/...`
- An eBus device-role entity MUST comply with the Homie Convention v5.0 (device description, lifecycle, property publication, datatypes)
- An eBus entity SHOULD use QoS 2 for property values, QoS 0 for `/set` commands
- eBus device/node types use `energy.ebus.device.*` namespace; manufacturers MAY use their own prefix

## REST API / Configuration
- MQTT is primary (real-time state, pub/sub); REST is complementary (configuration, administration, bootstrap)
- An eBus entity SHOULD have baked-in default configuration; dynamic configuration via REST SHOULD override defaults
- An eBus entity SHOULD provide an HTTP REST API for configuration and administration
- An eBus entity's REST API SHOULD be documented via OpenAPI, served by the entity via HTTP
- An eBus entity SHOULD provide a registration endpoint that exchanges a device passphrase for API credentials and MQTT broker connection details
- An eBus entity MAY provide an HTTP GUI; the GUI SHOULD use the REST API

## MQTT Broker Configuration
- An eBus entity's configuration SHOULD include a broker URL and mode: `configured-only`, `discovery-with-fallback`, or `discovery-only` (default)

## OTA
- An eBus entity SHOULD support a REST endpoint to initiate OTA firmware update
- The OTA update server URL SHOULD be obtained from configuration
- An OTA update MUST NOT permanently brick the device

## Adapters
- An adapter is an eBus entity (device-role) that bridges a non-eBus device by translating its native protocol to Homie/MQTT
- An adapter's Homie device is indistinguishable from a native eBus device
- Adapters for cloud APIs SHOULD cache data locally
