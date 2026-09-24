import json
import logging.config

import pytest
import yaml

from clinical_mdr_api.tests.telemetry.config import LOG_CONFIG, if_logging_configured


@if_logging_configured
@pytest.mark.forked  # Without this marker, it would break Pytest
def test_logging_config():
    """
    Tests that the logging configuration is valid by parsing the config file and passing it to logging.config

    Should it emit any log message, the Pytest would break by not exiting.
    """
    configure_logging(LOG_CONFIG)
    log = logging.getLogger("test_logging_config")
    log.info("testing")


def configure_logging(log_config):
    if log_config.endswith(".json"):
        with open(log_config, encoding="UTF-8") as file:
            loaded_config = json.load(file)
            logging.config.dictConfig(loaded_config)
    elif log_config.endswith((".yaml", ".yml")):
        with open(log_config, encoding="UTF-8") as file:
            loaded_config = yaml.safe_load(file)
            logging.config.dictConfig(loaded_config)
    else:
        logging.config.fileConfig(log_config, disable_existing_loggers=False)
