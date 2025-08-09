### Configuration

- The application is configurationless locally; it discovers the API and fetches all settings remotely.
- Local file `configuration/configuration.json` is not used at runtime.
- Remote configuration (AMQP host/port/username/vhost, keepalive seconds, etc.) is fetched from the API via `GET /configuration` and is expected as a flat JSON object (no top-level wrapper).

Networking discovery is automatic:

- The active interface is determined via the default route (fallback to first IPv4-capable interface).
- The subnet is derived from the interface netmask and scanned for the Peripheral API.
- The API is expected at scheme `http` on port `5000`. There are no environment variables used for discovery or configuration.


