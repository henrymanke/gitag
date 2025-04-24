import logging
import sys


def setup_logging(debug: bool = False):
    """Set up clean and aligned logging for CLI output."""
    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(fmt="%(levelname)-5s: %(message)s")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("gitag")
    root_logger.handlers = [handler]

    if debug:
        root_logger.setLevel(logging.DEBUG)
        root_logger.debug("🔧 Debug logging enabled.")
    else:
        root_logger.setLevel(logging.INFO)
