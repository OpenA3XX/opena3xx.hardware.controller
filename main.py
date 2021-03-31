import json

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


def main():
    try:
        logger.info("OpenA3XX Hardware Controller: Application Started")
        networking_client = NetworkingClient()
        networking_client.start_api_discovery()

        http_client = OpenA3xxHttpClient()
        data = http_client.get_configuration()

        board_details = http_client.get_hardware_board_details(1)

        # ---------------------------------------------
        # Initialize the I2C bus:
        i2c = busio.I2C(board.SCL, board.SDA)
        # ---------------------------------------------
        # Initialize the MCP23017 chips
        extender_address_start = 32

        extender_bus_details = []
        extender_bus_bit_details = []

        for extender in board_details.io_extender_buses:
            logger.info(f"Registering Extender: Id:{extender.id}, {extender.name} with HEX address: "
                        f"{hex(extender_address_start)}")
            bus = MCP23017(i2c, address=extender_address_start)
            extender_bus_details.append({"extender_bus_id": extender.id, "extender_bus_name": extender.name,
                                         "bus_instance": bus})

            bus.interrupt_enable = 0xFFFF
            bus.interrupt_configuration = 0x0000  # interrupt on any change
            bus.io_control = 0x44  # Interrupt as open drain and mirrored
            bus.clear_ints()  # Interrupts need to be cleared initially
            bus.default_value = 0xFFFF

            bit_counter = 0
            for extender_bit in extender.io_extender_bus_bits:
                pin = bus.get_pin(bit_counter)
                extender_bit_data_dict = {"extender_bus_id": extender.id,
                                          "extender_bus_name": extender.name,
                                          "bus": bus,
                                          "extender_bit_id": extender_bit.id,
                                          "extender_bit_name": extender_bit.name,
                                          "isInput": True if extender_bit.hardware_input_selector_fullname is not None else False,
                                          "input_selector_name": extender_bit.hardware_input_selector_fullname,
                                          "isOutput": True if extender_bit.hardware_output_selector_fullname is not None else False,
                                          "output_selector_name": extender_bit.hardware_output_selector_fullname,
                                          "extender_bit_instance": pin}
                if extender_bit_data_dict["isInput"]:
                    pin.direction = Direction.INPUT
                    pin.pull = Pull.UP

                if extender_bit_data_dict["isOutput"]:
                    pin.direction = Direction.OUTPUT

                extender_bus_bit_details.append(extender_bit_data_dict)

                bit_counter += 1
            extender_address_start += 1

        # bus_instance = extender_bus_details[0]["bus_instance"]
        # bit_instance = extender_bus_bit_details[0]["extender_bit_instance"]
        bus_instance = extender_bus_details[0]
        bit_instance = extender_bus_bit_details[0]

        asdasd = 1

    except NetworkingException as ex:
        logger.critical(f"Networking Exception occurred with message {ex}")
    # except Exception as ex:
    #    logger.critical(f"General Exception occurred with message {ex}")


if __name__ == '__main__':
    main()
