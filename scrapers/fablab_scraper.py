import requests
from bs4 import BeautifulSoup

def scrape_fablab_events():
    """
    Scrapes event data from the FabLab Livre SP agenda.

    Returns:
        list: A list of dictionaries, where each dictionary represents an event.
              Returns an empty list if scraping fails or no events are found.
    """
    url = "https://www.fablablivresp.prefeitura.sp.gov.br/busca?tipo=curso" # Changed URL
    events = []

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
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
        event_cards = soup.select('article.card-curso')
        if event_cards:
            print(f"Found {len(event_cards)} event cards using selector 'article.card-curso'.")
        else:
            print(f"No event cards found using 'div.views-row' or 'article.card-curso' on {url}. The website structure might have changed.")
            return events
    else:
        print(f"Found {len(event_cards)} event cards using selector 'div.views-row'.")

    for card in event_cards:
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
                all_texts = card.find_all(string=True)
                for text_node in all_texts:
                    if '*' in text_node and '|' in text_node:
                        datetime_text = text_node.strip().lstrip('*').strip()
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
            category_elements_text = []
            # Try selector for tags field:
            tags_field = card.select_one('div[class*="tags"], div[class*="tematica"], div[class*="area"]')
            if tags_field:
                # Are they links or just text?
                tag_links = tags_field.find_all('a')
                if tag_links:
                     category_elements_text = [tag.text.strip() for tag in tag_links if tag.text.strip()]
                else: # If no links, try to get text content, split by lines or common separators
                     category_elements_text = [line.strip() for line in tags_field.text.split('\n') if line.strip()]

            if not category_elements_text: # Fallback: get all text after location if specific fields fail
                # This is very heuristic.
                # Find all text nodes after the location element's parent, or after title element if location not found
                start_node = location_element.parent if location_element else title_link_element.parent if title_link_element else None
                if start_node:
                    for sibling in start_node.find_next_siblings():
                        # Collect text from siblings, assuming they are categories
                        # This needs refinement to avoid grabbing unwanted text
                        sibling_text = sibling.get_text(separator='\n', strip=True)
                        if sibling_text:
                             # Heuristic: categories are usually short, one or two words.
                             possible_cats = [cat.strip() for cat in sibling_text.split('\n') if cat.strip() and len(cat.split()) < 4]
                             category_elements_text.extend(possible_cats)
                        if len(category_elements_text) >=2 : # Assume max 2-3 categories for this heuristic
                            break


            if category_elements_text:
                event['category'] = ", ".join(list(dict.fromkeys(category_elements_text))) # Join and remove duplicates
            else:
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

        except Exception as e:
            print(f"Error parsing an event card: {e}")
            # Optionally, add the partially parsed event or skip it
            # events.append({"title": event.get('title', "Error parsing event"), "error": str(e), "link": event.get('official_event_link')})
            continue

    return events

if __name__ == '__main__':
    # Example usage:
    print("Scraping FabLab events...")
    scraped_events = scrape_fablab_events()
    if scraped_events:
        print(f"Found {len(scraped_events)} events:")
        for i, evt in enumerate(scraped_events):
            print(f"\nEvent {i+1}:")
            for key, value in evt.items():
                print(f"  {key}: {value}")
    else:
        print("No events were scraped.")
