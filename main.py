import json

import logging
import time

from opena3xx.exceptions import NetworkingException
from opena3xx.logging import log_init
from opena3xx.networking import NetworkingClient, OpenA3xxHttpClient

log_init()
logger = logging.getLogger("default")


def main():
    try:

        logger.info("OpenA3XX Hardware Controller: Application Started")
        networking_client = NetworkingClient()
        networking_client.start_api_discovery()

        http_client = OpenA3xxHttpClient()
        data = http_client.get_configuration()

        x = http_client.get_hardware_board_details(1)

    except NetworkingException as ex:
        logger.critical(f"Networking Exception occurred with message {ex}")
    except Exception as ex:
        logger.critical(f"General Exception occurred with message {ex}")
    time.sleep(5)


if __name__ == '__main__':
    main()
