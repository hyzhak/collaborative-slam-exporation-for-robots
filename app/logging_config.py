import os
import logging
import logging.config

def setup_logging(default_level="DEBUG"):
    """
    Set up logging configuration for the application.
    Uses LOG_LEVEL env variable if set, otherwise defaults to DEBUG.
    """
    log_level = os.getenv("LOG_LEVEL", default_level).upper()
    logging.config.dictConfig({
        "version": 1,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s %(levelname)s %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "level": log_level
            }
        },
        "root": {
            "handlers": ["console"],
            "level": log_level
        }
    })
