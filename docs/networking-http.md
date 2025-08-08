### Networking and HTTP API

Networking discovery: `opena3xx/networking/opena3xx_networking_client.py`

- Auto-detects active interface via default route (fallback: first IPv4 interface)
- Derives CIDR from netmask and scans subnet with concurrent TCP probes
- Verifies candidate via `OpenA3xxHttpClient.send_ping_request()` to `/core/heartbeat/ping` expecting `Pong from OpenA3XX`
- Returns `(scheme, host, port)` where `scheme` and `port` default to `http` and `5000`, overridable with env vars

HTTP client: `opena3xx/http/http_api_client.py`

- Constructed with discovered `scheme`, `base_url`, and `port`
- `get_configuration()` → fetches API configuration JSON
- `get_hardware_board_details(hardware_board_id)` → returns `HardwareBoardDetailsDto` built from JSON with bus/bit metadata


