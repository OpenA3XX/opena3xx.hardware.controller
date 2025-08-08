### Messaging (RabbitMQ/AMQP)

Component: `opena3xx/amqp/opena3xx_rabbitmq.py`

- Initializes from Peripheral API configuration (`/configuration` endpoint) via `OpenA3xxHttpClient`.
- Connects using `pika.BlockingConnection`.
- Exchanges:
  - data: `opena3xx.hardware_events.input_selectors`
  - keepalive: `opena3xx.hardware_boards.keep_alive`

APIs:

- `init_and_start()` → creates `data_channel` and `keepalive_channel`.
- `publish_hardware_event(hardware_board_id, extender_bus_bit_details)` → publishes JSON body with board/bus/bit/selector IDs and UTC timestamp.
- `keep_alive(hardware_board_id)` → publishes periodic heartbeat; re-inits channels if closed.

GPIO feedback:

- Turns `MESSAGING_LED` on during channel recovery and event publish; clears `FAULT_LED` on success; raises `OpenA3XXRabbitMqPublishingException` on failure.


