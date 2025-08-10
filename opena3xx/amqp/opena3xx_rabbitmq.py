import datetime as dt
import os
from pathlib import Path
import uuid
import json
import logging
import threading
import time
from queue import Queue, Empty

import pika
from opena3xx.hardware.gpio_shim import GPIO
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
        # API returns a flat JSON object (no top-level 'configuration')
        required_keys = [
            "opena3xx-amqp-host",
            "opena3xx-amqp-port",
            "opena3xx-amqp-username",
            "opena3xx-amqp-password",
        ]
        if not isinstance(self.configuration_data, dict) or not all(k in self.configuration_data for k in required_keys):
            self.logger.critical("Remote configuration missing required AMQP keys; cannot initialize AMQP")
        # Async publishing support
        self._event_queue: Queue = Queue(maxsize=10000)
        self._publisher_thread: threading.Thread | None = None
        self._stop_publisher = threading.Event()
        self._data_connection: pika.BlockingConnection | None = None
        self._keepalive_connection: pika.BlockingConnection | None = None
        # Disk spool for durable event storage
        spool_dir = os.getenv("OPENA3XX_EVENT_SPOOL_DIR", "/tmp/opena3xx_event_spool")
        self._spool_path = Path(spool_dir)
        try:
            self._spool_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback to /tmp if provided path not writable
            self._spool_path = Path("/tmp/opena3xx_event_spool")
            self._spool_path.mkdir(parents=True, exist_ok=True)

    def init_and_start(self):
        """Initialize RabbitMQ connection and channels, declare exchanges.

        Uses parameters fetched from the API configuration. Exchanges are
        declared idempotently, and delivery confirms are enabled when possible.
        """
        try:
            self.logger.info("RabbitMQ Connection Init Start: Started")
            configuration = self.configuration_data

            username = configuration["opena3xx-amqp-username"]
            password = configuration["opena3xx-amqp-password"]
            host = configuration["opena3xx-amqp-host"]
            port = int(configuration["opena3xx-amqp-port"])
            vhost = configuration.get("opena3xx-amqp-vhost", "/")
            self.logger.info(f"AMQP parameters: host={host}, port={port}, vhost={vhost}")
            # Avoid logging credentials
            credentials = pika.PlainCredentials(username, password)
            parameters = pika.ConnectionParameters(
                host=host,
                port=port,
                virtual_host=vhost,
                credentials=credentials,
                heartbeat=30,
                blocked_connection_timeout=10,
                connection_attempts=5,
                retry_delay=2.0,
                socket_timeout=10,
            )
            self.rabbitmq_data_exchange = "opena3xx.hardware_events.input_selectors"
            self.rabbitmq_keepalive_exchange = "opena3xx.hardware_boards.keep_alive"

            self.logger.info(f"Connecting to AMQP Server on host: "
                             f"{configuration['opena3xx-amqp-host']}:"
                             f"{configuration['opena3xx-amqp-port']}")
            # Create a dedicated connection for data publishing (publisher thread)
            self.logger.debug("Opening data BlockingConnection ...")
            self._data_connection = pika.BlockingConnection(parameters)
            self.logger.debug("AMQP data connection established")
            self.data_channel = self._data_connection.channel()
            self.logger.debug("AMQP data channel created")
            self.logger.info(f"Declaring Exchange: {self.rabbitmq_data_exchange}")
            try:
                self.data_channel.exchange_declare(exchange=self.rabbitmq_data_exchange, exchange_type='fanout', durable=True)
            except Exception as ex:
                self.logger.warning(f"Exchange declare warning (data): {ex}")
            try:
                self.data_channel.confirm_delivery()
            except Exception:
                pass

            # Create a separate connection for keepalive publishing (main thread)
            self.logger.debug("Opening keepalive BlockingConnection ...")
            self._keepalive_connection = pika.BlockingConnection(parameters)
            self.logger.debug("AMQP keepalive connection established")
            self.keepalive_channel = self._keepalive_connection.channel()
            self.logger.debug("AMQP keepalive channel created")

            self.logger.info("RabbitMQ Connection Init Start: Completed")
            self.logger.info(f"Declaring Exchange: {self.rabbitmq_keepalive_exchange}")
            try:
                self.keepalive_channel.exchange_declare(exchange=self.rabbitmq_keepalive_exchange, exchange_type='fanout', durable=True)
            except Exception as ex:
                self.logger.warning(f"Exchange declare warning (keepalive): {ex}")
            #GPIO.output(MESSAGING_LED, GPIO.LOW)

            # Start publisher thread once
            if self._publisher_thread is None or not self._publisher_thread.is_alive():
                self._stop_publisher.clear()
                self._publisher_thread = threading.Thread(target=self._publisher_loop, name="amqp-publisher", daemon=True)
                self._publisher_thread.start()

        except Exception as ex:
            self.logger.critical(f"AMQP initialization error: {ex}")
            raise ex

    def publish_hardware_event(self, hardware_board_id: int, extender_bus_bit_details: dict):
        """Persist an event to disk spool and signal the publisher thread.

        Returns immediately from interrupt callbacks. The publisher thread
        reads spooled events and publishes in FIFO order, surviving restarts.
        """
        message = {
            "hardware_board_id": hardware_board_id,
            "extender_bit_id": extender_bus_bit_details["extender_bit_id"],
            "extender_bit_name": extender_bus_bit_details["extender_bit_name"],
            "extender_bus_id": extender_bus_bit_details["extender_bus_id"],
            "extender_bus_name": extender_bus_bit_details["extender_bus_name"],
            "input_selector_name": extender_bus_bit_details["input_selector_name"],
            "input_selector_id": extender_bus_bit_details["input_selector_id"],
            "pressed": bool(extender_bus_bit_details.get("pressed", False)),
            "timestamp": str(dt.datetime.now(dt.UTC)),
        }
        try:
            self._spool_write_message(message)
            # Non-blocking signal to wake publisher
            try:
                self._event_queue.put_nowait(None)
            except Exception:
                pass
        except Exception as ex:
            GPIO.output(FAULT_LED, GPIO.HIGH)
            self.logger.critical(f"Failed to spool hardware event: {ex}")

    def keep_alive(self, hardware_board_id: int):
        """Publish periodic keepalive messages to the keepalive exchange."""
        try:
            if self.keepalive_channel.is_closed:
                self.logger.warning("Keepalive channel closed; reconnecting")
                self._connect_keepalive_channel()
        except Exception:
            self.logger.warning("Keepalive channel invalid; reconnecting")
            self._connect_keepalive_channel()

        try:
            message = {
                "timestamp": str(dt.datetime.now(dt.UTC)),
                "hardware_board_id": hardware_board_id,
                "message": "Ping"
            }
            # timestamp already timezone-aware (UTC)
            self.logger.debug(f"Publishing keepalive to exchange '{self.rabbitmq_keepalive_exchange}': {message}")
            GPIO.output(MESSAGING_LED, GPIO.HIGH)
            self.keepalive_channel.basic_publish(exchange=self.rabbitmq_keepalive_exchange,
                                                 routing_key='*',
                                                 body=json.dumps(message))
            GPIO.output(MESSAGING_LED, GPIO.LOW)
            GPIO.output(FAULT_LED, GPIO.LOW)
        except Exception as ex:
            self.logger.critical(f"Keepalive publish failed: {ex}")
            raise OpenA3XXRabbitMqPublishingException(ex)

    # ----- Internal helpers -----
    def _connect_data_channel(self):
        configuration = self.configuration_data
        username = configuration["opena3xx-amqp-username"]
        password = configuration["opena3xx-amqp-password"]
        host = configuration["opena3xx-amqp-host"]
        port = int(configuration["opena3xx-amqp-port"])
        vhost = configuration.get("opena3xx-amqp-vhost", "/")
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=vhost,
            credentials=credentials,
            heartbeat=30,
            blocked_connection_timeout=10,
            connection_attempts=5,
            retry_delay=2.0,
            socket_timeout=10,
        )
        try:
            if self._data_connection is not None:
                try:
                    self._data_connection.close()
                except Exception:
                    pass
            self._data_connection = pika.BlockingConnection(parameters)
            self.data_channel = self._data_connection.channel()
            self.data_channel.exchange_declare(exchange=self.rabbitmq_data_exchange, exchange_type='fanout', durable=True)
            try:
                self.data_channel.confirm_delivery()
            except Exception:
                pass
        except Exception as ex:
            self.logger.critical(f"Reconnecting data channel failed: {ex}")
            raise

    def _connect_keepalive_channel(self):
        configuration = self.configuration_data
        username = configuration["opena3xx-amqp-username"]
        password = configuration["opena3xx-amqp-password"]
        host = configuration["opena3xx-amqp-host"]
        port = int(configuration["opena3xx-amqp-port"])
        vhost = configuration.get("opena3xx-amqp-vhost", "/")
        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=vhost,
            credentials=credentials,
            heartbeat=30,
            blocked_connection_timeout=10,
            connection_attempts=5,
            retry_delay=2.0,
            socket_timeout=10,
        )
        try:
            if self._keepalive_connection is not None:
                try:
                    self._keepalive_connection.close()
                except Exception:
                    pass
            self._keepalive_connection = pika.BlockingConnection(parameters)
            self.keepalive_channel = self._keepalive_connection.channel()
            self.keepalive_channel.exchange_declare(exchange=self.rabbitmq_keepalive_exchange, exchange_type='fanout', durable=True)
        except Exception as ex:
            self.logger.critical(f"Reconnecting keepalive channel failed: {ex}")
            raise

    def _publisher_loop(self):
        while not self._stop_publisher.is_set():
            # Process any spooled files first (FIFO by filename)
            files = self._spool_list_paths()
            if not files:
                # Wait for a wake signal, then loop
                try:
                    self._event_queue.get(timeout=0.5)
                    try:
                        self._event_queue.task_done()
                    except Exception:
                        pass
                except Empty:
                    pass
                continue

            path = files[0]
            try:
                message = self._spool_read(path)
            except Exception as ex:
                self.logger.warning(f"Failed reading spooled event {path.name}: {ex}; deleting file")
                try:
                    self._spool_delete(path)
                except Exception:
                    pass
                continue

            # Try to publish with backoff and reconnect
            published = False
            backoff = 0.5
            for attempt in range(5):
                try:
                    if getattr(self, 'data_channel', None) is None or self.data_channel.is_closed:
                        self.logger.warning("Data channel not open; reconnecting")
                        self._connect_data_channel()
                    self.data_channel.basic_publish(
                        exchange=self.rabbitmq_data_exchange,
                        routing_key="*",
                        body=json.dumps(message),
                    )
                    GPIO.output(FAULT_LED, GPIO.LOW)
                    published = True
                    break
                except Exception as ex:
                    self.logger.warning(f"Publish attempt {attempt + 1} failed: {ex}")
                    try:
                        if self._data_connection is not None:
                            self._data_connection.close()
                    except Exception:
                        pass
                    time.sleep(backoff)
                    backoff = min(5.0, backoff * 2)

            if published:
                try:
                    self._spool_delete(path)
                except Exception as ex:
                    self.logger.warning(f"Published but failed to delete spool file {path.name}: {ex}")
            else:
                GPIO.output(FAULT_LED, GPIO.HIGH)
                self.logger.warning(f"Will retry later for spooled event {path.name}")

    # ----- Spool helpers -----
    def _spool_write_message(self, message: dict) -> None:
        ts_ms = int(time.time() * 1000)
        name = f"{ts_ms:013d}_{uuid.uuid4().hex}.json"
        tmp = self._spool_path / (name + ".tmp")
        final = self._spool_path / name
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps(message, separators=(",", ":")))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final)

    def _spool_list_paths(self) -> list[Path]:
        try:
            files = [p for p in self._spool_path.iterdir() if p.is_file() and p.suffix == ".json"]
            return sorted(files, key=lambda p: p.name)
        except Exception:
            return []

    def _spool_read(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.read())

    def _spool_delete(self, path: Path) -> None:
        try:
            path.unlink(missing_ok=True)  # type: ignore[call-arg]
        except TypeError:
            # Python <3.8 compatibility
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass
