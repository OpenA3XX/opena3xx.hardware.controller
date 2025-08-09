### Networking and HTTP API

Networking discovery: `opena3xx/networking/opena3xx_networking_client.py`

- Auto-detects active interface via default route (fallback: first IPv4 interface)
- Derives CIDR from netmask and scans subnet with concurrent TCP probes
- Verifies candidate via `OpenA3xxHttpClient.send_ping_request()` to `/core/heartbeat/ping` expecting `Pong from OpenA3XX`
- Returns `(scheme, host, port)` using fixed defaults: `scheme=http`, `port=5000`. No environment variables are used.

HTTP client: `opena3xx/http/http_api_client.py`

- Constructed with discovered `scheme`, `base_url`, and `port`
- Reuses a session with retries/backoff; consistent 10s timeouts
- `get_configuration()` → fetches API configuration JSON (flat object)
- `get_hardware_board_details(hardware_board_id)` → returns `HardwareBoardDetailsDto` built from JSON with bus/bit metadata


