from datetime import datetime
import json
import logging

import pika
from RPi import GPIO
from pika.adapters.blocking_connection import BlockingChannel

from opena3xx.exceptions import OpenA3XXRabbitMqPublishingException
from opena3xx.http import OpenA3xxHttpClient
from opena3xx.models import FAULT_LED, MESSAGING_LED


class OpenA3XXMessagingService:
    data_channel: BlockingChannel
    keepalive_channel: BlockingChannel

    def __init__(self, http_client: OpenA3xxHttpClient):
        self.http_client = http_client
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Fetching remote configuration from API for AMQP setup")
        self.configuration_data = http_client.get_configuration()
        if not self.configuration_data or "configuration" not in self.configuration_data:
            self.logger.critical("Remote configuration missing or invalid; cannot initialize AMQP")
        self.rabbitmq_data_exchange = ""
        self.rabbitmq_keepalive_exchange = ""

    def init_and_start(self):
        try:
            self.logger.info("RabbitMQ Connection Init Start: Started")
            configuration = self.configuration_data["configuration"]

            username = configuration["opena3xx-amqp-username"]
            password = configuration["opena3xx-amqp-password"]
            host = configuration["opena3xx-amqp-host"]
            port = configuration["opena3xx-amqp-port"]
            vhost = configuration.get("opena3xx-amqp-vhost", "/")
            self.logger.info(f"AMQP parameters: host={host}, port={port}, vhost={vhost}, user={username}")
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(host, port, vhost, credentials)
            self.rabbitmq_data_exchange = "opena3xx.hardware_events.input_selectors"
            self.rabbitmq_keepalive_exchange = "opena3xx.hardware_boards.keep_alive"

            self.logger.info(f"Connecting to AMQP Server on host: "
                             f"{configuration['opena3xx-amqp-host']}:"
                             f"{configuration['opena3xx-amqp-port']}")
            self.logger.debug("Opening pika.BlockingConnection ...")
            amqp_connection = pika.BlockingConnection(parameters)
            self.logger.debug("AMQP connection established")
            self.data_channel = amqp_connection.channel()
            self.logger.debug("AMQP data channel created")
            #self.logger.info(f"Declaring Exchange: {self.rabbitmq_data_exchange}")
            #self.data_channel.exchange_declare(exchange=self.rabbitmq_data_exchange)

            self.keepalive_channel = amqp_connection.channel()
            self.logger.debug("AMQP keepalive channel created")

            self.logger.info("RabbitMQ Connection Init Start: Completed")
            #self.logger.info(f"Declaring Exchange: {self.rabbitmq_keepalive_exchange}")
            #self.keepalive_channel.exchange_declare(exchange=self.rabbitmq_keepalive_exchange)
            #GPIO.output(MESSAGING_LED, GPIO.LOW)

        except Exception as ex:
            self.logger.critical(f"AMQP initialization error: {ex}")
            raise ex

    def publish_hardware_event(self, hardware_board_id: int, extender_bus_bit_details: dict):
        try:
            if self.data_channel.is_closed:
                self.logger.critical("Data Channel is closed!")
                GPIO.output(MESSAGING_LED, GPIO.HIGH)
                self.init_and_start()
                GPIO.output(MESSAGING_LED, GPIO.LOW)

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
            self.logger.debug(f"Publishing hardware event to exchange '{self.rabbitmq_data_exchange}': {message}")
            self.data_channel.basic_publish(exchange=f"{self.rabbitmq_data_exchange}",
                                            routing_key="*",
                                            body=json.dumps(message))
            GPIO.output(FAULT_LED, GPIO.LOW)
        except Exception as ex:
            self.logger.critical(f"Hardware event publish failed: {ex}")
            raise OpenA3XXRabbitMqPublishingException(ex)

    def keep_alive(self, hardware_board_id: int):

        if self.keepalive_channel.is_closed:
            self.logger.critical("Keep Alive Channel is closed!")
            GPIO.output(MESSAGING_LED, GPIO.HIGH)
            self.init_and_start()
            GPIO.output(MESSAGING_LED, GPIO.LOW)

        try:
            message = {
                "timestamp": str(datetime.utcnow()),
                "hardware_board_id": hardware_board_id,
                "message": "Ping"
            }
            self.logger.debug(f"Publishing keepalive to exchange '{self.rabbitmq_keepalive_exchange}': {message}")
            self.keepalive_channel.basic_publish(exchange=self.rabbitmq_keepalive_exchange,
                                                 routing_key='*',
                                                 body=json.dumps(message))
            GPIO.output(FAULT_LED, GPIO.LOW)
        except Exception as ex:
            self.logger.critical(f"Keepalive publish failed: {ex}")
            raise OpenA3XXRabbitMqPublishingException(ex)
