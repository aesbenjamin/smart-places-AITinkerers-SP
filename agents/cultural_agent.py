# agents/cultural_agent.py

# This file defines the main cultural agent application using the Agent Development Kit (ADK).
# It sets up intent handlers and registers them with the agent application.

# Assuming utils.logger is accessible, adjust path if necessary when running standalone
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

logger = get_logger(__name__)

# Note: The exact import paths for 'agent_application' and 'IntentHandler'
# might vary based on the specific version or structure of the ADK provided.
# This implementation is based on common patterns found in ADK examples like goo.gle/ice-cream-agent-code.
try:
    from agent_sdk import agent_application, IntentHandler, types
    logger.info("Successfully imported agent_sdk.")
except ImportError:
    logger.warning("agent_sdk not found. Using mock objects for IntentHandler and agent_application.")

    class MockAgentIntentInfo:
        def __init__(self, display_name=""):
            self.display_name = display_name
            self.parameters = {}

    class MockAgentRequest:
        def __init__(self, intent_display_name="", parameters=None):
            self.intent_info = MockAgentIntentInfo(display_name=intent_display_name)
            if parameters:
                self.intent_info.parameters = {k: {'resolved_value': v} for k, v in parameters.items()}

        def get_parameter(self, param_name):
            param_data = self.intent_info.parameters.get(param_name)
            return param_data.get('resolved_value') if param_data else None

    class MockAgentResponse:
        def __init__(self):
            self.fulfillment_text = ""
            self.session_state = {}

    class types:
        AgentRequest = MockAgentRequest
        AgentResponse = MockAgentResponse

    class IntentHandler:
        def __init__(self, request: types.AgentRequest):
            self.request = request
            self.response = types.AgentResponse()

        def handle(self):
            pass

    class AgentApplication:
        def __init__(self):
            self.handlers = {}
            logger.info("Mock AgentApplication created.")

        def add_intent_handler(self, intent_name, handler_class):
            self.handlers[intent_name] = handler_class
            logger.info(f"Mock: Registered {handler_class.__name__} for intent '{intent_name}'")

        def run(self, port=8080):
            logger.info(f"Mock AgentApplication 'running' (handlers registered: {list(self.handlers.keys())})")

# Define Intent Handlers:
class WelcomeHandler(IntentHandler):
    def handle(self):
        logger.info("WelcomeHandler: Handling intent.")
        self.response.fulfillment_text = "Bem-vindo ao Agente Cultural de São Paulo! Como posso ajudar?"
        logger.debug(f"WelcomeHandler: Response set to: '{self.response.fulfillment_text}'")

# --- Mock Event Data ---
SHARED_MOCK_EVENTS = [
    {'title': "Oficina de Impressão 3D no FabLab", 'description': "Aprenda a modelar e imprimir em 3D.", 'date': "2024-09-15", 'time': "14:00 - 17:00", 'location': "FabLab Centro, Av. Principal, 100", 'category': "Oficina", 'official_event_link': "http://example.com/fablab_event1"},
    {'title': "Concerto de Jazz no Parque", 'description': "Show ao ar livre com bandas locais.", 'date': "2024-09-15", 'time': "18:00 - 20:00", 'location': "Parque da Cidade, Setor Sul", 'category': "Música", 'official_event_link': "http://example.com/music_event1"},
    {'title': "Exposição Fotográfica 'Olhares Urbanos'", 'description': "Fotografias retratando a vida na cidade.", 'date': "2024-09-20", 'time': "10:00 - 19:00", 'location': "Galeria Municipal, Rua das Artes, 20", 'category': "Exposição", 'official_event_link': "http://example.com/expo_event1"},
    {'title': "Peça Teatral 'O Sonho'", 'description': "Drama clássico em nova montagem.", 'date': "2024-09-15", 'time': "20:00 - 22:00", 'location': "Teatro Principal, Praça Central", 'category': "Teatro", 'official_event_link': "http://example.com/teatro_event1"},
    {'title': "Curso de Pintura Aquarela", 'description': "Aulas para iniciantes e avançados.", 'date': "2024-09-20", 'time': "09:00 - 12:00", 'location': "Casa de Cultura Leste, Vila Esperança", 'category': "Curso", 'official_event_link': "http://example.com/curso_event1"},
    {'title': "Festival de Cinema Independente", 'description': "Mostra de filmes independentes.", 'date': "2024-09-22", 'time': "13:00 - 23:00", 'location': "Cine Belas Artes, Rua Augusta, 300", 'category': "Cinema", 'official_event_link': "http://example.com/cinema_event1"},
    {'title': "Feira de Artesanato da Vila Mariana", 'description': "Artesanato local e comidas típicas.", 'date': "2024-09-28", 'time': "10:00 - 17:00", 'location': "Praça da Vila Mariana", 'category': "Feira", 'official_event_link': "http://example.com/feira_vilamariana"},
]

