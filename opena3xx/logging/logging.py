import json
import logging

import coloredlogs
import seqlog


def log_init():
    logger = logging.getLogger("default")
    coloredlogs.install(level='verbose', logger=logger)
    seqlog.log_to_seq(
        server_url="http://192.168.50.22:8080/",
        api_key="OfJYXzzdvCGgCWbHpoek",
        level=logging.DEBUG,
        batch_size=10,
        auto_flush_timeout=1,  # seconds
        override_root_logger=False,
        json_encoder_class=json.encoder.JSONEncoder
        # Optional; only specify this if you want to use a custom JSON encoder
    )
