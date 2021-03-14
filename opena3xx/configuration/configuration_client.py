import json
import logging

logger = logging.getLogger("default")

CONFIGURATION_FILE_PATH = "./configuration/configuration.json"


class ConfigurationClient:

    @staticmethod
    def get_configuration() -> []:
        logger.info("Reading Config")
        with open(CONFIGURATION_FILE_PATH, 'r') as file:
            configuration_data = json.load(file)
        return configuration_data

    @staticmethod
    def update_configuration(configuration: []):
        logger.info("Updating Config")
        with open(CONFIGURATION_FILE_PATH, 'w') as outfile:
            json.dump(configuration, outfile, indent=4)
        return

