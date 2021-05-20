import json
import logging

import pathlib

from opena3xx.models import OpenA3XXConfigurationDto

CONFIGURATION_FILE_PATH = f"{pathlib.Path().absolute()}/configuration/configuration.json"


class OpenA3XXConfigurationClient:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_configuration(self) -> OpenA3XXConfigurationDto:
        self.logger.info(f"Reading Config from {CONFIGURATION_FILE_PATH}")
        with open(CONFIGURATION_FILE_PATH, 'r') as file:
            configuration_data = json.load(file)
        configuration_dto = OpenA3XXConfigurationDto(configuration_data)

        return configuration_dto

    def update_configuration(self, configuration: OpenA3XXConfigurationDto):
        self.logger.info("Updating Config")
        with open(CONFIGURATION_FILE_PATH, 'w') as outfile:
            json.dump(configuration, outfile, indent=4)
        return
