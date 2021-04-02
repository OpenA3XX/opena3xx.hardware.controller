import json
import logging

import pika
from pika.adapters.blocking_connection import BlockingChannel

from opena3xx.http import OpenA3xxHttpClient


class OpenA3XXMessagingService:
    channel: BlockingChannel

    def __init__(self):
        http_client = OpenA3xxHttpClient()
        self.configuration_data = http_client.get_configuration()
        self.rabbitmq_queue = "hardware_events"
        self.logger = logging.getLogger(self.__class__.__name__)

    def init_and_start(self):
        try:
            configuration = self.configuration_data["configuration"]

            credentials = pika.PlainCredentials(configuration["opena3xx-amqp-username"],
                                                configuration["opena3xx-amqp-password"])
            parameters = pika.ConnectionParameters(configuration["opena3xx-amqp-host"],
                                                   configuration["opena3xx-amqp-port"],
                                                   configuration["opena3xx-amqp-vhost"],
                                                   credentials)
            self.logger.info(f"Connecting to AMQP Server on host: "
                             f"{configuration['opena3xx-amqp-host']}:"
                             f"{configuration['opena3xx-amqp-port']}")
            amqp_connection = pika.BlockingConnection(parameters)
            self.channel = amqp_connection.channel()
            self.logger.info(f"Declaring Queue: {self.rabbitmq_queue}")
            self.channel.queue_declare(queue=self.rabbitmq_queue)
        except Exception as ex:
            raise ex

    @staticmethod
    def __generate_message(message: str):
        message = {
            "hardware_board_id": 1,
            "message": message
        }
        return message

    def send_message(self, message):
        self.channel.basic_publish(exchange='',
                                   routing_key=self.rabbitmq_queue,
                                   body=json.dumps(self.__generate_message(message)))

    def keep_alive(self):
        self.send_message("I am alive")