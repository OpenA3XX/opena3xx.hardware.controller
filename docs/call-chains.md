### Call Chain Analysis

Primary startup chain:

1. `main.py:start` (Click) → validates `hardware_board_id` → `main(hardware_board_id)`
2. `main`:
   - `OpenA3XXNetworkingClient.start_api_discovery()`
     - Detects default interface and its IP/netmask
     - Computes CIDR and scans subnet with concurrent TCP probes
     - Verifies candidate hosts by `OpenA3xxHttpClient.send_ping_request()` expecting `Pong from OpenA3XX`
     - Returns `(scheme, host, port)`; optional env var overrides can short-circuit scanning
   - `OpenA3xxHttpClient.get_hardware_board_details(hardware_board_id)`
   - Messaging: `OpenA3XXMessagingService.init_and_start()`
   - Hardware: `OpenA3XXHardwareService.init_and_start(board_details)`
     - `GPIO.setmode()`/LED setup → `OpenA3XXHardwareLightsService.init_pattern()`
     - Reset `EXTENDER_CHIPS_RESET`
     - For each extender bus from DTO:
       - Create `MCP23017` with incremental I2C address (from `EXTENDER_ADDRESS_START`)
       - Configure bus interrupts; register `GPIO.add_event_detect(..., callback=bus_interrupt)`
       - For each extender bit:
         - Parse pin index via `parse_bit_from_name()`
         - Configure pin `Direction.INPUT/Pull.UP` or `Direction.OUTPUT`
         - Store bit metadata in `extender_bus_bit_details`
   - Enter main loop:
     - `OpenA3XXMessagingService.keep_alive()`
     - For each bus: `bus_instance.clear_ints()`
     - If `GPIO.input(INPUT_SWITCH) == GPIO.LOW` → pulse FAULT LED → raise to restart

Interrupt handling chain (hardware event):

- GPIO edge on a configured `interrupt_pin` → `OpenA3XXHardwareService.bus_interrupt(port)`
  - Identify matching extender bus and its pins
  - For each `int_flag` reported by `MCP23017`:
    - Find matching bit, ensure active-low press (`not extender_bit_instance.value`)
    - If bit is mapped to an input selector:
      - `bus_instance.clear_ints()`
      - Turn on `MESSAGING_LED` → `OpenA3XXMessagingService.publish_hardware_event(hardware_board_id, bit)` → off LED
      - Log pressed selector
    - Errors → raise `OpenA3XXRabbitMqPublishingException` and set `FAULT_LED` HIGH

Messaging keepalive chain:

- `main` loop → `OpenA3XXMessagingService.keep_alive(hardware_board_id)`
  - Ensures channel open; on closed → re-init
  - Publishes to `opena3xx.hardware_boards.keep_alive`

Failure and restart chain:

- Any exception in `main` propagates → `start` catches → sleep(5) → restart `main`.


