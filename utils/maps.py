# utils/maps.py
"""
Provides utility functions to interact with Google Maps services,
including geocoding addresses and fetching place details.

API key management is handled internally by loading from `config.yaml`.
"""

import googlemaps
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError
from utils.config import load_config # Import the configuration loader
from .logger import get_logger # Assuming logger.py is in the same directory (utils)

logger = get_logger(__name__)

# Constant for the API key placeholder value from config.yaml
API_KEY_PLACEHOLDER = "YOUR_GOOGLE_MAPS_API_KEY_HERE"

def _get_maps_api_key() -> str | None:
    """
    Helper function to load and retrieve the Google Maps API key from config.yaml.

    It checks if the configuration can be loaded, if the 'api_keys' section and
    'google_maps' key exist, and if the key is not the placeholder value.
    Appropriate error messages are logged if issues are found.

    Returns:
        str | None: The Google Maps API key if found and valid, otherwise None.
    """
    config = load_config() # load_config now uses its own logger
    if not config: # load_config would return None on file not found or major parse error
        logger.error("Failed to load configuration for Maps API key.")
        return None

    api_key = config.get('api_keys', {}).get('google_maps')

    if not api_key:
        logger.error("Google Maps API key not found in configuration (api_keys.google_maps).")
        return None
    if api_key == API_KEY_PLACEHOLDER:
        logger.error(f"Google Maps API key is still the placeholder value ('{API_KEY_PLACEHOLDER}'). Please update config.yaml.")
        return None

    logger.debug("Successfully retrieved Google Maps API key from configuration.")
    return api_key

def get_geocode(address: str) -> dict | None:
    """
    Geocodes an address string to latitude and longitude coordinates using Google Maps API.
    The API key is automatically loaded from `config.yaml`.

    Args:
        address (str): The address string to geocode (e.g., "Rua Augusta, São Paulo, SP").

    Returns:
        dict | None: A dictionary with 'latitude' and 'longitude' keys if successful
                     (e.g., {'latitude': -23.5505, 'longitude': -46.6333}),
                     otherwise None. Logs errors or warnings on failure.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        # _get_maps_api_key already logs detailed errors
        return None

    if not address or not isinstance(address, str) or not address.strip():
        logger.error("Address for geocoding is missing or invalid.")
        return None

    gmaps = googlemaps.Client(key=api_key)
    logger.debug(f"Attempting to geocode address: '{address}'")

    try:
        geocode_result = gmaps.geocode(address)

        if geocode_result and len(geocode_result) > 0:
            location = geocode_result[0]['geometry']['location']
            logger.info(f"Geocode successful for '{address}': Lat {location['lat']}, Lng {location['lng']}")
            return {'latitude': location['lat'], 'longitude': location['lng']}
        else:
            logger.warning(f"No geocoding results found for address: {address}")
            return None

    except ApiError as e:
        logger.error(f"Google Maps API Error during geocoding for '{address}': {e}", exc_info=True)
    except HTTPError as e: # Typically for 4xx/5xx HTTP status codes
        logger.error(f"Google Maps HTTP Error during geocoding for '{address}': {e}", exc_info=True)
    except Timeout:
        logger.error(f"Google Maps API request timed out during geocoding for '{address}'.")
    except TransportError as e: # Catches network-level issues like DNS failure, refused connection
        logger.error(f"Google Maps Transport Error (network issue) during geocoding for '{address}': {e}", exc_info=True)
    except Exception as e: # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred during geocoding for '{address}': {e}", exc_info=True)

    return None

def get_place_details(place_id: str) -> dict | None:
    """
    Retrieves detailed information for a specific place using its Google Maps Place ID.
    The API key is automatically loaded from `config.yaml`.

    Args:
        place_id (str): The Place ID string for the location (e.g., "ChIJ0xR62sBfzpQR0g0yLNRAwNo").

    Returns:
        dict | None: A dictionary containing various place details (name, address, rating, etc.)
                     if successful, otherwise None. Logs errors or warnings on failure.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        # _get_maps_api_key already logs detailed errors
        return None

    if not place_id or not isinstance(place_id, str) or not place_id.strip():
        logger.error("Place ID for details lookup is missing or invalid.")
        return None

    gmaps = googlemaps.Client(key=api_key)

    # Define the fields you want to request.
    # Refer to Google Maps Place Details API documentation for all available fields.
    fields = [
        'name', 'formatted_address', 'rating', 'photos',
        'opening_hours', 'website', 'international_phone_number',
        'geometry', # For lat/lng
        'place_id' # Good to have for confirmation
    ]
    logger.debug(f"Attempting to fetch place details for Place ID: '{place_id}' with fields: {fields}")

    try:
        place_details_result = gmaps.place(place_id=place_id, fields=fields)

        if place_details_result and place_details_result.get('result'):
            details = place_details_result['result']
            logger.info(f"Successfully fetched place details for '{details.get('name', place_id)}' (ID: {place_id})")
            return details
        else:
            logger.warning(f"No place details found for Place ID: {place_id}. Response: {place_details_result}")
            return None

    except ApiError as e:
        logger.error(f"Google Maps API Error for Place ID '{place_id}': {e}", exc_info=True)
    except HTTPError as e:
        logger.error(f"Google Maps HTTP Error for Place ID '{place_id}': {e}", exc_info=True)
    except Timeout:
        logger.error(f"Google Maps API request timed out for Place ID '{place_id}'.")
    except TransportError as e:
        logger.error(f"Google Maps Transport Error (network issue) for Place ID '{place_id}': {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred for Place ID '{place_id}': {e}", exc_info=True)

    return None

