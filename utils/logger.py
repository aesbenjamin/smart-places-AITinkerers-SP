# utils/logger.py
"""
Provides a configured logger instance for consistent logging across the application.

This module ensures that all parts of the application can easily obtain a
logger that outputs messages in a standardized format to the console.
It supports basic configuration for log level and format.
"""

import logging
import sys

# --- Configuration ---
LOG_LEVEL = logging.INFO  # Default log level for all loggers obtained from this module.
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' # Standard log message format.
DATE_FORMAT = '%Y-%m-%d %H:%M:%S' # Date format for log messages.

# Keep track of configured loggers to avoid adding multiple handlers to the same logger.
_configured_loggers = {}

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a configured logger instance.

    If a logger with the given name has already been configured by this function,
    it returns the existing instance. Otherwise, it creates and configures a new
    logger. The configuration includes setting the log level, creating a
    StreamHandler to output logs to stdout, and applying a standard formatter.

    Args:
        name (str): The name for the logger. This is typically the `__name__`
                    attribute of the calling module, which helps in identifying
                    the source of log messages.

    Returns:
        logging.Logger: The configured logger instance.
    """
    if name in _configured_loggers:
        return _configured_loggers[name]

    # Create a new logger or get the existing one if already created by logging module
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Ensure handlers are not added multiple times if get_logger is called again for an already existing logger
    # (e.g. if some other part of the code or a library configured it, though _configured_loggers handles our own calls).
    if not logger.handlers:
        # Create a handler (StreamHandler to output to console)
        # All logs (INFO, WARNING, ERROR etc.) will go to sys.stdout with this single handler.
        # For more advanced scenarios, different handlers could be used for different levels (e.g., stderr for errors).
        handler = logging.StreamHandler(sys.stdout)
        # The handler's level also needs to be set, otherwise it might default to WARNING or higher.
        handler.setLevel(LOG_LEVEL)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

    # Store our configured logger instance in the cache.
    _configured_loggers[name] = logger

    # Optional: Prevent log propagation to the root logger.
    # This can be useful if you want to avoid duplicate logging in environments where the
    # root logger is also configured with a handler (e.g. some cloud logging setups).
    # For most simple console applications, default propagation (True) is fine.
    # logger.propagate = False

    return logger

if __name__ == '__main__':
    # This block demonstrates example usage of the get_logger function.
    # It's intended for testing the logger setup itself.
    logger_test_main = get_logger(__name__) # Logger for this __main__ block
    logger_test_main.info("This is an info message from logger_test_main.")
    logger_test_main.warning("This is a warning message from logger_test_main.")
    logger_test_main.error("This is an error message from logger_test_main.")

    logger_test_module = get_logger("MyModuleTest") # Example of getting a logger for another conceptual module
    logger_test_module.debug("This is a debug message (will not show if LOG_LEVEL is INFO).")
    logger_test_module.info("Another info message from MyModuleTest.")

    # Test that getting the same logger returns the same instance (due to _configured_loggers cache)
    logger_test_main_again = get_logger(__name__)
    if id(logger_test_main) == id(logger_test_main_again):
        logger_test_main_again.info("Logger instance for __main__ is the same (retrieved from cache).")
    else:
        # This case should ideally not be reached with the current caching logic.
        logger_test_main_again.warning("Logger instance for __main__ is different (caching might not be working as expected).")

    print("\nLogging test complete. Check console output for formatted log messages.")
    print(f"Loggers configured by this module: {list(_configured_loggers.keys())}")

```
