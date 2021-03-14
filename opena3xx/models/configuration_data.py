class ConfigurationData(object):
    def __init__(
            self, networking, api, amqp
    ):
        self.networking = networking
        self.api = api
        self.amqp = amqp