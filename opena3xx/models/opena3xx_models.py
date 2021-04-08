class IOExtenderBitDto:
    def __init__(self, id: int, name: str, hardwareInputSelectorFullName: str, hardwareOutputSelectorFullName: str,
                 hardware_input_selector_id: int, hardware_output_selector_id: int):
        self.id = id
        self.name = name
        self.hardware_input_selector_id = hardware_input_selector_id
        self.hardware_input_selector_fullname = hardwareInputSelectorFullName
        self.hardware_output_selector_id = hardware_output_selector_id
        self.hardware_output_selector_fullname = hardwareOutputSelectorFullName


class IOExtenderBusDto:
    def __init__(self, id: int, name: str, ioExtenderBusBits: []):
        self.id = id
        self.name = name
        self.io_extender_bus_bits = []
        for extender_bus_bit in ioExtenderBusBits:
            self.io_extender_bus_bits.append(IOExtenderBitDto(int(extender_bus_bit["id"]),
                                                              extender_bus_bit["name"],
                                                              extender_bus_bit["hardwareInputSelectorFullName"],
                                                              extender_bus_bit["hardwareOutputSelectorFullName"],
                                                              extender_bus_bit["hardwareInputSelectorId"],
                                                              extender_bus_bit["hardwareOutputSelectorId"]))


class HardwareBoardDetailsDto:
    def __init__(self, id: int, name: str, ioExtenderBuses: []):
        self.id = id
        self.name = name
        self.io_extender_buses = []

        for extender_bus in ioExtenderBuses:
            self.io_extender_buses.append(IOExtenderBusDto(int(extender_bus["id"]),
                                                           extender_bus["name"],
                                                           extender_bus["ioExtenderBusBits"]))


class OpenA3XXConfigurationDto:
    def __init__(self, configuration_dict: []):
        self.opena3xx_network_interface = configuration_dict["opena3xx-network-interface"]
        self.opena3xx_network_scan_range_cidr = configuration_dict["opena3xx-network-interface"]
        self.opena3xx_peripheral_api_scheme = configuration_dict["opena3xx-peripheral-api-scheme"]
        self.opena3xx_peripheral_api_ip = configuration_dict["opena3xx-peripheral-api-ip"]
        self.opena3xx_peripheral_api_port = configuration_dict["opena3xx-peripheral-api-port"]
        self.opena3xx_peripheral_keepalive_seconds = configuration_dict["opena3xx-peripheral-keepalive-seconds"]
        self.opena3xx_amqp_host = configuration_dict["opena3xx-amqp-host"]
        self.opena3xx_amqp_username = configuration_dict["opena3xx-amqp-username"]
        self.opena3xx_amqp_password = configuration_dict["opena3xx-amqp-password"]




