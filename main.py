import coloredlogs, logging

from opena3xx.networking import NetworkingClient

logger = logging.getLogger("default")
coloredlogs.install(level='info', logger=logger)

def main():
    logger.info("Application Started")

    networking_client = NetworkingClient()
    networking_client.start_api_discovery()


if __name__ == '__main__':
    main()
