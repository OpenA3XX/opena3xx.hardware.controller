from datetime import datetime
import json
import logging

import pika
from RPi import GPIO
from pika.adapters.blocking_connection import BlockingChannel

from opena3xx.exceptions import OpenA3XXRabbitMqPublishingException
from opena3xx.http import OpenA3xxHttpClient
from opena3xx.models import FAULT_LED


class OpenA3XXMessagingService:
    data_channel: BlockingChannel
    keepalive_channel: BlockingChannel

    def __init__(self):
        http_client = OpenA3xxHttpClient()
        self.configuration_data = http_client.get_configuration()
        self.rabbitmq_data_exchange = ""
        self.rabbitmq_keepalive_exchange = ""
        self.logger = logging.getLogger(self.__class__.__name__)

    def init_and_start(self):
        try:
            self.logger.info("RabbitMQ Connection Init Start: Started")
            configuration = self.configuration_data["configuration"]

            credentials = pika.PlainCredentials(configuration["opena3xx-amqp-username"],
                                                configuration["opena3xx-amqp-password"])
            parameters = pika.ConnectionParameters(configuration["opena3xx-amqp-host"],
                                                   configuration["opena3xx-amqp-port"],
                                                   configuration["opena3xx-amqp-vhost"],
                                                   credentials)
            self.rabbitmq_data_exchange = "opena3xx.hardware_events.input_selectors"
            self.rabbitmq_keepalive_exchange = "opena3xx.hardware_boards.keep_alive"

            self.logger.info(f"Connecting to AMQP Server on host: "
                             f"{configuration['opena3xx-amqp-host']}:"
                             f"{configuration['opena3xx-amqp-port']}")
            amqp_connection = pika.BlockingConnection(parameters)
            self.data_channel = amqp_connection.channel()
            #self.logger.info(f"Declaring Exchange: {self.rabbitmq_data_exchange}")
            #self.data_channel.exchange_declare(exchange=self.rabbitmq_data_exchange)

            self.keepalive_channel = amqp_connection.channel()

            self.logger.info("RabbitMQ Connection Init Start: Completed")
            #self.logger.info(f"Declaring Exchange: {self.rabbitmq_keepalive_exchange}")
            #self.keepalive_channel.exchange_declare(exchange=self.rabbitmq_keepalive_exchange)
        except Exception as ex:
            raise ex

    def publish_hardware_event(self, hardware_board_id: int, extender_bus_bit_details: dict):
        try:
            if self.data_channel.is_closed:
                self.logger.critical("Data Channel is closed!")
                self.init_and_start()

            message = {
                "hardware_board_id": hardware_board_id,
                "extender_bit_id": extender_bus_bit_details["extender_bit_id"],
                "extender_bit_name": extender_bus_bit_details["extender_bit_name"],
                "extender_bus_id": extender_bus_bit_details["extender_bus_id"],
                "extender_bus_name": extender_bus_bit_details["extender_bus_name"],
                "input_selector_name": extender_bus_bit_details["input_selector_name"],
                "input_selector_id": extender_bus_bit_details["input_selector_id"],
                "timestamp": str(datetime.utcnow())
            }
            self.data_channel.basic_publish(exchange=f"{self.rabbitmq_data_exchange}",
                                            routing_key="*",
                                            body=json.dumps(message))
            GPIO.output(FAULT_LED, GPIO.LOW)
        except Exception as ex:
            raise OpenA3XXRabbitMqPublishingException(ex)

    def keep_alive(self, hardware_board_id: int):

        if self.keepalive_channel.is_closed:
            self.logger.critical("Keep Alive Channel is closed!")
            self.init_and_start()
        try:
            message = {
                "timestamp": str(datetime.utcnow()),
                "hardware_board_id": hardware_board_id,
                "message": "Ping"
            }
            self.keepalive_channel.basic_publish(exchange=self.rabbitmq_keepalive_exchange,
                                                 routing_key='*',
                                                 body=json.dumps(message))
            GPIO.output(FAULT_LED, GPIO.LOW)
        except Exception as ex:
            raise OpenA3XXRabbitMqPublishingException(ex)
