from opena3xx.configuration import *
import netifaces as ni

from netaddr import IPNetwork
import socket
from opena3xx.exceptions import OpenA3XXNetworkingException
from opena3xx.http import OpenA3xxHttpClient
from opena3xx.models import *


class OpenA3XXNetworkingClient:

    configuration: OpenA3XXConfigurationDto

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._configuration_client = OpenA3XXConfigurationClient()

    def start_api_discovery(self) -> None:
        self.configuration = self._configuration_client.get_configuration()
        try:
            interface = self.configuration.opena3xx_network_interface
            ip = self.__discover_local_ip_address(interface)
            if not self.configuration.opena3xx_peripheral_api_ip:
                self.__scan_network(ip)
            else:
                self.__ping_request_target(self.configuration.opena3xx_peripheral_api_ip,
                                           self.configuration.opena3xx_peripheral_api_port)
        except Exception as ex:
            raise OpenA3XXNetworkingException(ex)

    def __ping_request_target(self, target_ip: str, target_port: int) -> bool:
        try:
            scheme = self.configuration.opena3xx_peripheral_api_scheme
            http_client = OpenA3xxHttpClient()
            r = http_client.send_ping_request(scheme, target_ip, target_port)
            if r.status_code == 200:
                if r.text == "Pong from OpenA3XX":
                    self.logger.info("Received Valid Response from OpenA3XX API - Success")
                    return True
            else:
                self.logger.info("Invalid Response from OpenA3XX API")
            return False
        except Exception as ex:
            self.logger.critical(ex)
            return False

    def __scan_network(self, local_ip_address):
        self.logger.info("Started Scanning Network")
        cidr = self.configuration.opena3xx_network_scan_range_cidr
        opena3xx_api_port = self.configuration.opena3xx_peripheral_api_port
        cidr_range = f"{local_ip_address}/{cidr}"

        for ip in IPNetwork(cidr_range):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket.setdefaulttimeout(0.1)
            target_ip_address = socket.gethostbyname(str(ip))
            # returns an error indicator
            result = s.connect_ex((target_ip_address, int(opena3xx_api_port)))
            if result == 0:
                self.logger.info(f"Found something on IP: {target_ip_address} on Port: {opena3xx_api_port}")
                self.logger.info("Sending Ping to check if it is OpenA3XX API")
                if self.__ping_request_target(target_ip_address, opena3xx_api_port):
                    self.configuration.opena3xx_peripheral_api_ip = target_ip_address
                    configuration_client = OpenA3XXConfigurationClient()
                    configuration_client.update_configuration(self.configuration)
                    s.close()
                    return True
                else:
                    self.logger.warning(f"Continue scanning: Invalid Response from {target_ip_address}")
            s.close()
        return False

    def __discover_local_ip_address(self, interface: str) -> str:
        try:
            self.logger.info("Discovering Local IP Address")
            ip = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
            self.logger.info(f"Local IP Address is {ip}")
            return ip
        except Exception as ex:
            raise ex
