import os
from tabulate import tabulate
import logging
import time
import click
import busio
from RPi import GPIO
import board
from digitalio import Direction, Pull
from art import *
from opena3xx.exceptions import NetworkingException
from opena3xx.helpers import parse_bit_from_name
from opena3xx.logging import log_init
from opena3xx.models import INTERRUPT_EXTENDER_MAP, EXTENDER_ADDRESS_START
from opena3xx.networking import NetworkingClient, OpenA3xxHttpClient
from adafruit_mcp230xx.mcp23017 import MCP23017

log_init()
logger = logging.getLogger("default")

extender_bus_details: list = []
extender_bus_bit_details: list = []
debouncing_time: int = 80


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
                    if pin['input_selector_name'] is not None:
                        logger.warning(f"Hardware Input Selector: {pin['input_selector_name']} ===> Pressed")
                    _bus_instance.clear_ints()
                break


def screen_clear():
    if os.name == 'posix':
        _ = os.system('clear')
    else:
        _ = os.system('cls')


@click.command()
@click.option('--hardware-board-id', 'hardware_board_id', help="Hardware Board Identifier")
def main(hardware_board_id: int):
    screen_clear()
    tprint("OPENA3XX")
    try:
        if hardware_board_id is None:
            logger.critical("Hardware Board Identifier Parameter is required to run the hardware controller. Check "
                            "--hardware-board-id option.")
            exit(-1)

        extender_address_start: int = EXTENDER_ADDRESS_START
        logger.info("OpenA3XX Hardware Controller: Application Started")
        networking_client = NetworkingClient()
        networking_client.start_api_discovery()

        http_client = OpenA3xxHttpClient()
        http_client.get_configuration()

        board_details = http_client.get_hardware_board_details(hardware_board_id)
        if board_details is not None:
            GPIO.setmode(GPIO.BCM)

            # ---------------------------------------------
            # Initialize the I2C bus:
            i2c = busio.I2C(board.SCL, board.SDA)
            # ---------------------------------------------

            for extender in board_details.io_extender_buses:
                logger.info(f"Registering Extender: Id:{extender.id}, {extender.name} with HEX address: "
                            f"{hex(extender_address_start)}")
                bus = MCP23017(i2c, address=extender_address_start)

                extender_data_dict = {"extender_bus_id": extender.id,
                                      "extender_bus_name": extender.name,
                                      "bus_instance": bus,
                                      "interrupt_pin": INTERRUPT_EXTENDER_MAP[extender.name]}
                GPIO.setup(int(extender_data_dict["interrupt_pin"]), GPIO.IN, GPIO.PUD_UP)
                GPIO.add_event_detect(int(extender_data_dict["interrupt_pin"]),
                                      GPIO.FALLING,
                                      callback=bus_interrupt,
                                      bouncetime=debouncing_time)
                extender_bus_details.append(extender_data_dict)

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
                                                  is_output=True if extender_bit.hardware_output_selector_fullname is not None else False,
                                                  output_selector_name=extender_bit.hardware_output_selector_fullname,
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

                    extender_bus_bit_details.append(extender_bit_data_dict)
                    bit_counter += 1
                extender_address_start += 1

            logger.info(f"\n{tabulate(extender_bus_details, headers='keys', tablefmt='pretty')}")
            logger.info(f"\n{tabulate(extender_bus_bit_details, headers='keys', tablefmt='pretty')}")

            while True:
                time.sleep(5)

        else:
            logger.critical(f"Hardware Board with Id: {hardware_board_id} seems to be invalid. No Response for "
                            f"OpenA3XX Peripheral API")

    except NetworkingException as ex:
        logger.critical(f"Networking Exception occurred with message {ex}")
    except Exception as ex:
        logger.critical(f"General Exception occurred with message {ex}")


if __name__ == '__main__':
    main()
