import os
import logging
import time
import click
from art import *
from opena3xx.exceptions import NetworkingException
from opena3xx.hardware.opena3xx_mcp23017 import OpenA3XXHardwareService
from opena3xx.logging import log_init
from opena3xx.networking import NetworkingClient, OpenA3xxHttpClient

log_init()
logger = logging.getLogger("default")


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

        logger.info("OpenA3XX Hardware Controller: Application Started")
        networking_client = NetworkingClient()
        networking_client.start_api_discovery()

        http_client = OpenA3xxHttpClient()
        http_client.get_configuration()

        board_details = http_client.get_hardware_board_details(hardware_board_id)
        if board_details is not None:
            hardware_service = OpenA3XXHardwareService()
            hardware_service.init_and_start(board_details)

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