class FindEventsHandler(IntentHandler):
    def handle(self):
        logger.info("FindEventsHandler: Handling intent.")
        event_type_param = self.request.get_parameter('eventType')
        date_param = self.request.get_parameter('date')
        logger.info(f"FindEventsHandler: Extracted parameters: eventType='{event_type_param}', date='{date_param}'")

        current_events = SHARED_MOCK_EVENTS
        filtered_events = []
        if not event_type_param and not date_param:
            logger.info("FindEventsHandler: No specific filters provided by user. Placeholder: returning all mock events for now.")
            filtered_events = current_events
        else:
            for event in current_events:
                match_type = True
                match_date = True
                if event_type_param:
                    if event_type_param.lower() not in event['category'].lower():
                        match_type = False
                if date_param:
                    if date_param != event['date']:
                        match_date = False
                if match_type and match_date:
                    filtered_events.append(event)

        logger.info(f"FindEventsHandler: Found {len(filtered_events)} events after filtering.")

        if filtered_events:
            event_titles = [event['title'] for event in filtered_events]
            response_text = f"Encontrei {len(filtered_events)} eventos"
            if event_type_param:
                response_text += f" do tipo '{event_type_param}'"
            if date_param:
                response_text += f" para a data {date_param}"
            response_text += f": {'; '.join(event_titles)}."
        else:
            response_text = "Desculpe, não encontrei eventos"
            if event_type_param:
                response_text += f" do tipo '{event_type_param}'"
            if date_param:
                response_text += f" para a data {date_param}"
            response_text += ". Gostaria de tentar outra busca?"
        self.response.fulfillment_text = response_text
        logger.debug(f"FindEventsHandler: Response set to: '{self.response.fulfillment_text}'")

class FindEventsNearLocationHandler(IntentHandler):
    def handle(self):
        logger.info("FindEventsNearLocationHandler: Handling intent.")
        location_query = self.request.get_parameter('location')
        logger.info(f"FindEventsNearLocationHandler: Extracted location_query='{location_query}'")

        if not location_query:
            self.response.fulfillment_text = "Por favor, especifique um local para que eu possa encontrar eventos próximos."
            logger.info(f"FindEventsNearLocationHandler: Response set to: '{self.response.fulfillment_text}' (no location provided)")
            return

        logger.info(f"FindEventsNearLocationHandler: Simulating geocoding for '{location_query}'.")
        current_events = SHARED_MOCK_EVENTS
        filtered_events = []
        location_query_lower = location_query.lower()
        for event in current_events:
            if location_query_lower in event.get('location', '').lower():
                filtered_events.append(event)

        logger.info(f"FindEventsNearLocationHandler: Found {len(filtered_events)} events containing '{location_query}' in their location string.")

        if filtered_events:
            event_titles = [event['title'] for event in filtered_events]
            response_text = f"Encontrei {len(filtered_events)} eventos perto de '{location_query}': {'; '.join(event_titles)}."
        else:
            response_text = f"Desculpe, não encontrei eventos perto de '{location_query}'. Gostaria de tentar outro local?"
        self.response.fulfillment_text = response_text
        logger.debug(f"FindEventsNearLocationHandler: Response set to: '{self.response.fulfillment_text}'")

# Create the Agent Application instance
ADK_SDK_AVAILABLE = 'agent_application' in globals()
if ADK_SDK_AVAILABLE:
    app = agent_application.AgentApplication()
else:
    app = AgentApplication()

app.add_intent_handler("DefaultWelcomeIntent", WelcomeHandler)
app.add_intent_handler("welcome", WelcomeHandler)
app.add_intent_handler("FindEventsByTypeDate", FindEventsHandler)
app.add_intent_handler("FindEventsNearLocation", FindEventsNearLocationHandler)

