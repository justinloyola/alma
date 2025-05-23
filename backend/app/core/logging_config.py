import logging
import sys


class SimpleFormatter(logging.Formatter):
    """Simple formatter that outputs basic log information."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a simple string."""
        log_fmt = "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> None:
    """
    Configure basic console logging for the application.

    This function sets up a console handler with a simple formatter and configures
    the root logger and specific loggers for common libraries.
    """
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(SimpleFormatter())

    # Add handler to root logger
    root_logger.addHandler(console_handler)
    # Prevent the log messages from being propagated to the root logger
    # This prevents duplicate logs in some environments
    root_logger.propagate = False

    # Set up specific loggers
    loggers = ["uvicorn", "uvicorn.error", "fastapi"]
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = False
        logger.addHandler(console_handler)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration complete")


# Call setup_logging when this module is imported
setup_logging()
