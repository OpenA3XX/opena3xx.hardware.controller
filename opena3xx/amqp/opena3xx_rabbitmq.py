from datetime import datetime
import json
import logging

import pika
from pika.adapters.blocking_connection import BlockingChannel

from opena3xx.exceptions import OpenA3XXRabbitMqPublishingException
from opena3xx.http import OpenA3xxHttpClient


class OpenA3XXMessagingService:
    data_channel: BlockingChannel
    keepalive_channel: BlockingChannel

    def __init__(self):
        http_client = OpenA3xxHttpClient()
        self.configuration_data = http_client.get_configuration()
        self.rabbitmq_data_queue = ""
        self.rabbitmq_keepalive_queue = ""
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
            self.rabbitmq_data_queue = configuration["opena3xx-amqp-hardware-input-selector-events-queue-name"]
            self.rabbitmq_keepalive_queue = configuration["opena3xx-amqp-keepalive-queue-name"]

            self.logger.info(f"Connecting to AMQP Server on host: "
                             f"{configuration['opena3xx-amqp-host']}:"
                             f"{configuration['opena3xx-amqp-port']}")
            amqp_connection = pika.BlockingConnection(parameters)
            self.data_channel = amqp_connection.channel()
            self.logger.info(f"Declaring Queue: {self.rabbitmq_data_queue}")
            self.data_channel.queue_declare(queue=self.rabbitmq_data_queue)

            self.keepalive_channel = amqp_connection.channel()
            self.logger.info(f"Declaring Queue: {self.rabbitmq_keepalive_queue}")
            self.keepalive_channel.queue_declare(queue=self.rabbitmq_keepalive_queue)
        except Exception as ex:
            raise ex

    def publish_hardware_event(self, hardware_board_id: int, extender_bus_bit_details: dict):
        try:
            message = {
                "hardware_board_id": hardware_board_id,
                "extender_bit_id": extender_bus_bit_details["extender_bit_id"],
                "extender_bit_name": extender_bus_bit_details["extender_bit_name"],
                "extender_bus_id": extender_bus_bit_details["extender_bus_id"],
                "extender_bus_name": extender_bus_bit_details["extender_bus_name"],
                "input_selector_name": extender_bus_bit_details["input_selector_name"],
                "timestamp": str(datetime.utcnow())
            }
            self.keepalive_channel.basic_publish(exchange='',
                                                 routing_key=self.rabbitmq_data_queue,
                                                 body=json.dumps(message))
        except Exception as ex:
            raise OpenA3XXRabbitMqPublishingException(ex)

    def keep_alive(self, hardware_board_id: int):
        try:
            message = {
                "timestamp": str(datetime.utcnow()),
                "hardware_board_id": hardware_board_id,
                "message": "Ping"
            }
            self.keepalive_channel.basic_publish(exchange='',
                                                 routing_key=self.rabbitmq_keepalive_queue,
                                                 body=json.dumps(message))
        except Exception as ex:
            raise OpenA3XXRabbitMqPublishingException(ex)
