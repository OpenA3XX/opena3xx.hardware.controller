import json

from tabulate import tabulate
import logging
import time

import busio
from RPi import GPIO
import board
from digitalio import Direction, Pull

from opena3xx.exceptions import NetworkingException
from opena3xx.logging import log_init
from opena3xx.networking import NetworkingClient, OpenA3xxHttpClient
from adafruit_mcp230xx.mcp23017 import MCP23017

log_init()
logger = logging.getLogger("default")

extender_bus_details = []
extender_bus_bit_details = []


def bus_interrupt(port):
    _bus = None
    _bus_instance = None
    _bus_pins = []
    for bus in extender_bus_details:
        if int(bus["interrupt_pin"]) == int(port):
            _bus = bus
            _bus_instance = bus["bus_instance"]
            break

    for bit in extender_bus_bit_details:
        if bit["extender_bus_id"] == _bus["extender_bus_id"]:
            _bus_pins.append(bit)

    for pin_flag in _bus_instance.int_flag:
        for pin in _bus_pins:
            if int(pin["bus_bit"]) == int(pin_flag):
                if not pin["extender_bit_instance"].value:
                    logger.warning(f"Hardware Input Selector: {pin['input_selector_name']} ===> Pressed")
                    _bus_instance.clear_ints()
                break


def main():
    try:
        logger.info("OpenA3XX Hardware Controller: Application Started")
        networking_client = NetworkingClient()
        networking_client.start_api_discovery()

        http_client = OpenA3xxHttpClient()
        data = http_client.get_configuration()

        board_details = http_client.get_hardware_board_details(1)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(24, GPIO.IN, GPIO.PUD_UP)
        GPIO.setup(23, GPIO.IN, GPIO.PUD_UP)

        # ---------------------------------------------
        # Initialize the I2C bus:
        i2c = busio.I2C(board.SCL, board.SDA)
        # ---------------------------------------------
        # Initialize the MCP23017 chips
        extender_address_start = 32

        for extender in board_details.io_extender_buses:
            logger.info(f"Registering Extender: Id:{extender.id}, {extender.name} with HEX address: "
                        f"{hex(extender_address_start)}")
            bus = MCP23017(i2c, address=extender_address_start)

            extender_data_dict = {"extender_bus_id": extender.id,
                                  "extender_bus_name": extender.name,
                                  "bus_instance": bus,
                                  "interrupt_pin": 24 if extender.id == 1 else 23}
            GPIO.add_event_detect(int(extender_data_dict["interrupt_pin"]),
                                  GPIO.FALLING,
                                  callback=bus_interrupt,
                                  bouncetime=200)
            extender_bus_details.append(extender_data_dict)

            bus.interrupt_enable = 0xFFFF
            bus.interrupt_configuration = 0x0000  # interrupt on any change
            bus.io_control = 0x44  # Interrupt as open drain and mirrored
            bus.clear_ints()  # Interrupts need to be cleared initially
            bus.default_value = 0xFFFF

            bit_counter = 0
            for extender_bit in extender.io_extender_bus_bits:
                bus_bit = int(extender_bit.name.split("Bit")[1])
                pin = bus.get_pin(bus_bit)
                extender_bit_data_dict = {"extender_bus_id": extender.id,
                                          "extender_bus_name": extender.name,
                                          "bus": bus,
                                          "extender_bit_id": extender_bit.id,
                                          "extender_bit_name": extender_bit.name,
                                          "bus_bit": bus_bit,
                                          "is_input": True if extender_bit.hardware_input_selector_fullname is not None else False,
                                          "input_selector_name": extender_bit.hardware_input_selector_fullname,
                                          "is_output": True if extender_bit.hardware_output_selector_fullname is not None else False,
                                          "output_selector_name": extender_bit.hardware_output_selector_fullname,
                                          "extender_bit_instance": pin}

                # Set Default Input Mode to Output. Not doing this will cause abnormal interrupts which are caused
                # due to the pin being in unstable state (not 0v/5v/3.3v)

                if extender_bit_data_dict["is_input"] is False and extender_bit_data_dict["is_output"] is False:
                    extender_bit_data_dict["is_output"] = True

                if extender_bit_data_dict["is_input"]:
                    pin.direction = Direction.INPUT
                    pin.pull = Pull.UP

                if extender_bit_data_dict["is_output"]:
                    pin.direction = Direction.OUTPUT

                extender_bus_bit_details.append(extender_bit_data_dict)

                bit_counter += 1

            extender_address_start += 1

        print(tabulate(extender_bus_details,  headers="keys", tablefmt="rst"))
        print(tabulate(extender_bus_bit_details, headers="keys", tablefmt="rst"))

        #for i in range(0, len(extender_bus_bit_details)):
        #    logger.info(f"{extender_bus_details[i]['extender_bus_id']}, {extender_bus_details[i]['extender_bus_name']}")

        while True:
            time.sleep(5)

    except NetworkingException as ex:
        logger.critical(f"Networking Exception occurred with message {ex}")
    # except Exception as ex:
    #    logger.critical(f"General Exception occurred with message {ex}")


if __name__ == '__main__':
    main()