if __name__ == '__main__':
    # This section is for basic testing of the maps utility functions.
    # It relies on the API key being correctly configured in 'config.yaml'.
    main_logger = get_logger(__name__)
    main_logger.info("Testing Google Maps utilities (API key loaded from config.yaml)...")

    # Note: load_config() itself logs, so we don't need to print its direct output here.
    _test_config = load_config()
    _test_api_key = _test_config.get('api_keys', {}).get('google_maps') if _test_config else None

    if _test_api_key and _test_api_key != API_KEY_PLACEHOLDER:
        main_logger.info("--- Testing get_geocode (with key from config) ---")
        address1 = "Museu de Arte de São Paulo Assis Chateaubriand - MASP, Avenida Paulista, 1578, Bela Vista, São Paulo"
        geocode1 = get_geocode(address1)
        if geocode1:
            main_logger.info(f"Geocode for '{address1}': {geocode1}")

        address2 = "Invalid Address String For Testing Error From MapsPy"
        geocode2 = get_geocode(address2)
        if not geocode2:
            main_logger.info(f"Geocoding for '{address2}' correctly returned None or failed as expected (logged by get_geocode).")

        main_logger.info("--- Testing get_place_details (with key from config) ---")
        place_id_masp = "ChIJ0xR62sBfzpQR0g0yLNRAwNo" # MASP Place ID
        details1 = get_place_details(place_id_masp)
        if details1:
            main_logger.info(f"Details for Place ID '{place_id_masp}':")
            # Print some details using main_logger for demonstration
            main_logger.info(f"  Name: {details1.get('name')}")
            main_logger.info(f"  Address: {details1.get('formatted_address')}")
            main_logger.info(f"  Rating: {details1.get('rating', 'N/A')}")
            if 'opening_hours' in details1 and isinstance(details1['opening_hours'], dict):
                 main_logger.info(f"  Opening Hours (weekday_text): {details1['opening_hours'].get('weekday_text', 'N/A')}")

        place_id_invalid = "InvalidPlaceIDForTestingError123"
        details2 = get_place_details(place_id_invalid) # Corrected: No API key argument
        if not details2:
            main_logger.info(f"Place details for '{place_id_invalid}' correctly returned None or failed as expected (logged by get_place_details).")
    else:
        main_logger.warning("Skipping live API tests for maps.py.")
        if not _test_config:
             main_logger.warning("Reason: Configuration could not be loaded (check utils.config logs).")
        elif not _test_api_key:
            main_logger.warning("Reason: Google Maps API key not found in config.yaml (api_keys.google_maps).")
        elif _test_api_key == API_KEY_PLACEHOLDER:
            main_logger.warning(f"Reason: Google Maps API key in config.yaml is still the placeholder value ('{API_KEY_PLACEHOLDER}').")
        main_logger.info("To run live tests, set a valid Google Maps API key in config.yaml and ensure Geocoding & Places APIs are enabled.")

        main_logger.info("Example expected output structure for get_geocode (if successful):")
        main_logger.info("{'latitude': -23.561375, 'longitude': -46.656134}")
        main_logger.info("Example expected output structure for get_place_details (if successful, partial):")
        main_logger.info("{'name': 'Museu de Arte de São Paulo Assis Chateaubriand', 'formatted_address': 'Av. Paulista, 1578 - Bela Vista, São Paulo - SP, 01310-200, Brazil', ...}")

```