if __name__ == '__main__':
    logger.info("Cultural Agent Application - Main Block")
    logger.info("This script defines the agent handlers and application.")

    if (ADK_SDK_AVAILABLE and isinstance(app, agent_application.AgentApplication)) or \
       (not ADK_SDK_AVAILABLE and isinstance(app, AgentApplication)):
        logger.info("AgentApplication instantiated successfully.")
        if hasattr(app, 'handlers'):
             logger.info(f"Registered handlers: {app.handlers}")
        elif hasattr(app, '_name_to_handler_map'):
            logger.info(f"Registered handlers (from _name_to_handler_map): {app._name_to_handler_map}")

    logger.info("--- Conceptual Handler Test ---")
    if not ADK_SDK_AVAILABLE:
        logger.info("Running conceptual test with MOCK request for 'FindEventsByTypeDate'...")
        try:
            mock_params_case1 = {'eventType': "Música", 'date': "2024-09-15"}
            mock_request_case1 = types.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=mock_params_case1)
            handler_class_case1 = app.handlers.get("FindEventsByTypeDate")
            if handler_class_case1:
                logger.info(f"Testing FindEventsByTypeDate with params: {mock_params_case1}")
                handler_instance_case1 = handler_class_case1(mock_request_case1)
                handler_instance_case1.handle()
                logger.info(f"Response: {handler_instance_case1.response.fulfillment_text}")
            else:
                logger.warning("Could not find handler for 'FindEventsByTypeDate'.")

            mock_params_case2 = {'eventType': "Exposição"}
            mock_request_case2 = types.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=mock_params_case2)
            if handler_class_case1:
                logger.info(f"Testing FindEventsByTypeDate with params: {mock_params_case2}")
                handler_instance_case2 = handler_class_case1(mock_request_case2)
                handler_instance_case2.handle()
                logger.info(f"Response: {handler_instance_case2.response.fulfillment_text}")

            mock_params_case3 = {'eventType': "Dança", 'date': "2024-01-01"}
            mock_request_case3 = types.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=mock_params_case3)
            if handler_class_case1:
                logger.info(f"Testing FindEventsByTypeDate with params: {mock_params_case3} (expected no match)")
                handler_instance_case3 = handler_class_case1(mock_request_case3)
                handler_instance_case3.handle()
                logger.info(f"Response: {handler_instance_case3.response.fulfillment_text}")

            logger.info("--- Testing FindEventsNearLocationHandler ---")
            handler_class_loc = app.handlers.get("FindEventsNearLocation")
            if handler_class_loc:
                mock_loc_params1 = {'location': "Vila Mariana"}
                mock_loc_request1 = types.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=mock_loc_params1)
                logger.info(f"Testing FindEventsNearLocation with params: {mock_loc_params1}")
                handler_loc_instance1 = handler_class_loc(mock_loc_request1)
                handler_loc_instance1.handle()
                logger.info(f"Response: {handler_loc_instance1.response.fulfillment_text}")

                mock_loc_params2 = {'location': "Jardins"}
                mock_loc_request2 = types.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=mock_loc_params2)
                logger.info(f"Testing FindEventsNearLocation with params: {mock_loc_params2} (expected no match)")
                handler_loc_instance2 = handler_class_loc(mock_loc_request2)
                handler_loc_instance2.handle()
                logger.info(f"Response: {handler_loc_instance2.response.fulfillment_text}")

                mock_loc_params3 = {}
                mock_loc_request3 = types.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=mock_loc_params3)
                logger.info(f"Testing FindEventsNearLocation with params: {mock_loc_params3} (no location)")
                handler_loc_instance3 = handler_class_loc(mock_loc_request3)
                handler_loc_instance3.handle()
                logger.info(f"Response: {handler_loc_instance3.response.fulfillment_text}")
            else:
                logger.warning("Could not find handler for 'FindEventsNearLocation'.")
        except Exception as e:
            logger.error(f"Error during conceptual handler test: {e}", exc_info=True)
            logger.warning("(This test might fail if SDK components are not fully available or are mocked differently)")
    else:
        logger.info("Skipping conceptual handler test because ADK_SDK_AVAILABLE is True (real SDK might be present).")

    logger.info("End of main block.")
