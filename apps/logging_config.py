import logging
from rich.logging import RichHandler

LOG_FILENAME = "apps/main.log"

def setup_logging(name="flask-app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler(LOG_FILENAME)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler with color (using rich)
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setLevel(logging.INFO)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
