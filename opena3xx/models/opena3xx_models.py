class IOExtenderBitDto:
    def __init__(self, id: int, name: str, hardwareInputSelectorFullName: str, hardwareOutputSelectorFullName: str):
        self.id = id
        self.name = name
        self.hardware_input_selector_fullname = hardwareInputSelectorFullName
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
                                                              extender_bus_bit["hardwareOutputSelectorFullName"]))


class HardwareBoardDetailsDto:
    def __init__(self, id: int, name: str, ioExtenderBuses: []):
        self.id = id
        self.name = name
        self.io_extender_buses = []

        for extender_bus in ioExtenderBuses:
            self.io_extender_buses.append(IOExtenderBusDto(int(extender_bus["id"]),
                                                           extender_bus["name"],
                                                           extender_bus["ioExtenderBusBits"]))
