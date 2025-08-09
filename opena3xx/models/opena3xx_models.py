from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class IOExtenderBitDto:
    id: int
    name: str
    hardware_input_selector_fullname: str
    hardware_output_selector_fullname: str
    hardware_input_selector_id: int
    hardware_output_selector_id: int

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "IOExtenderBitDto":
        return cls(
            id=int(data["id"]),
            name=data["name"],
            hardware_input_selector_fullname=data["hardwareInputSelectorFullName"],
            hardware_output_selector_fullname=data["hardwareOutputSelectorFullName"],
            hardware_input_selector_id=data["hardwareInputSelectorId"],
            hardware_output_selector_id=data["hardwareOutputSelectorId"],
        )


@dataclass
class IOExtenderBusDto:
    id: int
    name: str
    io_extender_bus_bits: List[IOExtenderBitDto] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "IOExtenderBusDto":
        bits = [IOExtenderBitDto.from_api(b) for b in data["ioExtenderBusBits"]]
        return cls(id=int(data["id"]), name=data["name"], io_extender_bus_bits=bits)


@dataclass
class HardwareBoardDetailsDto:
    id: int
    name: str
    io_extender_buses: List[IOExtenderBusDto] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "HardwareBoardDetailsDto":
        buses = [IOExtenderBusDto.from_api(b) for b in data["ioExtenderBuses"]]
        return cls(id=int(data["id"]), name=data["name"], io_extender_buses=buses)


@dataclass
class OpenA3XXConfigurationDto:
    opena3xx_network_interface: str
    opena3xx_network_scan_range_cidr: str
    opena3xx_peripheral_api_scheme: str
    opena3xx_peripheral_api_ip: str
    opena3xx_peripheral_api_port: str
    opena3xx_peripheral_keepalive_seconds: str
    opena3xx_amqp_host: str
    opena3xx_amqp_username: str
    opena3xx_amqp_password: str

    @classmethod
    def from_api(cls, configuration_dict: Dict[str, Any]) -> "OpenA3XXConfigurationDto":
        return cls(
            opena3xx_network_interface=configuration_dict["opena3xx-network-interface"],
            opena3xx_network_scan_range_cidr=configuration_dict["opena3xx-network-interface"],
            opena3xx_peripheral_api_scheme=configuration_dict["opena3xx-peripheral-api-scheme"],
            opena3xx_peripheral_api_ip=configuration_dict["opena3xx-peripheral-api-ip"],
            opena3xx_peripheral_api_port=configuration_dict["opena3xx-peripheral-api-port"],
            opena3xx_peripheral_keepalive_seconds=configuration_dict["opena3xx-peripheral-keepalive-seconds"],
            opena3xx_amqp_host=configuration_dict["opena3xx-amqp-host"],
            opena3xx_amqp_username=configuration_dict["opena3xx-amqp-username"],
            opena3xx_amqp_password=configuration_dict["opena3xx-amqp-password"],
        )




