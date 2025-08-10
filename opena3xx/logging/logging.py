import coloredlogs
import logging


def log_init():
    coloredlogs.install(level='info')
    # Reduce noisy third-party logs (pika may log stack traces on reconnects)
    logging.getLogger("pika").setLevel(logging.WARNING)

