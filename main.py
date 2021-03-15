import json

import coloredlogs, logging

from opena3xx.networking import NetworkingClient, OpenA3xxHttpClient
from opena3xx.exceptions import NetworkingException

logger = logging.getLogger("default")
coloredlogs.install(level='debug', logger=logger)


def main():
    try:
        logger.info("Application Started")

        networking_client = NetworkingClient()
        networking_client.start_api_discovery()

        http_client = OpenA3xxHttpClient()
        data = http_client.get_configuration()

    except NetworkingException as ex:
        logger.critical(f"Networking Exception occurred with message {ex}")
    except Exception as ex:
        logger.critical(f"General Exception occurred with message {ex}")


if __name__ == '__main__':
    main()
