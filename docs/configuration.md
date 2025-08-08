### Configuration

The application is now configurationless locally; it discovers the API endpoint and fetches configuration remotely.

- Local file `configuration/configuration.json` is no longer used at runtime.
- Remote configuration (AMQP credentials, keepalive seconds, etc.) is fetched from the API via `GET /configuration`.

Environment variable overrides (optional):

- `OPENA3XX_API_SCHEME` (default: `http`)
- `OPENA3XX_API_HOST` (if set, discovery scan is skipped and this host is used)
- `OPENA3XX_API_PORT` (default: `5000`)

Network detection on Raspberry Pi is automatic:

- Active interface is resolved via default route (fallback to first IPv4-capable interface).
- CIDR is computed from the interface netmask; subnet is scanned concurrently for the API.


