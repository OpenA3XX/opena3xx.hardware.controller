from opena3xx.configuration import *
import netifaces as ni
import logging

logger = logging.getLogger("default")

OPENA3XX_NETWORK_INTERFACE_CONFIGURATION_NAME = "opena3xx.network.interface"


class NetworkingClient:

    def start_api_discovery(self) -> None:
        configuration = ConfigurationClient.get_configuration().networking
        interface = configuration[OPENA3XX_NETWORK_INTERFACE_CONFIGURATION_NAME]
        ip = self.__discover_local_ip_address(interface)
        print(ip)

    @staticmethod
    def __discover_local_ip_address(interface: str) -> str:
        logger.info("Discovering Local IP Address")
        ni.ifaddresses(interface)
        ip = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
        logger.info(f"Local IP Address is {ip}")
        return ip