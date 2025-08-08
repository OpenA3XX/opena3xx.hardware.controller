### Architecture Overview

High-level components:

- main entry: `main.py` (Click CLI `start`) initializes logging, network discovery, HTTP client, messaging, and hardware.
- configurationless runtime: no local JSON config is read/written; runtime discovers the API and fetches remote configuration from the API.
- HTTP client: `opena3xx/http/http_api_client.py` talks to the Peripheral API to fetch configuration and hardware board details; it is constructed with the discovered endpoint.
- networking: `opena3xx/networking/opena3xx_networking_client.py` auto-detects interface/subnet and discovers the API via ping/scan; optional env overrides.
- messaging: `opena3xx/amqp/opena3xx_rabbitmq.py` publishes hardware input events and keepalive messages to RabbitMQ using configuration fetched from the API.
- hardware: `opena3xx/hardware/opena3xx_mcp23017.py` and `opena3xx/hardware/opena3xx_lights.py` manage MCP23017 IO expanders and LEDs.
- models/constants: `opena3xx/models/*` define DTOs and constants (GPIO pins, debouncing, addresses).
- logging: `opena3xx/logging/logging.py` installs colored logs.

Runtime flow (normal boot):

1. `main.py` → `log_init()`; CLI `start` requires `--hardware-board-id`.
2. `OpenA3XXNetworkingClient.start_api_discovery()` discovers/validates `OpenA3XX Peripheral API` endpoint (scheme/host/port); no local config involved.
3. `OpenA3xxHttpClient.get_hardware_board_details()` pulls the board topology (extender buses and bits).
4. `OpenA3XXMessagingService.init_and_start()` connects to RabbitMQ and opens data and keepalive channels (config fetched from API `/configuration`).
5. `OpenA3XXHardwareService.init_and_start()`
   - Configures GPIO mode and LEDs, toggles spinner pattern, resets MCP23017 chips, creates MCP23017 buses per board details.
   - Sets up extenders: interrupt pins, edge detection with debouncing, input/output pin modes per bit metadata.
6. Main loop: clears MCP interrupts, checks `INPUT_SWITCH`, publishes keepalives via messaging, sleeps.

Error handling:

- Networking errors → `OpenA3XXNetworkingException` → FAULT LED HIGH, re-raised.
- I2C MCP registration errors → `OpenA3XXI2CRegistrationException` → FAULT LED HIGH, re-raised.
- RabbitMQ publish/keepalive errors → `OpenA3XXRabbitMqPublishingException` → FAULT LED HIGH, re-raised.
- Outer `start` loop restarts the controller on any exception.

Deployment/runtime environment:

- Config path hardcoded to `/home/pi/opena3xx.hardware.controller/configuration/configuration.json`.
- Systemd service uses `start.sh` to run `python3 .../main.py --hardware-board-id=<id>`.


