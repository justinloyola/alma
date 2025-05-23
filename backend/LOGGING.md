# Logging in Alma Backend

This document describes the logging implementation in the Alma backend application.

## Overview

The backend uses Python's built-in `logging` module with the following features:

- **Structured Logging**: Logs are formatted consistently with timestamps, log levels, and source information.
- **Multiple Handlers**: Logs are sent to both console and files.
- **Log Rotation**: Log files are rotated when they reach 10MB, with up to 5 backup files kept.
- **Separate Log Files**: 
  - `logs/app.log`: All application logs (DEBUG and above)
  - `logs/error.log`: Only ERROR level and above
- **Request Logging**: All HTTP requests and responses are logged with their status codes.

## Log Levels

- **DEBUG**: Detailed information, typically of interest only when diagnosing problems.
- **INFO**: Confirmation that things are working as expected.
- **WARNING**: An indication that something unexpected happened, but the application is still working.
- **ERROR**: Due to a more serious problem, the software has not been able to perform some function.
- **CRITICAL**: A serious error, indicating that the program itself may be unable to continue running.

## Usage in Code

### Basic Logging

```python
import logging

# Get a logger for your module
logger = logging.getLogger(__name__)

# Log messages at different levels
logger.debug("Detailed debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error message")
```

### Logging Exceptions

Use `exc_info=True` to include stack traces:

```python
try:
    # Some code that might raise an exception
    result = 1 / 0
except Exception as e:
    logger.error("An error occurred: %s", str(e), exc_info=True)
```

### Logging Context

Include additional context in log messages:

```python
user_id = 123
action = "file_upload"
logger.info("User %s performed %s", user_id, action, extra={"user_id": user_id, "action": action})
```

## Viewing Logs

### Console

By default, INFO level and above logs are shown in the console when running the application.

### Log Files

- Application logs: `logs/app.log`
- Error logs: `logs/error.log`

### Log Rotation

Log files are rotated when they reach 10MB, keeping up to 5 backup files with numeric extensions (e.g., `app.log.1`, `app.log.2`, etc.).

## Configuration

Logging is configured in `app/core/logging_config.py`. You can modify:

- Log levels
- Log formats
- File paths and rotation settings
- Which loggers to configure

## Best Practices

1. Use appropriate log levels (DEBUG for development, INFO for normal operation).
2. Include relevant context in log messages.
3. Use `exc_info=True` when logging exceptions.
4. Be mindful of logging sensitive information.
5. Use structured logging for better searchability.

## Troubleshooting

### No Logs Appearing

- Ensure the `logs` directory exists and is writable.
- Check that the log level is set appropriately.
- Verify that the application has write permissions to the log directory.

### Log File Permissions

If you encounter permission issues, ensure the application has write access to the `logs` directory:

```bash
chmod -R 755 logs/
```

### Log Rotation Issues

If log rotation isn't working as expected:
- Check that the application has write permissions for the log files.
- Verify that the log files aren't being held open by another process.
- Check available disk space.
