# -- MOCK IMPLEMENTATION --
# This script provides a mock implementation for scraping events from the
# Secretaria Municipal de Cultura de São Paulo agenda.
# The live website (https://www.prefeitura.sp.gov.br/cidade/secretarias/cultura/agenda/)
# was found to be heavily reliant on JavaScript for loading event content,
# making it challenging to scrape reliably with simple requests/BeautifulSoup
# and even presenting difficulties for Playwright without precise, up-to-date selectors
# found via interactive browser inspection.
# This mock function returns a static list of sample events and should be
# replaced with a functional scraper when a more robust solution for the live site is developed.

# import requests # Kept for consistency, though not used in mock
# from bs4 import BeautifulSoup # Kept for consistency, though not used in mock

# Assuming utils.logger is accessible, adjust path if necessary when running standalone
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger(__name__)

def scrape_cultura_sp_events():
    """
    MOCK IMPLEMENTATION: Returns a predefined list of sample Cultura SP events.

    This function simulates the output of a real scraper. Due to challenges in
    scraping the live JavaScript-heavy website, this mock version is provided
    as a placeholder. It should be replaced with a functional scraper when possible.

    Returns:
        list: A list of dictionaries, where each dictionary represents a sample event.
    """
    logger.info("Executing MOCK scrape_cultura_sp_events().")
    logger.info("This is NOT scraping live data but returning predefined sample events.")

    sample_events = [
        { # Event 1 (Exposição)
            'title': "Exposição de Arte Moderna no Centro",
            'description': "Uma incrível coleção de arte moderna brasileira, com artistas renomados e novas promessas.",
            'date': "2024-09-10",
            'time': "10:00 - 18:00",
            'location': "Centro Cultural São Paulo, Rua Vergueiro, 1000 - Paraíso, São Paulo",
            'category': "Exposição",
            'official_event_link': "https://centrocultural.sp.gov.br/category/artes-visuais/"
        },
        { # Event 2 (Música)
            'title': "Concerto da Orquestra Sinfônica Municipal",
            'description': "A Orquestra Sinfônica Municipal apresenta um repertório clássico com peças de Villa-Lobos e Mozart.",
            'date': "2024-09-21",
            'time': "20:00 - 22:00",
            'location': "Theatro Municipal de São Paulo, Praça Ramos de Azevedo, s/n - República, São Paulo",
            'category': "Música",
            'official_event_link': "https://theatromunicipal.org.br/pt-br/categoria/concerto/"
        },
        { # Event 3 (Teatro)
            'title': "Peça Teatral 'Crônicas da Cidade'",
            'description': "Uma peça envolvente que retrata o cotidiano e as histórias da metrópole de São Paulo.",
            'date': "2024-10-05",
            'time': "19:30 - 21:00",
            'location': "Teatro Oficina Uzyna Uzona, Rua Jaceguai, 520 - Bixiga, São Paulo",
            'category': "Teatro",
            'official_event_link': "https://www.teatrooficina.com.br/programacao/"
        }
    ]

    # Ensure 'official_event_link' key consistency (already handled in previous version, but good to keep if structure changes)
    # for event in sample_events:
    #     if 'link' in event and 'official_event_link' not in event:
    #         event['official_event_link'] = event.pop('link')

    logger.info(f"Returning {len(sample_events)} mock events.")
    return sample_events

if __name__ == '__main__':
    # Configure logger for standalone script execution
    import logging
    if not logger.handlers:
         logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Testing MOCK Cultura SP scraper directly...")
    scraped_events = scrape_cultura_sp_events()
    if scraped_events:
        logger.info(f"Found {len(scraped_events)} sample events:")
        for i, evt in enumerate(scraped_events):
            logger.info(f"Event {i+1}: Title='{evt.get('title')}', Date='{evt.get('date')}', Category='{evt.get('category')}'")
    else:
        logger.info("No sample events were returned by the mock scraper.")
