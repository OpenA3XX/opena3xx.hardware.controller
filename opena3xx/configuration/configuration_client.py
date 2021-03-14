import json

from opena3xx.models import ConfigurationData

CONFIGURATION_FILE_PATH = "./configuration/configuration.json"


class ConfigurationClient:

    @staticmethod
    def get_configuration() -> ConfigurationData:
        configuration_file_path = CONFIGURATION_FILE_PATH
        with open(configuration_file_path, 'r') as file:
            general_configuration_data = ConfigurationData(
                **json.load(file))
        return general_configuration_data
