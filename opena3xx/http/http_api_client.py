import json
import logging
import requests
from requests import Session, Response

from opena3xx.configuration import ConfigurationClient
from opena3xx.models import *
from opena3xx.models.opena3xx_models import HardwareBoardDetailsDto


class OpenA3xxHttpClient:
    scheme: str
    base_url: str
    port: int

    def __init__(self):
        configuration_client = ConfigurationClient()
        configuration = configuration_client.get_configuration()
        self.scheme = configuration[OPENA3XX_API_SCHEME_CONFIGURATION_NAME]
        self.base_url = configuration[OPENA3XX_API_IP_ADDRESS_CONFIGURATION_NAME]
        self.port = int(configuration[OPENA3XX_API_PORT_CONFIGURATION_NAME])
        self.logger = logging.getLogger(self.__class__.__name__)

    def send_ping_request(self, scheme: str, target_ip: str, target_port: int) -> Response:
        endpoint = f'{scheme}://{target_ip}:{target_port}/core/heartbeat/ping'
        self.logger.info(f"Sending request to endpoint: {endpoint}")
        r = requests.get(endpoint, timeout=10)
        # log_response(r)
        return r

    def get_configuration(self) -> Response:
        endpoint = f"{self.scheme}://{self.base_url}:{self.port}/configuration"
        self.logger.info(f"Sending request to endpoint: {endpoint}")
        r = requests.get(endpoint, timeout=10)
        if r.status_code == 200:
            # log_response(r)
            return r.json()

    def get_hardware_board_details(self, hardware_board_id: int) -> HardwareBoardDetailsDto:
        endpoint = f"{self.scheme}://{self.base_url}:{self.port}/hardware-boards/{hardware_board_id}"
        self.logger.info(f"Sending request to endpoint: {endpoint}")
        r = requests.get(endpoint, timeout=10)
        if r.status_code == 200:
            # log_response(r)
            data_dict = json.loads(r.content)
            hardware_board_details_dto = HardwareBoardDetailsDto(int(data_dict["id"]),
                                                                 data_dict["name"],
                                                                 data_dict["ioExtenderBuses"])
            return hardware_board_details_dto

    def __log_response(self, response):
        try:
            self.logger.info(f"Response: {json.dumps(response.json(), indent=4, sort_keys=True)}")
        except ValueError:
            self.logger.info(f"Response: {response.content}")
