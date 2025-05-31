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

import requests # Kept for consistency, though not used in mock
from bs4 import BeautifulSoup # Kept for consistency, though not used in mock

def scrape_cultura_sp_events():
    """
    MOCK IMPLEMENTATION: Returns a predefined list of sample Cultura SP events.

    This function simulates the output of a real scraper. Due to challenges in
    scraping the live JavaScript-heavy website, this mock version is provided
    as a placeholder. It should be replaced with a functional scraper when possible.

    Returns:
        list: A list of dictionaries, where each dictionary represents a sample event.
    """
    print("Executing MOCK scrape_cultura_sp_events().")
    print("This is NOT scraping live data but returning predefined sample events.")

    sample_events = [
        {
            'title': "Exposição de Arte Moderna no Centro",
            'description': "Uma incrível coleção de arte moderna brasileira, com artistas renomados e novas promessas.",
            'date': "2024-09-10", # Future date
            'time': "10:00 - 18:00",
            'location': "Centro Cultural São Paulo, Rua Vergueiro, 1000 - Paraíso, São Paulo",
            'category': "Exposição",
            'official_event_link': "https://centrocultural.sp.gov.br/category/artes-visuais/" # Example link
        },
        {
            'title': "Concerto da Orquestra Sinfônica Municipal",
            'description': "A Orquestra Sinfônica Municipal apresenta um repertório clássico com peças de Villa-Lobos e Mozart.",
            'date': "2024-09-21", # Future date
            'time': "20:00 - 22:00",
            'location': "Theatro Municipal de São Paulo, Praça Ramos de Azevedo, s/n - República, São Paulo",
            'category': "Música",
            'official_event_link': "https://theatromunicipal.org.br/pt-br/categoria/concerto/" # Example link
        },
        {
            'title': "Peça Teatral 'Crônicas da Cidade'",
            'description': "Uma peça envolvente que retrata o cotidiano e as histórias da metrópole de São Paulo.",
            'date': "2024-10-05", # Future date
            'time': "19:30 - 21:00",
            'location': "Teatro Oficina Uzyna Uzona, Rua Jaceguai, 520 - Bixiga, São Paulo",
            'category': "Teatro",
            'official_event_link': "https://www.teatrooficina.com.br/programacao/" # Example link
        }
    ]

    # Rename 'link' to 'official_event_link' to match expected key from previous scrapers
    for event in sample_events:
        if 'link' in event and 'official_event_link' not in event:
            event['official_event_link'] = event.pop('link')

    return sample_events

if __name__ == '__main__':
    print("Testing MOCK Cultura SP scraper...")
    scraped_events = scrape_cultura_sp_events()
    if scraped_events:
        print(f"\nFound {len(scraped_events)} sample events:")
        for i, evt in enumerate(scraped_events):
            print(f"\nEvent {i+1}:")
            for key, value in evt.items():
                print(f"  {key}: {value}")
    else:
        print("\nNo sample events were returned by the mock scraper.")
