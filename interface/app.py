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
import datetime # Already imported but good to ensure it's here for date logic in dispatch

# Import scraper functions
from scrapers.fablab_scraper import scrape_fablab_events
from scrapers.cultura_sp_scraper import scrape_cultura_sp_events # This is currently a mock

# Import ADK agent application and mock types (assuming they are in sys.path)
from agents.cultural_agent import AgentApplication as MockAgentApplication # Rename to avoid conflict if real ADK was also imported
from agents.cultural_agent import types as MockAgentTypes # For creating mock requests

# Import logger
from utils.logger import get_logger
logger = get_logger(__name__)


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
    logger.info("Loading event data from scrapers...")
    fablab_events_raw = scrape_fablab_events() # This scraper now uses logging
    cultura_sp_events_mock_raw = scrape_cultura_sp_events() # This mock scraper also uses logging

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

    logger.info(f"Loaded and processed {len(processed_events)} total events.")
    return processed_events

# Load data
all_events = load_event_data_with_coords()
logger.debug(f"Total events loaded after initial processing: {len(all_events)}")

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


# --- Chat Interface with Mock ADK Agent ---
st.sidebar.markdown("---")
st.sidebar.header("Chat com Agente Cultural")
st.sidebar.caption("Interaja com o agente para buscar eventos.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    logger.debug("Initializing chat history in session_state.")
    st.session_state.messages = [{"role": "assistant", "content": "Olá! Sou seu Agente Cultural. Pergunte-me sobre eventos em São Paulo."}]
else:
    logger.debug("Chat history already present in session_state.")


# Display prior chat messages
for message in st.session_state.messages:
    with st.sidebar.chat_message(message["role"]):
        st.sidebar.markdown(message["content"])

# Instantiate the mock agent application
# This could be cached or made a singleton in a more complex app
@st.cache_resource
def get_mock_agent_app():
    logger.info("Initializing Mock AgentApplication instance for chat.")
    # The cultural_agent.py script now uses logging for its mock setup.
    return MockAgentApplication()

agent_app = get_mock_agent_app()
logger.debug("Mock AgentApplication instance obtained for chat.")

# Simple intent dispatcher based on keywords
def mock_intent_dispatch(user_query: str) -> tuple[str, dict]:
    """
    Super simple keyword-based dispatcher for mock intent recognition.
    Returns (intent_name, parameters_dict).
    """
    query_lower = user_query.lower()
    params = {}

    # Keywords for FindEventsNearLocation
    if "perto de" in query_lower or "próximo a" in query_lower or "em" in query_lower and not ("tipo" in query_lower or "data" in query_lower):
        intent = "FindEventsNearLocation"
        # Simplistic location extraction - assumes location is after "perto de" or "em"
        if "perto de" in query_lower:
            parts = query_lower.split("perto de", 1)
        elif "próximo a" in query_lower:
            parts = query_lower.split("próximo a", 1)
        else: # "em"
            parts = query_lower.split("em", 1)

        if len(parts) > 1:
            location_str = parts[1].strip()
            # Remove common follow-up questions for cleaner location
            location_str = location_str.split("?")[0].split("hoje")[0].split("amanhã")[0].strip()
            params['location'] = location_str
        else: # Default if parsing fails but keyword was found
            params['location'] = query_lower # Pass full query as location as a fallback
        return intent, params

    # Keywords for FindEventsByTypeDate
    # This is very basic, a real NLU is needed for robust parsing.
    # Example: "eventos de [tipo] em [data]" or "qual [tipo] para [data]"

    # Try to find event type (from our predefined list)
    event_categories_for_dispatch = [cat.lower() for cat in event_categories if cat != "Todos"]
    found_category = None
    for cat in event_categories_for_dispatch:
        if cat in query_lower:
            found_category = cat
            params['eventType'] = found_category.capitalize() # Use original capitalization for handler
            logger.debug(f"Dispatch: Found eventType keyword: {found_category}")
            break

    # Try to find a date (very simple YYYY-MM-DD or DD/MM/YYYY pattern or "hoje", "amanhã")
    # This is extremely naive date parsing for mock purposes.
    import re # Ensure re is imported if not already at top level of script
    date_match_iso = re.search(r'\d{4}-\d{2}-\d{2}', query_lower)
    date_match_br = re.search(r'\d{2}/\d{2}/\d{4}', query_lower)

    if date_match_iso:
        params['date'] = date_match_iso.group(0)
        logger.debug(f"Dispatch: Found ISO date: {params['date']}")
    elif date_match_br:
        params['date'] = date_match_br.group(0) # Note: handler might need to parse this
        logger.debug(f"Dispatch: Found BR date: {params['date']}")
    elif "hoje" in query_lower:
        params['date'] = datetime.date.today().strftime("%Y-%m-%d")
        logger.debug(f"Dispatch: Found 'hoje', date set to: {params['date']}")
    elif "amanhã" in query_lower:
        params['date'] = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        logger.debug(f"Dispatch: Found 'amanhã', date set to: {params['date']}")

    if params: # If we found any parameter for type/date
        logger.info(f"Dispatch: Intent 'FindEventsByTypeDate' with params: {params}")
        return "FindEventsByTypeDate", params

    # Default fallback or welcome
    if "olá" in query_lower or "oi" in query_lower or "bom dia" in query_lower:
        logger.info("Dispatch: Intent 'welcome'")
        return "welcome", {}

    logger.info(f"Dispatch: Intent 'DefaultFallbackIntent' for query: '{user_query}'")
    return "DefaultFallbackIntent", {'query': user_query} # Or a specific fallback handler

# Chat input processing
if prompt := st.sidebar.chat_input("Como posso te ajudar?"):
    logger.info(f"User entered chat prompt: '{prompt}'")
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.sidebar.chat_message("user"):
        st.sidebar.markdown(prompt)

    with st.sidebar.chat_message("assistant"):
        response_text = "Processando sua solicitação..."
        placeholder = st.sidebar.empty()
        placeholder.markdown(response_text + " ⏳")

        try:
            # 1. Determine intent and parameters (mocked)
            intent_name, parameters = mock_intent_dispatch(prompt)
            logger.info(f"Dispatched to intent='{intent_name}', params={parameters}")

            # 2. Create Mock AgentRequest
            # Ensure the mock types are correctly used if agents.cultural_agent is also mocking them.
            mock_request = MockAgentTypes.AgentRequest(
                intent_display_name=intent_name,
                parameters=parameters
            )

            # 3. Get and call the appropriate handler
            handler_class = agent_app.handlers.get(intent_name)

            if handler_class:
                handler_instance = handler_class(mock_request) # Pass the mock request
                handler_instance.handle() # Call the handler's logic
                agent_response_text = handler_instance.response.fulfillment_text
            elif intent_name == "DefaultFallbackIntent":
                 agent_response_text = f"Desculpe, não entendi bem o que você quis dizer com '{parameters.get('query')}'. Pode tentar de outra forma?"
            else: # Should not happen if dispatch is comprehensive or has a welcome/fallback
                agent_response_text = "Desculpe, não consegui processar sua solicitação no momento (handler não encontrado)."

            placeholder.markdown(agent_response_text) # Update placeholder with actual response
            st.session_state.messages.append({"role": "assistant", "content": agent_response_text})

        except Exception as e:
            print(f"Error processing chat input with mock agent: {e}")
            import traceback
            traceback.print_exc()
            error_message = "Ocorreu um erro ao processar sua solicitação com o agente."
            placeholder.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})


if __name__ == '__main__':
    print("To run the Streamlit application, use the command:")
    print("streamlit run interface/app.py")
