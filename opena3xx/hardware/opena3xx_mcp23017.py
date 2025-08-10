import logging

import board
import time
import busio
from opena3xx.hardware.gpio_shim import GPIO
from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction, Pull
from tabulate import tabulate

from opena3xx.amqp import OpenA3XXMessagingService
from opena3xx.exceptions import OpenA3XXI2CRegistrationException, OpenA3XXRabbitMqPublishingException
from opena3xx.hardware.opena3xx_lights import OpenA3XXHardwareLightsService
from opena3xx.helpers import parse_bit_from_name
from opena3xx.models import HardwareBoardDetailsDto, MESSAGING_LED, FAULT_LED, GENERAL_LED, EXTENDER_CHIPS_RESET, \
    INPUT_SWITCH
from opena3xx.models import INTERRUPT_EXTENDER_MAP, EXTENDER_ADDRESS_START, DEBOUNCING_TIME


class OpenA3XXHardwareService:

    def __init__(self, messaging_service: OpenA3XXMessagingService, hardware_board_id: int):
        self.extender_bus_details: list = []
        self.extender_bus_bit_details: list = []
        self.debouncing_time: int = DEBOUNCING_TIME
        self.logger = logging.getLogger(self.__class__.__name__)
        self.messaging_service: OpenA3XXMessagingService = messaging_service
        self.hardware_board_id = hardware_board_id

    def bus_interrupt(self, port):
        """GPIO interrupt callback for extender bus IRQ lines.

        Identifies the associated extender bus, reads MCP23017 interrupt flags
        to locate the triggered bit(s), and publishes an event if the bit is
        mapped to a hardware input selector. LEDs provide brief visual feedback.
        """
        GPIO.output(GENERAL_LED, GPIO.HIGH)
        self.logger.debug(f"Interrupt received on port {port}")
        _bus = None
        _bus_instance = None
        _bus_pins = []

        for bus in self.extender_bus_details:
            if int(bus["interrupt_pin"]) == int(port):
                _bus = bus
                _bus_instance = bus["bus_instance"]
                break

        if _bus is None or _bus_instance is None:
            self.logger.warning(f"No extender bus matched for interrupt port {port}")
            GPIO.output(GENERAL_LED, GPIO.LOW)
            return

        self.logger.debug(f"Matched interrupt to bus id={_bus['extender_bus_id']} name={_bus['extender_bus_name']}")

        for bit in self.extender_bus_bit_details:
            if bit["extender_bus_id"] == _bus["extender_bus_id"]:
                _bus_pins.append(bit)

        try:
            flags = list(_bus_instance.int_flag)
            self.logger.debug(f"MCP int_flag values: {flags}")
            for pin_flag in flags:
                for pin in _bus_pins:
                    if int(pin["bus_bit"]) == int(pin_flag):
                        pin_value = pin["extender_bit_instance"].value
                        self.logger.debug(
                            f"Flag {pin_flag} -> bit {pin['bus_bit']} name={pin['extender_bit_name']} value={pin_value}"
                        )
                        if not pin_value:
                            if pin['input_selector_name'] is not None:
                                try:
                                    GPIO.output(MESSAGING_LED, GPIO.HIGH)
                                    self.messaging_service.publish_hardware_event(self.hardware_board_id, pin)
                                    GPIO.output(MESSAGING_LED, GPIO.LOW)
                                    self.logger.warning(
                                        f"Hardware Input Selector: {pin['input_selector_name']} ===> Pressed"
                                    )
                                except OpenA3XXRabbitMqPublishingException as ex:
                                    GPIO.output(FAULT_LED, GPIO.HIGH)
                                    raise ex
                            else:
                                self.logger.debug("Interrupt from a non-mapped input selector; ignoring")
                        break
        finally:
            # Always clear interrupts to release the IRQ line
            try:
                _bus_instance.clear_ints()
            except Exception:
                pass
            GPIO.output(GENERAL_LED, GPIO.LOW)

    def init_and_start(self, board_details: HardwareBoardDetailsDto):
        """Initialize GPIO, I2C, extenders, and register interrupt handlers."""
        self.logger.info("Initializing hardware service (GPIO/MCP23017)")
        try:
            GPIO.setmode(GPIO.BCM)
        except Exception as ex:
            self.logger.critical(f"Failed to set GPIO mode: {ex}")
            raise OpenA3XXI2CRegistrationException(ex)

        i2c = self._init_i2c()
        self._setup_gpio_basics()
        self._reset_extenders()
        self._register_extenders(i2c, board_details)
        self._log_summary()

    def _init_i2c(self):
        self.logger.debug("Initializing I2C bus on board.SCL/board.SDA")
        return busio.I2C(board.SCL, board.SDA)

    def _setup_gpio_basics(self):
        # Initialize GPIO pins for LEDs and switches
        GPIO.setup(MESSAGING_LED, GPIO.OUT)
        GPIO.setup(FAULT_LED, GPIO.OUT)
        GPIO.setup(GENERAL_LED, GPIO.OUT)
        GPIO.setup(EXTENDER_CHIPS_RESET, GPIO.OUT)
        GPIO.setup(INPUT_SWITCH, GPIO.IN)

        # Initialize INPUT_SWITCH
        try:
            input_switch_value = GPIO.input(INPUT_SWITCH)
            self.logger.info(f"INPUT_SWITCH initial state: {'LOW' if input_switch_value == GPIO.LOW else 'HIGH'}")
        except Exception:
            self.logger.warning("Unable to read INPUT_SWITCH initial state")

        # Initialize the LED pattern
        OpenA3XXHardwareLightsService.init_pattern()

    def _reset_extenders(self):
        # Reset the MCP23017 ICs
        self.logger.info("Resetting MCP23017 ICs Reset Pin: Started")
        GPIO.output(EXTENDER_CHIPS_RESET, GPIO.LOW)
        time.sleep(1)
        GPIO.output(EXTENDER_CHIPS_RESET, GPIO.HIGH)
        time.sleep(1)
        self.logger.info("Resetting MCP23017 ICs Reset Pin: Completed")

    def _register_extenders(self, i2c, board_details: HardwareBoardDetailsDto):
        extender_address_start: int = EXTENDER_ADDRESS_START
        for extender in board_details.io_extender_buses:
            self._register_single_extender(i2c, extender, extender_address_start)
            extender_address_start += 1

    def _register_single_extender(self, i2c, extender, address: int) -> None:
        self.logger.info(
            f"Registering Bus Extender: Id:{extender.id}, {extender.name} with HEX address: {hex(address)}"
        )
        GPIO.output(GENERAL_LED, GPIO.HIGH)
        try:
            bus = MCP23017(i2c, address=address)
            self.logger.info(
                f"Registering Bus Extender with details: Id:{extender.id}, Name:{extender.name}: Found"
            )
        except Exception as ex:
            self.logger.critical(
                f"Failed Registering Bus Extender with details: Id:{extender.id}, Name:{extender.name}"
            )
            raise OpenA3XXI2CRegistrationException(ex)
        finally:
            GPIO.output(GENERAL_LED, GPIO.LOW)

        extender_data_dict = {
            "extender_bus_id": extender.id,
            "extender_bus_name": extender.name,
            "bus_instance": bus,
            "interrupt_pin": INTERRUPT_EXTENDER_MAP[extender.name],
        }

        # Configure MCP23017 core registers first
        self.logger.debug("Configuring MCP23017 core registers and defaults")
        bus.io_control = 0x44  # Interrupt as open drain and mirrored
        bus.default_value = 0x0000
        bus.interrupt_configuration = 0x0000  # interrupt on any change
        bus.clear_ints()  # clear any stale flags

        # Configure all extender bits for this bus (direction/pulls/defaults)
        for extender_bit in extender.io_extender_bus_bits:
            self._configure_extender_bit(bus, extender, extender_bit)

        # Compute interrupt enable mask for input pins only
        input_interrupt_mask = 0
        for bit in extender.io_extender_bus_bits:
            try:
                bus_bit = parse_bit_from_name(bit.name)
                if bit.hardware_input_selector_fullname:
                    input_interrupt_mask |= (1 << bus_bit)
            except Exception:
                # Ignore malformed names here; they are already logged in _configure_extender_bit
                continue

        # Optional diagnostic override: enable all interrupt bits if requested
        try:
            import os
            if os.getenv("OPENA3XX_FORCE_ENABLE_ALL_INTERRUPTS", "0") in ("1", "true", "True"):
                self.logger.warning(
                    "Environment override OPENA3XX_FORCE_ENABLE_ALL_INTERRUPTS active: enabling 0xFFFF"
                )
                input_interrupt_mask = 0xFFFF
        except Exception:
            pass

        # Clear any pending interrupts before enabling
        bus.clear_ints()
        bus.interrupt_enable = input_interrupt_mask

        # Log mask and potential misconfiguration
        enabled_bits = [idx for idx in range(16) if (input_interrupt_mask >> idx) & 1]
        self.logger.debug(
            f"Interrupts enabled on input bits for {extender.name}: mask=0x{input_interrupt_mask:04X}, bits={enabled_bits}"
        )
        if input_interrupt_mask == 0:
            self.logger.warning(
                f"No input bits found for {extender.name}. Interrupts will not fire for this extender."
            )

        # Wire the Raspberry Pi interrupt after MCP is fully configured
        self.logger.debug(
            f"Configuring interrupt GPIO pin {extender_data_dict['interrupt_pin']} for bus {extender.name}"
        )
        GPIO.setup(int(extender_data_dict["interrupt_pin"]), GPIO.IN, GPIO.PUD_UP)
        GPIO.add_event_detect(
            int(extender_data_dict["interrupt_pin"]),
            GPIO.FALLING,
            callback=self.bus_interrupt,
            bouncetime=self.debouncing_time,
        )

        # If the IRQ line is already asserted low at registration time,
        # trigger the handler once to service any pending interrupts.
        try:
            if GPIO.input(int(extender_data_dict["interrupt_pin"])) == GPIO.LOW:
                self.logger.debug(
                    f"Interrupt line low at registration for {extender.name}; invoking handler immediately"
                )
                self.bus_interrupt(int(extender_data_dict["interrupt_pin"]))
        except Exception:
            pass

        self.extender_bus_details.append(extender_data_dict)

    def _configure_extender_bit(self, bus, extender, extender_bit) -> None:
        # Parse the bit index from the name defensively
        try:
            bus_bit = parse_bit_from_name(extender_bit.name)
            if not (0 <= bus_bit <= 15):
                raise ValueError(f"Invalid bus_bit {bus_bit} for '{extender_bit.name}'")
        except Exception as ex:
            self.logger.error(f"Unable to parse bus bit for '{extender_bit.name}': {ex}")
            return

        pin = bus.get_pin(bus_bit)

        is_input = bool(extender_bit.hardware_input_selector_fullname)
        is_output = bool(extender_bit.hardware_output_selector_fullname)

        if is_input and is_output:
            self.logger.warning(
                f"Extender bit '{extender_bit.name}' is marked as both INPUT and OUTPUT; prioritizing INPUT"
            )

        # Default to OUTPUT if neither role is defined to avoid floating states
        if not is_input and not is_output:
            is_output = True

        if is_input:
            pin.direction = Direction.INPUT
            pin.pull = Pull.UP
            self.logger.debug(
                f"Configured extender bit '{extender_bit.name}' as INPUT (bus_bit={bus_bit}) with PULL.UP"
            )
        else:
            pin.direction = Direction.OUTPUT
            try:
                pin.value = False  # known safe default level
            except Exception:
                pass
            self.logger.debug(
                f"Configured extender bit '{extender_bit.name}' as OUTPUT (bus_bit={bus_bit})"
            )

        extender_bit_data_dict = dict(
            extender_bus_id=extender.id,
            extender_bus_name=extender.name,
            bus=bus,
            extender_bit_id=extender_bit.id,
            extender_bit_name=extender_bit.name,
            bus_bit=bus_bit,
            is_input=is_input,
            input_selector_name=extender_bit.hardware_input_selector_fullname,
            input_selector_id=extender_bit.hardware_input_selector_id,
            is_output=is_output,
            output_selector_name=extender_bit.hardware_output_selector_fullname,
            output_selector_id=extender_bit.hardware_output_selector_id,
            extender_bit_instance=pin,
        )

        self.extender_bus_bit_details.append(extender_bit_data_dict)

    def _log_summary(self):
        # Log a concise view by selecting specific columns from details
        bus_columns = ["extender_bus_id", "extender_bus_name", "interrupt_pin"]
        bit_columns = [
            "extender_bus_id",
            "extender_bit_id",
            "extender_bus_name",
            "extender_bit_name",
            "bus_bit",
            "is_input",
            "input_selector_name",
            "is_output",
            "output_selector_name",
        ]

        def _select_columns(rows: list, cols: list[str]) -> list[list]:
            # Return rows as lists aligned to the headers order
            selected_rows: list[list] = []
            for row in rows:
                selected_rows.append([row.get(c) for c in cols])
            return selected_rows

        # Sort by extender bus name for buses
        sorted_buses = sorted(
            self.extender_bus_details,
            key=lambda r: (
                str(r.get("extender_bus_name", "")),
                int(r.get("interrupt_pin", 0)),
            ),
        )

        # Sort by extender bus name and numeric bus_bit for bits
        sorted_bits = sorted(
            self.extender_bus_bit_details,
            key=lambda r: (
                str(r.get("extender_bus_name", "")),
                int(r.get("bus_bit", 0)),
            ),
        )

        bus_table = tabulate(_select_columns(sorted_buses, bus_columns), headers=bus_columns, tablefmt='grid')
        bit_table = tabulate(_select_columns(sorted_bits, bit_columns), headers=bit_columns, tablefmt='grid')

        self.logger.info(f"Extender Bus Details ↓\n{bus_table}")
        self.logger.info(f"Extender Bus Bit Details ↓\n{bit_table}")
