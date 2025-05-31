# utils/config.py
"""
Handles loading and caching of application configuration from a YAML file.

This module provides a centralized way to access configuration settings,
such as API keys, default values, or other parameters needed by the application.
It reads from `config.yaml` located in the project root and caches the
configuration to avoid repeated file I/O.
"""

import yaml
import os
from .logger import get_logger # Assuming logger.py is in the same directory (utils)

logger = get_logger(__name__)

# Define the expected path to the config.yaml file.
# Assumes this script (utils/config.py) is in a subdirectory (e.g., 'utils')
# of the project root where config.yaml is located.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE_PATH = os.path.join(_PROJECT_ROOT, 'config.yaml')

# In-memory cache for the loaded configuration.
_cached_config = None

def load_config() -> dict | None:
    """
    Reads and parses the `config.yaml` file from the project root.

    The configuration is loaded only once and then cached for subsequent calls
    to this function.

    Handles potential errors:
    - `FileNotFoundError`: If `config.yaml` is not found.
    - `yaml.YAMLError`: If there's an error parsing the YAML content.
    - Other `Exception`: For any other unexpected errors during loading.

    In case of `FileNotFoundError` or parsing errors, an error is logged,
    and `None` is returned. If the YAML file is empty or contains only comments,
    an empty dictionary is returned and a warning is logged.

    Returns:
        dict | None: The configuration dictionary if successful.
                     Returns an empty dictionary if the config file is empty or invalid YAML.
                     Returns `None` if the file is not found or a critical parsing error occurs.
                     The result is cached for subsequent calls.
    """
    global _cached_config
    if _cached_config is not None:
        logger.debug("Returning cached configuration.")
        return _cached_config

    logger.info(f"Attempting to load configuration from: {CONFIG_FILE_PATH}")
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
            if config_data is None:
                logger.warning(f"Configuration file at {CONFIG_FILE_PATH} is empty or not valid YAML. Returning empty config.")
                _cached_config = {} # Cache empty dict for empty/invalid file
                return _cached_config

            _cached_config = config_data
            logger.info("Configuration loaded successfully.")
            return config_data
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {CONFIG_FILE_PATH}. Returning None.")
        _cached_config = {} # Cache empty dict to prevent re-attempts for a non-existent file
        return None
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML in {CONFIG_FILE_PATH}: {e}. Returning None.")
        _cached_config = {} # Cache empty dict on critical parse error
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading config: {e}. Returning None.", exc_info=True)
        _cached_config = {} # Cache empty dict on other errors
        return None

if __name__ == '__main__':
    # This block is for testing the configuration loader directly.
    # It uses its own logger instance for test-specific messages.
    main_test_logger = get_logger(f"{__name__}.test")
    main_test_logger.info("Testing configuration loader...")

    # First call to load_config() will attempt to read the file and use the module-level logger.
    config = load_config()

    if config is not None:
        main_test_logger.info(f"Loaded configuration content (first load): {config if config else '{}'}")

        api_keys = config.get('api_keys')
        if api_keys:
            google_maps_key = api_keys.get('google_maps')
            if google_maps_key and google_maps_key != "YOUR_GOOGLE_MAPS_API_KEY_HERE":
                main_test_logger.info(f"Google Maps API Key found: {google_maps_key[:4]}... (masked)")
            elif google_maps_key:
                main_test_logger.info(f"Google Maps API Key found, but it's the placeholder: '{google_maps_key}'")
            else:
                main_test_logger.warning("Google Maps API Key not found under 'api_keys' in the loaded config.")
        else:
            main_test_logger.warning("'api_keys' section not found in the loaded config.")

        main_test_logger.info("Testing cached config load...")
        config2 = load_config() # This call should use the cached configuration.
        if config2 is config:
            main_test_logger.info("Configuration was successfully loaded from cache (same object instance).")
        else:
            # This would indicate an issue with the caching logic if reached.
            main_test_logger.error("Error: Configuration was reloaded instead of using cache, or cache returned a different object.")
    else:
        # This means load_config() returned None, indicating a failure like file not found.
        main_test_logger.error("Configuration could not be loaded. Review logs from 'utils.config' for details.")

    main_test_logger.info(f"To verify correct behavior, ensure '{CONFIG_FILE_PATH}' exists and is properly formatted.")

```
