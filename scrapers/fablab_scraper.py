import requests
from bs4 import BeautifulSoup
# Assuming utils.logger is accessible, adjust path if necessary when running standalone
# For project structure, this should work if scrapers/ and utils/ are sibling dirs.
import sys, os
# Add project root to sys.path for utils.logger import if running from scrapers directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger(__name__)

def scrape_fablab_events():
    """
    Scrapes event data from the FabLab Livre SP agenda.

    Returns:
        list: A list of dictionaries, where each dictionary represents an event.
              Returns an empty list if scraping fails or no events are found.
    """
    url = "https://www.fablablivresp.prefeitura.sp.gov.br/busca?tipo=curso"
    events = []
    logger.info(f"Starting FabLab event scraping from URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return events

    soup = BeautifulSoup(response.content, 'html.parser')

    # Based on the view_text_website output for /busca?tipo=curso
    # It seems events are within 'div' elements with class 'views-row' or similar,
    # or perhaps article tags. Let's try a general approach first.
    # The text output shows titles as links like: "[22]Camiseta com Orgulho..."
    # This suggests the title is an <a> tag.
    # Dates are like: "* 7/06/2025 | 10:00 - 14:00"
    # Locations are links like: "[23]Centro Cultural Olido"
    # Categories are text below location.

    # The actual HTML structure needs to be inferred or inspected directly.
    # For now, let's assume each event item is in a 'div' with a class like 'result-item' or 'event-card'.
    # From inspecting the live site (not possible for the agent, but necessary for a human):
    # Event items are in <article class="card-curso"> OR <div class="views-row">
    # Primary attempt with 'div.views-row' as it worked in the last test.
    event_cards = soup.select('div.views-row')

    if not event_cards:
        # Fallback to 'article.card-curso' if 'div.views-row' is not found
        logger.info("No event cards found with 'div.views-row', trying 'article.card-curso'.")
        event_cards = soup.select('article.card-curso')
        if event_cards:
            logger.info(f"Found {len(event_cards)} event cards using selector 'article.card-curso'.")
        else:
            logger.warning(f"No event cards found using 'div.views-row' or 'article.card-curso' on {url}. Website structure might have changed.")
            return events
    else:
        logger.info(f"Found {len(event_cards)} event cards using selector 'div.views-row'.")

    for i, card in enumerate(event_cards):
        event = {}
        try:
            # Extract Title and Official event link
            # For views-row, title is often in a span with class 'field-content' inside a heading, or just the first <a>
            # Let's try finding the first <a> tag that has an href and some text.
            title_link_element = card.find('a', href=True, string=True) # General selector for the first link, changed text to string

            # A more specific selector based on Drupal views structure might be:
            # card.select_one('.views-field-title .field-content a') or similar
            # card.select_one('h2 a') or card.select_one('h3 a')

            if title_link_element:
                event['title'] = title_link_element.text.strip()
                event_link = title_link_element.get('href')
                if event_link and event_link.startswith('http'):
                    event['official_event_link'] = event_link
                elif event_link: # Relative link
                    event['official_event_link'] = f"https://www.fablablivresp.prefeitura.sp.gov.br{event_link}"
                else:
                    event['official_event_link'] = "N/A"
            else:
                event['title'] = "N/A"
                event['official_event_link'] = "N/A"

            # Extract Date and Time
            # In views-row, this might be in a div with class like 'views-field-field-event-date'
            # From text output: "* 7/06/2025 | 10:00 - 14:00"
            # This looks like it's text content. We might need to find a specific div/span.
            # Let's try finding a div that contains '|' and '/' which are typical for date/time strings.
            datetime_text = ""
            # Try to find a specific field for date, often includes "date" or "data" in class name
            date_field = card.select_one('div[class*="date"], div[class*="data"], span[class*="date"], span[class*="data"]')
            if date_field:
                datetime_text = date_field.text.strip()
            else: # Fallback: search for text node containing '*' and '|'
                # This fallback might be too broad or pick up unintended text.
                # Consider refining if it causes issues.
                all_texts = card.find_all(string=True, recursive=False) # Check direct text children first
                for text_node in all_texts:
                    cleaned_node_text = text_node.strip()
                    if cleaned_node_text.startswith('*') and '|' in cleaned_node_text:
                        datetime_text = cleaned_node_text.lstrip('*').strip()
                        break
                if not datetime_text: # If not found in direct children, search deeper but be more careful
                    all_texts_recursive = card.find_all(string=True)
                    for text_node_recursive in all_texts_recursive:
                        cleaned_node_text_recursive = text_node_recursive.strip()
                        if cleaned_node_text_recursive.startswith('*') and '|' in cleaned_node_text_recursive:
                             # Ensure it's not part of something already captured, e.g. title or location.
                             # This heuristic is tricky. A more stable selector is always better.
                            if not title_link_element or (title_link_element and cleaned_node_text_recursive not in title_link_element.get_text(strip=True)):
                                datetime_text = cleaned_node_text_recursive.lstrip('*').strip()
                                break

            if datetime_text:
                if "|" in datetime_text:
                    date_part, time_part = datetime_text.split("|", 1)
                    event['date'] = date_part.strip()
                    event['time'] = time_part.strip()
                else:
                    event['date'] = datetime_text
                    event['time'] = "N/A"
            else:
                event['date'] = "N/A"
                event['time'] = "N/A"

            # Extract Location (Venue name/address)
            # This is often the second <a> tag in a views-row structure, or in a field like 'views-field-field-event-location'
            all_links = card.find_all('a', href=True, string=True) # changed text to string
            location_element = None
            if len(all_links) > 1:
                # Assuming the second link is the location if the first was the title.
                # This is fragile. A class-based selector is better.
                # e.g. card.select_one('.views-field-field-unidade .field-content a')
                # For now, let's try a more specific selector for location if possible,
                # or default to the second link.
                location_field = card.select_one('div[class*="unidade"], div[class*="location"], span[class*="unidade"], span[class*="location"]')
                if location_field and location_field.find('a'):
                    location_element = location_field.find('a')
                elif title_link_element and all_links[1] != title_link_element : # ensure it's not the title link again
                    location_element = all_links[1]


            if location_element:
                event['location'] = location_element.text.strip()
            else:
                event['location'] = "N/A"

            # Extract Categories
            # These might be text nodes or links within a 'views-field-field-tags' or similar.
            # From text output: "Sustentabilidade", "Corte e Costura"
            # These followed the location.
            category_texts = []
            # Try selector for tags field:
            # Common Drupal class for fields: .views-field-field-[your-field-name]
            # More general: div with class containing "tags", "tematica", "area"
            tags_container = card.select_one('div[class*="tags"], div[class*="tematica"], div[class*="area"], div.field--name-field-tags') # Added common Drupal pattern
            if tags_container:
                # Are they links or just text?
                tag_links = tags_container.find_all('a')
                if tag_links:
                     category_texts = [tag.text.strip() for tag in tag_links if tag.text.strip()]
                else: # If no links, try to get text content, split by lines or common separators
                     category_texts = [line.strip() for line in tags_container.text.split('\n') if line.strip() and len(line.strip()) > 1] # Avoid single char/empty lines

            # Fallback logic for categories (if specific field not found or empty)
            if not category_texts and location_element:
                # Heuristic: Try to get text nodes that are siblings of the location's parent, or title's parent
                start_node_for_cat_search = location_element.parent if location_element.parent else (title_link_element.parent if title_link_element.parent else None)
                if start_node_for_cat_search:
                    for sibling in start_node_for_cat_search.find_next_siblings():
                        sibling_text = sibling.get_text(separator=' ', strip=True)
                        if sibling_text:
                            # Avoid taking very long text that might be descriptions
                            if len(sibling_text) < 50: # Arbitrary length limit for category text
                                category_texts.append(sibling_text)
                            else:
                                break # Stop if text is too long (likely not a category list)
                        if len(category_texts) >= 2: # Assume max 2-3 categories for this heuristic
                            break

            if category_texts:
                # Clean up potential duplicates if multiple selectors found similar text
                unique_categories = []
                seen_categories = set()
                for cat_text in category_texts:
                    # Further split if a single string contains multiple categories (e.g. "Category1 / Category2")
                    split_cats = [c.strip() for c in cat_text.replace('/', ',').split(',') if c.strip()]
                    for cat in split_cats:
                        if cat.lower() not in seen_categories:
                            unique_categories.append(cat)
                            seen_categories.add(cat.lower())
                event['category'] = ", ".join(unique_categories)
            else: # Last fallback: infer from title
                event_text_lower = event.get('title', "").lower()
                if "oficina" in event_text_lower:
                    event['category'] = "Oficina"
                elif "palestra" in event_text_lower:
                    event['category'] = "Palestra"
                elif "curso" in event_text_lower:
                    event['category'] = "Curso"
                else:
                    event['category'] = "Outro"

            # Description is not available on this list page.
            # Setting to N/A for now.
            event['description'] = "N/A (available on official event link)"

            events.append(event)
            logger.debug(f"Successfully parsed event card {i+1}: {event.get('title')}")

        except Exception as e:
            logger.error(f"Error parsing an event card (index {i}): {e}", exc_info=True)
            # Optionally add the partially parsed event or skip it
            # events.append({"title": event.get('title', "Error parsing event"), "error": str(e), "link": event.get('official_event_link')})
            continue

    logger.info(f"FabLab scraping finished. Found {len(events)} events.")
    return events

if __name__ == '__main__':
    # Example usage:
    # Configure logger for standalone script execution (if not already configured by importing module)
    # This is mainly for testing this script directly.
    # In a project, the main entry point would configure logging.
    if not logger.handlers: # Basic check, assumes default setup if handlers exist
         logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Starting FabLab scraper directly for testing...")
    scraped_events = scrape_fablab_events()
    if scraped_events:
        logger.info(f"Found {len(scraped_events)} events:")
        for i, evt in enumerate(scraped_events):
            # Using logger.info for structured output, could also just print for direct script test
            logger.info(f"Event {i+1}: Title='{evt.get('title')}', Date='{evt.get('date')}', Location='{evt.get('location')}', Category='{evt.get('category')}'")
    else:
        logger.info("No events were scraped.")
