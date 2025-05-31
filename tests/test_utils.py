import unittest
from unittest.mock import patch, mock_open, MagicMock
import sys
import os
import yaml # For yaml.YAMLError
import logging

# Adjust sys.path to allow imports from the parent directory (project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Functions to test
from utils.config import load_config
import utils.config as utils_config_module # To reset cache
from utils.maps import get_geocode, get_place_details
import utils.maps as utils_maps_module # To mock _get_maps_api_key
import googlemaps # For googlemaps.exceptions

# --- Test Cases for utils.config ---
class TestConfig(unittest.TestCase):

    def setUp(self):
        # Reset the cache before each test in this class
        utils_config_module._cached_config = None

    @patch('yaml.safe_load')
    @patch('builtins.open', new_callable=mock_open, read_data='api_keys:\n  google_maps: "TEST_KEY_123"')
    def test_load_config_success(self, mock_file_open, mock_yaml_load):
        # Mock yaml.safe_load to return a specific dictionary
        expected_config = {'api_keys': {'google_maps': 'TEST_KEY_123'}}
        mock_yaml_load.return_value = expected_config

        config = load_config()

        self.assertEqual(config, expected_config)
        mock_file_open.assert_called_once_with(utils_config_module.CONFIG_FILE_PATH, 'r')
        mock_yaml_load.assert_called_once()

    @patch('builtins.open', side_effect=FileNotFoundError("File not found for test"))
    def test_load_config_file_not_found(self, mock_file_open):
        config = load_config()
        self.assertIsNone(config, "Config should be None if file not found")
        # Also check if _cached_config is set to {} as per current implementation for not found
        self.assertEqual(utils_config_module._cached_config, {})

    @patch('builtins.open', new_callable=mock_open, read_data='invalid: yaml: content')
    @patch('yaml.safe_load', side_effect=yaml.YAMLError("YAML parsing error for test"))
    def test_load_config_yaml_error(self, mock_yaml_load, mock_file_open):
        config = load_config()
        self.assertIsNone(config, "Config should be None on YAML error")
        self.assertEqual(utils_config_module._cached_config, {})

    @patch('builtins.open', new_callable=mock_open, read_data='') # Empty file
    @patch('yaml.safe_load') # Mock to control its behavior
    def test_load_config_empty_file(self, mock_yaml_load):
        mock_yaml_load.return_value = None # yaml.safe_load returns None for empty file
        config = load_config()
        self.assertEqual(config, {}, "Config should be an empty dict for an empty file")


# --- Test Cases for utils.maps ---
class TestMaps(unittest.TestCase):

    # This patch will apply to all test methods in this class
    # It mocks the _get_maps_api_key function within the utils.maps module
    @patch('utils.maps._get_maps_api_key')
    @patch('googlemaps.Client')
    def test_get_geocode_success(self, MockGoogleMapsClient, mock_get_key):
        mock_get_key.return_value = "VALID_TEST_KEY" # Simulate valid API key

        # Configure the mock googlemaps.Client instance and its geocode method
        mock_gmaps_instance = MockGoogleMapsClient.return_value
        mock_geocode_result = [{'geometry': {'location': {'lat': 10.0, 'lng': 20.0}}}]
        mock_gmaps_instance.geocode.return_value = mock_geocode_result

        result = get_geocode("some address")

        self.assertIsNotNone(result)
        self.assertEqual(result, {'latitude': 10.0, 'longitude': 20.0})
        mock_gmaps_instance.geocode.assert_called_once_with("some address")

    @patch('utils.maps._get_maps_api_key')
    @patch('googlemaps.Client')
    def test_get_geocode_api_error(self, MockGoogleMapsClient, mock_get_key):
        mock_get_key.return_value = "VALID_TEST_KEY"

        mock_gmaps_instance = MockGoogleMapsClient.return_value
        mock_gmaps_instance.geocode.side_effect = googlemaps.exceptions.ApiError("Test API Error")

        result = get_geocode("some address")
        self.assertIsNone(result)

    @patch('utils.maps._get_maps_api_key')
    @patch('googlemaps.Client')
    def test_get_geocode_no_results(self, MockGoogleMapsClient, mock_get_key):
        mock_get_key.return_value = "VALID_TEST_KEY"
        mock_gmaps_instance = MockGoogleMapsClient.return_value
        mock_gmaps_instance.geocode.return_value = [] # Empty list for no results

        result = get_geocode("unknown address")
        self.assertIsNone(result)

    @patch('utils.maps._get_maps_api_key')
    @patch('googlemaps.Client')
    def test_get_place_details_success(self, MockGoogleMapsClient, mock_get_key):
        mock_get_key.return_value = "VALID_TEST_KEY"

        mock_gmaps_instance = MockGoogleMapsClient.return_value
        mock_place_result = {"result": {"name": "Test Place", "formatted_address": "123 Test St"}}
        mock_gmaps_instance.place.return_value = mock_place_result

        # Define expected fields for the call to gmaps.place
        expected_fields = [
            'name', 'formatted_address', 'rating', 'photos',
            'opening_hours', 'website', 'international_phone_number',
            'geometry', 'place_id'
        ]
        result = get_place_details("some_place_id")

        self.assertIsNotNone(result)
        self.assertEqual(result, mock_place_result["result"])
        mock_gmaps_instance.place.assert_called_once_with(place_id="some_place_id", fields=expected_fields)

    @patch('utils.maps._get_maps_api_key')
    @patch('googlemaps.Client')
    def test_get_place_details_api_error(self, MockGoogleMapsClient, mock_get_key):
        mock_get_key.return_value = "VALID_TEST_KEY"

        mock_gmaps_instance = MockGoogleMapsClient.return_value
        mock_gmaps_instance.place.side_effect = googlemaps.exceptions.ApiError("Test API Error")

        result = get_place_details("some_place_id")
        self.assertIsNone(result)

    @patch('utils.maps._get_maps_api_key') # Mock the helper directly
    def test_maps_functions_no_api_key(self, mock_get_key):
        mock_get_key.return_value = None # Simulate API key not found or placeholder

        result_geocode = get_geocode("some address")
        self.assertIsNone(result_geocode, "get_geocode should return None if API key is missing")

        result_place_details = get_place_details("some_place_id")
        self.assertIsNone(result_place_details, "get_place_details should return None if API key is missing")

    def test_get_geocode_no_address(self):
        # This test doesn't need to mock _get_maps_api_key if we assume it returns a valid key,
        # or we can mock it to ensure the address check is the one failing.
        with patch('utils.maps._get_maps_api_key', return_value="VALID_TEST_KEY"):
            result = get_geocode(None) # type: ignore
            self.assertIsNone(result)
            result_empty = get_geocode("")
            self.assertIsNone(result_empty)

    def test_get_place_details_no_place_id(self):
        with patch('utils.maps._get_maps_api_key', return_value="VALID_TEST_KEY"):
            result = get_place_details(None) # type: ignore
            self.assertIsNone(result)
            result_empty = get_place_details("")
            self.assertIsNone(result_empty)


if __name__ == '__main__':
    # Temporarily disable logging to avoid excessive output during tests
    logging.disable(logging.CRITICAL)
    try:
        unittest.main()
    finally:
        logging.disable(logging.NOTSET) # Re-enable logging
