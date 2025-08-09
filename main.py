"""CLI entrypoint that orchestrates discovery, HTTP, AMQP, and hardware init.

Behavior:
- Discovers the Peripheral API, fetches board details and configuration
- Initializes RabbitMQ and the MCP23017-based hardware service
- Enters a keepalive loop and clears MCP interrupts periodically
- Restarts on failure; supports graceful shutdown via SIGINT/SIGTERM
"""

import os
import logging
import time
import signal
import threading
import click
from opena3xx.hardware.gpio_shim import GPIO
from art import *

from opena3xx.amqp import OpenA3XXMessagingService
from opena3xx.exceptions import OpenA3XXNetworkingException, OpenA3XXI2CRegistrationException, \
    OpenA3XXRabbitMqPublishingException
from opena3xx.hardware.opena3xx_mcp23017 import OpenA3XXHardwareService
from opena3xx.logging import log_init
from opena3xx.models import FAULT_LED, MESSAGING_LED, GENERAL_LED
from opena3xx.networking import OpenA3XXNetworkingClient
from opena3xx.http import OpenA3xxHttpClient
from opena3xx.models import INPUT_SWITCH, EXTENDER_CHIPS_RESET

log_init()
logger = logging.getLogger("main")
SHUTDOWN_EVENT = threading.Event()


def _install_signal_handlers():
    def _handler(signum, frame):
        logger.info(f"Signal received: {signum}. Initiating graceful shutdown...")
        SHUTDOWN_EVENT.set()

    try:
        signal.signal(signal.SIGINT, _handler)
        signal.signal(signal.SIGTERM, _handler)
    except Exception:
        pass


def screen_clear():
    """Clear the terminal screen in a cross-platform manner."""
    if os.name == 'posix':
        _ = os.system('clear')
    else:
        _ = os.system('cls')

def main(hardware_board_id: int):
    """Main controller routine for a single board id.

    Performs API discovery, configuration fetch, AMQP initialization, and
    hardware setup. On success, enters a keepalive loop until shutdown.
    """
    GPIO.cleanup()
    print("------------------------------------------------------------------------------------------------------")
    tprint("OPENA3XX")
    tprint("Hardware Controller", font="cybermedium")
    print("------------------------------------------------------------------------------------------------------")
    try:
        logger.info("OpenA3XX Hardware Controller: Application Started")
        networking_client = OpenA3XXNetworkingClient()
        scheme, api_host, api_port = networking_client.start_api_discovery()

        http_client = OpenA3xxHttpClient(scheme, api_host, api_port)
        board_details = http_client.get_hardware_board_details(hardware_board_id)

        if board_details is not None:
            rabbitmq_client = OpenA3XXMessagingService(http_client)
            rabbitmq_client.init_and_start()
            hardware_service = OpenA3XXHardwareService(rabbitmq_client, hardware_board_id)
            hardware_service.init_and_start(board_details)

            while not SHUTDOWN_EVENT.is_set():
                rabbitmq_client.keep_alive(hardware_board_id)

                for bus in hardware_service.extender_bus_details:
                    _bus_instance = bus["bus_instance"]
                    _bus_instance.clear_ints()

                if GPIO.input(INPUT_SWITCH) == GPIO.LOW:
                    GPIO.output(FAULT_LED, GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(FAULT_LED, GPIO.LOW)
                    raise
                time.sleep(2)

        else:
            logger.critical(f"Hardware Board with Id: {hardware_board_id} seems to be invalid. No Response for "
                            f"OpenA3XX Peripheral API")

    except OpenA3XXNetworkingException as ex:
        GPIO.output(FAULT_LED, GPIO.HIGH)
        logger.critical(f"Networking Exception occurred with message {ex}")
        raise
    except OpenA3XXI2CRegistrationException as ex:
        GPIO.output(FAULT_LED, GPIO.HIGH)
        logger.critical(f"MCP23017 registration failed with message {ex}. "
                        f"This is normally caused because the hardware board "
                        f"does not contain all the required extenders")
        raise
    except OpenA3XXRabbitMqPublishingException as ex:
        GPIO.output(FAULT_LED, GPIO.HIGH)
        logger.critical(f"Publishing Hardware Event to RabbitMQ Queue Failed: {ex}")
        raise
    except Exception as ex:
        GPIO.output(FAULT_LED, GPIO.HIGH)
        logger.critical(f"General Exception occurred with message {ex}")
        raise
    finally:
        try:
            GPIO.cleanup()
        except Exception:
            pass


@click.command()
@click.option('--hardware-board-id', 'hardware_board_id', help="Hardware Board Identifier")
def start(hardware_board_id: int):
    """CLI entrypoint that validates input and supervises the controller loop."""
    if hardware_board_id is None:
        logger.critical("Hardware Board Identifier Parameter is required to run the hardware controller. Check "
                        "--hardware-board-id option.")
        exit(-1)

    _install_signal_handlers()
    while not SHUTDOWN_EVENT.is_set():
        try:
            logger.info("OpenA3XX Hardware Controller Started")

            main(hardware_board_id)
        except Exception:
            logger.warning("Restarting OpenA3XX Hardware Controller in 5 seconds...")
            time.sleep(5)
            logger.warning("Restarting Now.")
        finally:
            if SHUTDOWN_EVENT.is_set():
                break


if __name__ == '__main__':
    screen_clear()
    start()
