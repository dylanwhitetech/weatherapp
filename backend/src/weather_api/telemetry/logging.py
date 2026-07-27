import sys

from loguru import logger


def configure_logging(log_level: str) -> None:
    logger.remove()
    logger.add(sys.stdout, serialize=True, level=log_level.upper())
