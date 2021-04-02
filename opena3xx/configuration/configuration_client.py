import json
import logging

CONFIGURATION_FILE_PATH = "./configuration/configuration.json"


class ConfigurationClient:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_configuration(self) -> []:
        self.logger.info("Reading Config")
        with open(CONFIGURATION_FILE_PATH, 'r') as file:
            configuration_data = json.load(file)
        return configuration_data

    def update_configuration(self, configuration: []):
        self.logger.info("Updating Config")
        with open(CONFIGURATION_FILE_PATH, 'w') as outfile:
            json.dump(configuration, outfile, indent=4)
        return

