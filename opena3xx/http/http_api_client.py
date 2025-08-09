import json
import logging
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from opena3xx.models.opena3xx_models import HardwareBoardDetailsDto


class OpenA3xxHttpClient:
    scheme: str
    base_url: str
    port: int

    def __init__(self, scheme: str, base_url: str, port: int):
        """Initialize an HTTP client bound to a discovered API endpoint.

        The client reuses a requests.Session with conservative retries for
        transient server/network errors and a consistent 10s timeout.
        """
        self.scheme = scheme
        self.base_url = base_url
        self.port = int(port)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=(502, 503, 504), allowed_methods=["GET"])  # type: ignore[arg-type]
        adapter = HTTPAdapter(max_retries=retries)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.headers.update({
            "User-Agent": "OpenA3XX-HardwareController/1.0",
            "Accept": "application/json",
        })

    def send_ping_request(self, scheme: str, target_ip: str, target_port: int) -> Response:
        """Send a ping request to the target API heartbeat endpoint.

        Returns the raw Response so the caller can inspect status and body.
        """
        endpoint = f'{scheme}://{target_ip}:{target_port}/core/heartbeat/ping'
        self.logger.info(f"Sending request to endpoint: {endpoint}")
        r = self._session.get(endpoint, timeout=10)
        # log_response(r)
        return r

    def get_configuration(self) -> Response:
        """Fetch platform configuration from the API (/configuration).

        Expected response: a flat JSON object with AMQP fields.
        Returns the JSON content (dict) when status is 200.
        """
        endpoint = f"{self.scheme}://{self.base_url}:{self.port}/configuration"
        self.logger.info(f"Sending request to endpoint: {endpoint}")
        r = self._session.get(endpoint, timeout=10)
        if r.status_code == 200:
            # log_response(r)
            return r.json()

    def get_hardware_board_details(self, hardware_board_id: int) -> HardwareBoardDetailsDto:
        """Retrieve board topology and construct a HardwareBoardDetailsDto."""
        endpoint = f"{self.scheme}://{self.base_url}:{self.port}/hardware-boards/{hardware_board_id}"
        self.logger.info(f"Sending request to endpoint: {endpoint}")
        r = self._session.get(endpoint, timeout=10)
        if r.status_code == 200:
            # log_response(r)
            data_dict = json.loads(r.content)
            hardware_board_details_dto = HardwareBoardDetailsDto.from_api(data_dict)
            return hardware_board_details_dto

    def __log_response(self, response):
        try:
            self.logger.info(f"Response: {json.dumps(response.json(), indent=4, sort_keys=True)}")
        except ValueError:
            self.logger.info(f"Response: {response.content}")
