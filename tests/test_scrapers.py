import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import logging # Import logging to disable it for tests

# Adjust sys.path to allow imports from the parent directory (project root)
# This is necessary so that 'scrapers' and 'utils' can be found
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from scrapers.fablab_scraper import scrape_fablab_events
from scrapers.cultura_sp_scraper import scrape_cultura_sp_events # This is a mock scraper
import requests # For requests.exceptions.RequestException

# --- Sample HTML for FabLab Scraper Test ---
# This HTML should mimic the structure targeted by scrape_fablab_events
# Specifically, 'div.views-row' and the internal structure for title, date, location, category.
SAMPLE_FABLAB_HTML = """
<html>
<body>
  <div class="views-row">
    <a href="/cursos/oficinas/evento_fablab_1">Título Evento FabLab 1</a>
    <div class="field-content card-curso__data">15/09/2024 | 10:00 - 12:00</div>
    <div class="field-content card-curso__unidade"><a href="/unidades/fablab_centro">FabLab Central</a></div>
    <div class="field-content card-curso__tags"><a href="/tags/oficina">Oficina</a>, <a href="/tags/3d">Impressão 3D</a></div>
  </div>
  <div class="views-row">
    <a href="/cursos/palestras/evento_fablab_2">Palestra Inovação FabLab</a>
    <div class="card-curso__data">20/09/2024 | 19:00 - 21:00</div>
    <div class="card-curso__unidade"><a>FabLab Vila Mariana</a></div>
    <div class="card-curso__tags"><a>Palestra</a></div>
  </div>
</body>
</html>
"""

class TestFablabScraper(unittest.TestCase):

    @patch('requests.get')
    def test_scrape_fablab_events_success(self, mock_get):
        # Configure the mock response for requests.get
        mock_response = MagicMock()
        mock_response.content = SAMPLE_FABLAB_HTML.encode('utf-8') # Ensure content is bytes
        mock_response.raise_for_status = MagicMock() # Mock this to do nothing (simulate success)
        mock_get.return_value = mock_response

        events = scrape_fablab_events()

        self.assertIsInstance(events, list, "Should return a list")
        self.assertEqual(len(events), 2, "Should find 2 events from sample HTML")

        for event in events:
            self.assertIsInstance(event, dict, "Each event should be a dictionary")
            self.assertIn('title', event)
            self.assertIn('official_event_link', event)
            self.assertIn('date', event)
            self.assertIn('time', event)
            self.assertIn('location', event)
            self.assertIn('category', event)
            self.assertIn('description', event) # Even if N/A

            if event['title'] == "Título Evento FabLab 1":
                self.assertTrue(event['official_event_link'].endswith("/cursos/oficinas/evento_fablab_1"))
                self.assertEqual(event['date'], "15/09/2024")
                self.assertEqual(event['time'], "10:00 - 12:00")
                self.assertEqual(event['location'], "FabLab Central")
                self.assertIn("Oficina", event['category'])
                self.assertIn("Impressão 3D", event['category'])
            elif event['title'] == "Palestra Inovação FabLab":
                 self.assertTrue(event['official_event_link'].endswith("/cursos/palestras/evento_fablab_2"))
                 self.assertEqual(event['date'], "20/09/2024")

    @patch('requests.get')
    def test_scrape_fablab_events_network_error(self, mock_get):
        # Configure the mock to raise a network error
        mock_get.side_effect = requests.exceptions.RequestException("Test network error")

        events = scrape_fablab_events()

        self.assertIsInstance(events, list, "Should return a list on network error")
        self.assertEqual(len(events), 0, "Should return an empty list on network error")
        # In a real test, you might also check if logger.error was called.
        # This requires further mocking of the logger within the scraper module.

    @patch('requests.get')
    def test_scrape_fablab_no_event_cards_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = "<html><body><p>No events here.</p></body></html>".encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        events = scrape_fablab_events()
        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 0)


class TestCulturaSpScraper(unittest.TestCase):

    def test_scrape_cultura_sp_events_returns_mock_data(self):
        events = scrape_cultura_sp_events() # This is the mock scraper

        self.assertIsInstance(events, list, "Mock scraper should return a list")
        self.assertTrue(len(events) >= 2, "Mock scraper should return at least 2-3 sample events")

        for event in events:
            self.assertIsInstance(event, dict)
            self.assertIn('title', event)
            self.assertIn('description', event)
            self.assertIn('date', event)
            self.assertIn('time', event)
            self.assertIn('location', event)
            self.assertIn('category', event)
            self.assertIn('official_event_link', event)

        # Check some specific values from the known mock data
        # Example: Assuming the first mock event has a specific title
        if events: # if list is not empty
            self.assertEqual(events[0]['title'], "Exposição de Arte Moderna no Centro")
            self.assertEqual(events[0]['category'], "Exposição")


if __name__ == '__main__':
    # This allows running the tests directly from this file

    # Temporarily disable logging to avoid excessive output during tests / potential hangs
    # This is a global change for the duration of this test run.
    # A more sophisticated approach might involve configuring specific loggers
    # or using a test-specific logging configuration.
    logging.disable(logging.CRITICAL)

    try:
        unittest.main()
    finally:
        # Re-enable logging if it was disabled (important if tests are part of a larger suite)
        logging.disable(logging.NOTSET)
