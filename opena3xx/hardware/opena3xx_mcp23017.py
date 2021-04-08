import logging

import board
import busio
from RPi import GPIO
from adafruit_mcp230xx.mcp23017 import MCP23017
from digitalio import Direction, Pull
from tabulate import tabulate

from opena3xx.amqp import OpenA3XXMessagingService
from opena3xx.exceptions import OpenA3XXI2CRegistrationException, OpenA3XXRabbitMqPublishingException
from opena3xx.helpers import parse_bit_from_name
from opena3xx.models import HardwareBoardDetailsDto
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
        _bus = None
        _bus_instance = None
        _bus_pins = []
        for bus in self.extender_bus_details:
            if int(bus["interrupt_pin"]) == int(port):
                _bus = bus
                _bus_instance = bus["bus_instance"]
                break

        for bit in self.extender_bus_bit_details:
            if bit["extender_bus_id"] == _bus["extender_bus_id"]:
                _bus_pins.append(bit)

        for pin_flag in _bus_instance.int_flag:
            for pin in _bus_pins:
                if int(pin["bus_bit"]) == int(pin_flag):
                    if not pin["extender_bit_instance"].value:
                        if pin['input_selector_name'] is not None:
                            try:
                                self.messaging_service.publish_hardware_event(self.hardware_board_id, pin)
                                self.logger.warning(f"Hardware Input Selector: {pin['input_selector_name']} ===> Pressed")
                            except OpenA3XXRabbitMqPublishingException as ex:
                                raise ex
                        _bus_instance.clear_ints()
                    break

    def init_and_start(self, board_details: HardwareBoardDetailsDto):
        GPIO.setmode(GPIO.BCM)
        extender_address_start: int = EXTENDER_ADDRESS_START
        # ---------------------------------------------
        # Initialize the I2C bus:
        i2c = busio.I2C(board.SCL, board.SDA)
        # ---------------------------------------------
        for extender in board_details.io_extender_buses:
            self.logger.info(f"Registering Bus Extender: Id:{extender.id}, {extender.name} with HEX address: "
                        f"{hex(extender_address_start)}")
            try:
                bus = MCP23017(i2c, address=extender_address_start)
                self.logger.info(f"Registering Bus Extender with details: Id:{extender.id}, Name:{extender.name}: Found")
            except Exception as ex:
                self.logger.critical(f"Failed Registering Bus Extender with details: Id:{extender.id}, Name:{extender.name}")
                raise OpenA3XXI2CRegistrationException(ex)

            extender_data_dict = {"extender_bus_id": extender.id,
                                  "extender_bus_name": extender.name,
                                  "bus_instance": bus,
                                  "interrupt_pin": INTERRUPT_EXTENDER_MAP[extender.name]}
            GPIO.setup(int(extender_data_dict["interrupt_pin"]), GPIO.IN, GPIO.PUD_UP)
            GPIO.add_event_detect(int(extender_data_dict["interrupt_pin"]),
                                  GPIO.FALLING,
                                  callback=self.bus_interrupt,
                                  bouncetime=self.debouncing_time)
            self.extender_bus_details.append(extender_data_dict)

            bus.interrupt_enable = 0xFFFF
            bus.interrupt_configuration = 0x0000  # interrupt on any change
            bus.io_control = 0x44  # Interrupt as open drain and mirrored
            bus.clear_ints()  # Interrupts need to be cleared initially
            bus.default_value = 0xFFFF

            bit_counter = 0
            for extender_bit in extender.io_extender_bus_bits:
                bus_bit = parse_bit_from_name(extender_bit.name)
                pin = bus.get_pin(bus_bit)
                extender_bit_data_dict = dict(extender_bus_id=extender.id, extender_bus_name=extender.name, bus=bus,
                                              extender_bit_id=extender_bit.id, extender_bit_name=extender_bit.name,
                                              bus_bit=bus_bit,
                                              is_input=True if extender_bit.hardware_input_selector_fullname is not None else False,
                                              input_selector_name=extender_bit.hardware_input_selector_fullname,
                                              input_selector_id=extender_bit.hardware_input_selector_id,
                                              is_output=True if extender_bit.hardware_output_selector_fullname is not None else False,
                                              output_selector_name=extender_bit.hardware_output_selector_fullname,
                                              output_selector_id=extender_bit.hardware_output_selector_id,
                                              extender_bit_instance=pin)

                # Set Default Input Mode to Output. Not doing this will cause abnormal interrupts which are caused
                # due to the pin being in unstable state (not 0v/5v/3.3v)
                if extender_bit_data_dict["is_input"] is False and extender_bit_data_dict["is_output"] is False:
                    extender_bit_data_dict["is_output"] = True

                if extender_bit_data_dict["is_input"]:
                    pin.direction = Direction.INPUT
                    pin.pull = Pull.UP

                if extender_bit_data_dict["is_output"]:
                    pin.direction = Direction.OUTPUT

                self.extender_bus_bit_details.append(extender_bit_data_dict)
                bit_counter += 1
            extender_address_start += 1

        self.logger.info(f"Extender Bus Details ↓\n{tabulate(self.extender_bus_details, headers='keys', tablefmt='pretty')}")
        self.logger.info(f"Extender Bus Bit Details ↓\n{tabulate(self.extender_bus_bit_details, headers='keys', tablefmt='pretty')}")
