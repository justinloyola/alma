import logging
import sys
from typing import Dict, Any

class SimpleFormatter(logging.Formatter):
    """Simple formatter that outputs basic log information."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a simple string."""
        log_fmt = "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logging():
    """Configure basic console logging for the application."""
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
    
    # Configure SQLAlchemy logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Configure Uvicorn logging
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').disabled = True
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration complete")

# Call setup_logging when this module is imported
setup_logging()
