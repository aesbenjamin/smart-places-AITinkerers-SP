import streamlit as st
import datetime
import sys
import os

# Adjust Python path to include the root directory of the project
# This allows imports from 'scrapers' and 'utils' modules.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

import pandas as pd # For st.map() DataFrame

# Import scraper functions
from scrapers.fablab_scraper import scrape_fablab_events
from scrapers.cultura_sp_scraper import scrape_cultura_sp_events # This is currently a mock

# --- Page Configuration (Optional but good practice) ---
st.set_page_config(
    page_title="Agente Cultural de São Paulo",
    page_icon="🎭", # Example icon
    layout="wide"
)

# --- Main Application Title ---
st.title("🎭 Agente Cultural de São Paulo")
st.markdown("Descubra eventos culturais, oficinas e exposições na cidade!")

# --- Sidebar for Filters ---
st.sidebar.header("Filtros de Eventos")

# Placeholder filter widgets
# Possible event categories - can be expanded or dynamically populated
event_categories = ["Todos", "Oficina", "Música", "Exposição", "Teatro", "Dança", "Palestra", "Curso", "Feira", "Cinema", "Outro"]
selected_event_category = st.sidebar.selectbox("Tipo de Evento (Categoria):", event_categories)

# Date filter: None means "Qualquer data"
selected_date = st.sidebar.date_input("Data do Evento (deixe em branco para qualquer data):", value=None)

# Location text query
location_query_text = st.sidebar.text_input("Filtrar por Local (parte do nome/endereço):")

# Button to trigger filtering - useful if filtering is expensive, though Streamlit reruns on widget change
# apply_filters_button = st.sidebar.button("Aplicar Filtros")

st.sidebar.markdown("---")
st.sidebar.info("Desenvolvido como parte de um projeto de IA.")


# --- Main Content Area ---

# Placeholder for Map
st.header("Mapa Interativo de Eventos")
st.markdown("_(Visualização do mapa com eventos geolocalizados será implementada aqui.)_")
# Example: Using st.map with no data or placeholder data
# map_data_placeholder = None # Or pd.DataFrame({'lat': [-23.5505], 'lon': [-46.6333]})
# st.map(map_data_placeholder)
st.map() # Shows a default map of the world, good placeholder visually

st.markdown("---")

# Section to Load and Display Event Data
st.header("Eventos Encontrados")

# Load data from scrapers
# This is a conceptual loading step. In a real app, this might be cached,
# run on a schedule, or triggered by user actions if scraping is slow.
@st.cache_data(ttl=3600) # Cache data for 1 hour
def load_event_data_with_coords():
    print("Interface: Loading event data from scrapers...")
    fablab_events_raw = scrape_fablab_events()
    cultura_sp_events_mock_raw = scrape_cultura_sp_events() # This is currently a mock

    processed_events = []

    # Process FabLab Events (add None for lat/lon for now)
    for event in fablab_events_raw:
        event['latitude'] = None
        event['longitude'] = None
        processed_events.append(event)

    # Process CulturaSP Mock Events (add mock lat/lon to some)
    # MASP: -23.5614, -46.6563
    # Centro Cultural SP: -23.5600, -46.6400 (approx)
    # Teatro Oficina: -23.5522, -46.6420 (approx)
    for i, event in enumerate(cultura_sp_events_mock_raw):
        if i == 0: # "Exposição de Arte Moderna no Centro" (mock CCSP)
            event['latitude'] = -23.5600
            event['longitude'] = -46.6400
        elif i == 1: # "Concerto da Orquestra Sinfônica Municipal" (mock Theatro Municipal)
             # Approx Theatro Municipal: -23.5451, -46.6390
            event['latitude'] = -23.5451
            event['longitude'] = -46.6390
        elif i == 2: # "Peça Teatral 'Crônicas da Cidade'" (mock Teatro Oficina)
            event['latitude'] = -23.5522
            event['longitude'] = -46.6420
        else: # Default for any other mock events
            event['latitude'] = None
            event['longitude'] = None
        processed_events.append(event)

    print(f"Interface: Loaded and processed {len(processed_events)} total events.")
    return processed_events

# Load data
all_events = load_event_data_with_coords()

# --- Filtering Logic ---
filtered_events = all_events

# Filter by Event Category
if selected_event_category != "Todos":
    filtered_events = [event for event in filtered_events if event.get('category', '').lower() == selected_event_category.lower()]

# Filter by Date
if selected_date: # If a date is selected (not None)
    filtered_events = [event for event in filtered_events if event.get('date') == selected_date.strftime("%Y-%m-%d") or event.get('date') == selected_date.strftime("%d/%m/%Y")]
    # Fablab dates are DD/MM/YYYY, mock culturaSP are YYYY-MM-DD. Handle both.

# Filter by Location Text Query (simple substring match on 'location' field)
if location_query_text:
    location_query_text_lower = location_query_text.lower()
    filtered_events = [
        event for event in filtered_events
        if location_query_text_lower in event.get('location', '').lower()
    ]

# --- Display Filtered Events and Map ---

# Prepare data for map (events with valid lat/lon)
map_display_data = []
for event in filtered_events:
    if event.get('latitude') is not None and event.get('longitude') is not None:
        map_display_data.append({
            'lat': event['latitude'],
            'lon': event['longitude'],
            # Future: Add 'size' or 'color' based on event type or other criteria for st.map
        })

if map_display_data:
    st.map(pd.DataFrame(map_display_data))
else:
    st.map() # Show default map if no geocoded events after filtering
    st.caption("Nenhum evento filtrado com coordenadas para exibir no mapa.")


st.markdown("---")
st.header(f"Eventos Encontrados ({len(filtered_events)})")

if filtered_events:
    for event in filtered_events:
        st.subheader(event.get('title', 'Título Indisponível'))

        details = []
        if event.get('date'): details.append(f"**Data:** {event.get('date')}")
        if event.get('time'): details.append(f"**Hora:** {event.get('time')}")
        details_str = " | ".join(details)
        if details_str: st.markdown(details_str)

        if event.get('location'): st.markdown(f"**Local:** {event.get('location')}")
        if event.get('category'): st.markdown(f"**Categoria:** {event.get('category')}")

        if event.get('description') and event.get('description') != "N/A (available on official event link)":
            with st.expander("Descrição"):
                st.markdown(event.get('description'))

        if event.get('official_event_link') and event.get('official_event_link') != "N/A":
            st.markdown(f"[Mais Detalhes]({event.get('official_event_link')})")
        st.markdown("---")
else:
    st.info("Nenhum evento encontrado com os filtros atuais. Tente ampliar sua busca!")

# Comments explaining the structure:
# - Event data is loaded and mock coordinates are added.
# - Filters for event type, date, and location query are applied.
# - Filtered events with coordinates are shown on st.map.
# - Filtered events are displayed as structured "cards".
# - TODO: Implement actual geocoding for FabLab events.
# - TODO: More sophisticated date filtering (ranges, today, etc.).
# - TODO: More advanced location filtering (radius search after geocoding).

if __name__ == '__main__':
    print("To run the Streamlit application, use the command:")
    print("streamlit run interface/app.py")
