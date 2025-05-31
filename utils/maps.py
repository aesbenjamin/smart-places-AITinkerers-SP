# This utility module provides functions to interact with Google Maps services.
# API Key Management:
# The Google Maps API key will eventually be loaded from a configuration file (e.g., config.yaml).
# For now, functions will accept the api_key as a direct argument.

import googlemaps
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError

# Placeholder for API key, to be replaced by config loading
# GOOGLE_MAPS_API_KEY = "YOUR_API_KEY_HERE" # Load from config.yaml

def get_geocode(api_key: str, address: str) -> dict | None:
    """
    Geocodes an address to latitude and longitude coordinates using Google Maps API.

    Args:
        api_key (str): Your Google Maps API key.
        address (str): The address string to geocode.

    Returns:
        dict | None: A dictionary with 'latitude' and 'longitude' if successful,
                     otherwise None.
    """
    if not api_key:
        print("Error: Google Maps API key is missing.")
        return None
    if not address:
        print("Error: Address for geocoding is missing.")
        return None

    gmaps = googlemaps.Client(key=api_key)

    try:
        print(f"Geocoding address: {address}")
        geocode_result = gmaps.geocode(address)

        if geocode_result and len(geocode_result) > 0:
            location = geocode_result[0]['geometry']['location']
            print(f"Geocode successful for {address}: Lat {location['lat']}, Lng {location['lng']}")
            return {'latitude': location['lat'], 'longitude': location['lng']}
        else:
            print(f"No results found for address: {address}")
            return None

    except ApiError as e:
        print(f"Google Maps API Error during geocoding for '{address}': {e}")
    except HTTPError as e:
        print(f"Google Maps HTTP Error during geocoding for '{address}': {e}")
    except Timeout:
        print(f"Google Maps API request timed out during geocoding for '{address}'.")
    except TransportError as e: # Catches network-level issues
        print(f"Google Maps Transport Error (network issue) during geocoding for '{address}': {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred during geocoding for '{address}': {e}")

    return None

def get_place_details(api_key: str, place_id: str) -> dict | None:
    """
    Retrieves detailed information for a place using its Google Maps Place ID.

    Args:
        api_key (str): Your Google Maps API key.
        place_id (str): The Place ID string for the location.

    Returns:
        dict | None: A dictionary containing place details if successful,
                     otherwise None.
    """
    if not api_key:
        print("Error: Google Maps API key is missing.")
        return None
    if not place_id:
        print("Error: Place ID for details lookup is missing.")
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

    try:
        print(f"Fetching place details for Place ID: {place_id}")
        place_details_result = gmaps.place(place_id=place_id, fields=fields)

        if place_details_result and place_details_result.get('result'):
            details = place_details_result['result']
            print(f"Successfully fetched details for {details.get('name', place_id)}")
            return details
        else:
            print(f"No results found for Place ID: {place_id}. Response: {place_details_result}")
            return None

    except ApiError as e:
        print(f"Google Maps API Error for Place ID '{place_id}': {e}")
    except HTTPError as e:
        print(f"Google Maps HTTP Error for Place ID '{place_id}': {e}")
    except Timeout:
        print(f"Google Maps API request timed out for Place ID '{place_id}'.")
    except TransportError as e:
        print(f"Google Maps Transport Error (network issue) for Place ID '{place_id}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred for Place ID '{place_id}': {e}")

    return None

if __name__ == '__main__':
    # This section is for basic testing.
    # You'll need a valid Google Maps API key with Geocoding API and Places API enabled.
    # Store it in your config.yaml or environment variable for actual use.
    print("Testing Google Maps utilities...")

    # Replace with your actual API key for testing, or ensure it's loaded from a config.
    # IMPORTANT: Do not commit your API key to version control.
    TEST_API_KEY = None # Or "YOUR_TEST_API_KEY"

    if TEST_API_KEY:
        print("\n--- Testing get_geocode ---")
        # Example address (MASP)
        address1 = "Museu de Arte de São Paulo Assis Chateaubriand - MASP, Avenida Paulista, 1578, Bela Vista, São Paulo"
        geocode1 = get_geocode(TEST_API_KEY, address1)
        if geocode1:
            print(f"Geocode for '{address1}': {geocode1}")

        address2 = "Invalid Address String For Testing Error"
        geocode2 = get_geocode(TEST_API_KEY, address2) # Should ideally print 'No results' or handle error
        if not geocode2:
            print(f"Geocoding for '{address2}' correctly returned None or failed as expected.")

        print("\n--- Testing get_place_details ---")
        # Example Place ID (You can get this from a place search or geocoding result)
        # MASP Place ID: ChIJ0xR62sBfzpQR0g0yLNRAwNo (Verify this if testing)
        place_id_masp = "ChIJ0xR62sBfzpQR0g0yLNRAwNo"
        details1 = get_place_details(TEST_API_KEY, place_id_masp)
        if details1:
            print(f"Details for Place ID '{place_id_masp}':")
            for key, value in details1.items():
                if key == 'photos' and isinstance(value, list): # Avoid printing full photo data
                    print(f"  {key}: [{len(value)} photos]")
                elif key == 'opening_hours' and isinstance(value, dict):
                    print(f"  {key}: {value.get('weekday_text', 'N/A')}")
                else:
                    print(f"  {key}: {value}")

        place_id_invalid = "InvalidPlaceIDForTestingError"
        details2 = get_place_details(TEST_API_KEY, place_id_invalid)
        if not details2:
            print(f"Place details for '{place_id_invalid}' correctly returned None or failed as expected.")

    else:
        print("\nSkipping live API tests as TEST_API_KEY is not set in maps.py.")
        print("To run tests, set a valid Google Maps API key in the TEST_API_KEY variable in this script.")
        print("Remember to enable Geocoding API and Places API in your Google Cloud Console project.")
        # Example of expected output structure (if API key was present and calls successful)
        print("\nExample expected output structure for get_geocode (if successful):")
        print("{'latitude': -23.561375, 'longitude': -46.656134}")
        print("\nExample expected output structure for get_place_details (if successful, partial):")
        print("{'name': 'Museu de Arte de São Paulo Assis Chateaubriand', 'formatted_address': 'Av. Paulista, 1578 - Bela Vista, São Paulo - SP, 01310-200, Brazil', ...}")
