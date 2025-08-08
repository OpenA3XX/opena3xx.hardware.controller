### Hardware (GPIO, LEDs, MCP23017)

GPIO pins/constants (from `opena3xx/models/opena3xx_constants.py`):

- `MESSAGING_LED=4`, `FAULT_LED=5`, `GENERAL_LED=6`, `INPUT_SWITCH=7`
- `EXTENDER_CHIPS_RESET=18`
- `EXTENDER_ADDRESS_START=32` (0x20)
- `DEBOUNCING_TIME=10` ms
- `INTERRUPT_EXTENDER_MAP`: maps `BusN` to GPIO pins 16..27

LED pattern: `OpenA3XXHardwareLightsService.init_pattern()` flashes LEDs at startup.

MCP23017 setup: in `OpenA3XXHardwareService.init_and_start()`

- Reset extenders via `EXTENDER_CHIPS_RESET`
- For each bus:
  - I2C address increments from `EXTENDER_ADDRESS_START`
  - Configure interrupts: `interrupt_enable=0xFFFF`, `interrupt_configuration=0x0000`, `io_control=0x44`, `clear_ints()`
  - Register Pi GPIO edge detection on mapped `interrupt_pin` → callback `bus_interrupt`
  - For each bit: set `Direction.INPUT/Pull.UP` if input; `Direction.OUTPUT` if output

Interrupt callback: `bus_interrupt(port)`

- Finds matching bus and pins, loops `mcp.int_flag`, filters for active-low presses, publishes events.


