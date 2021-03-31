from opena3xx.configuration import *
import netifaces as ni
import logging
from netaddr import IPNetwork
import socket
from opena3xx.exceptions import NetworkingException
from opena3xx.http import OpenA3xxHttpClient
from opena3xx.models import *


class NetworkingClient:
    configuration = []

    logger = logging.getLogger("default")

    def start_api_discovery(self) -> None:
        try:
            self.configuration = ConfigurationClient.get_configuration()
            interface = self.configuration[OPENA3XX_NETWORK_INTERFACE_CONFIGURATION_NAME]
            ip = self.__discover_local_ip_address(interface)
            if not self.configuration[OPENA3XX_API_IP_ADDRESS_CONFIGURATION_NAME]:
                self.__scan_network(ip)
            else:
                self.__ping_request_target(self.configuration[OPENA3XX_API_IP_ADDRESS_CONFIGURATION_NAME],
                                           self.configuration[OPENA3XX_API_PORT_CONFIGURATION_NAME])
        except Exception as ex:
            raise NetworkingException(ex)

    def __ping_request_target(self, target_ip: str, target_port: int) -> bool:
        try:
            scheme = self.configuration[OPENA3XX_API_SCHEME_CONFIGURATION_NAME]
            http_client = OpenA3xxHttpClient()
            r = http_client.send_ping_request(scheme, target_ip, target_port)
            if r.status_code == 200:
                if r.text == "Pong from OpenA3XX":
                    logging.info("Received Valid Response from OpenA3XX API - Success")
                    return True
            else:
                logger.info("Invalid Response from OpenA3XX API")
            return False
        except Exception as ex:
            logger.critical(ex)
            return False

    def __scan_network(self, local_ip_address):
        logger.info("Started Scanning Network")
        cidr = self.configuration[OPENA3XX_SCAN_CIDR_RANGE_CONFIGURATION_NAME]
        opena3xx_api_port = self.configuration[OPENA3XX_API_PORT_CONFIGURATION_NAME]
        cidr_range = f"{local_ip_address}/{cidr}"

        for ip in IPNetwork(cidr_range):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.setdefaulttimeout(0.1)
            target_ip_address = socket.gethostbyname(str(ip))
            # returns an error indicator
            result = s.connect_ex((target_ip_address, int(opena3xx_api_port)))
            if result == 0:
                logger.info(f"Found something on IP: {target_ip_address} on Port: {opena3xx_api_port}")
                logger.info("Sending Ping to check if it is OpenA3XX API")
                if self.__ping_request_target(target_ip_address, opena3xx_api_port):
                    self.configuration[OPENA3XX_API_IP_ADDRESS_CONFIGURATION_NAME] = target_ip_address
                    ConfigurationClient.update_configuration(self.configuration)
                    s.close()
                    return True
                else:
                    logger.warning(f"Continue scanning: Invalid Response from {target_ip_address}")
            s.close()
        return False

    @staticmethod
    def __discover_local_ip_address(interface: str) -> str:
        try:
            logger.info("Discovering Local IP Address")
            ip = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
            logger.info(f"Local IP Address is {ip}")
            return ip
        except Exception as ex:
            raise ex
