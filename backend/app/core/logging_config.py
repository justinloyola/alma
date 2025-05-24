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
    Configure detailed console logging for the application.

    This function sets up console handlers with detailed formatters and configures
    the root logger and specific loggers for common libraries.
    """
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all logs

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create console handler for general logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    # Create a more detailed formatter
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(detailed_formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)
    root_logger.propagate = False

    # Configure SQLAlchemy logging
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.INFO)
    sqlalchemy_logger.handlers = [console_handler]
    sqlalchemy_logger.propagate = False

    # Configure database logger
    db_logger = logging.getLogger("app.db")
    db_logger.setLevel(logging.DEBUG)
    db_logger.handlers = [console_handler]
    db_logger.propagate = False

    # Set up specific loggers
    loggers = ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "app"]
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        logger.addHandler(console_handler)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration complete")


# Call setup_logging when this module is imported
setup_logging()
