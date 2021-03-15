import json
import logging
import requests
from requests import Session, Response

from opena3xx.configuration import ConfigurationClient
from opena3xx.models import *

logger = logging.getLogger("default")


def log_response(response):
    try:
        logger.debug(f"Response: {json.dumps(response.json(), indent=4, sort_keys=True)}")
    except ValueError:
        logger.debug(f"Response: {response.content}")


class OpenA3xxHttpClient:
    scheme: str
    base_url: str
    port: int

    def __init__(self):
        configuration = ConfigurationClient.get_configuration()
        self.scheme = configuration[OPENA3XX_API_SCHEME_CONFIGURATION_NAME]
        self.base_url = configuration[OPENA3XX_API_IP_ADDRESS_CONFIGURATION_NAME]
        self.port = int(configuration[OPENA3XX_API_PORT_CONFIGURATION_NAME])

    def send_ping_request(self, scheme: str, target_ip: str, target_port: int) -> Session:
        endpoint = f'{scheme}://{target_ip}:{target_port}/core/heartbeat/ping'
        logger.info(f"Sending request to endpoint: {endpoint}")
        r = requests.get(endpoint, timeout=10)
        log_response(r)
        return r

    def get_configuration(self) -> Response:
        endpoint = f"{self.scheme}://{self.base_url}:{self.port}/configuration"
        logger.info(f"Sending request to endpoint: {endpoint}")
        r = requests.get(endpoint, timeout=10)
        if r.status_code == 200:
            log_response(r)
            return r.json()

