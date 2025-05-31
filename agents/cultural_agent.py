# agents/cultural_agent.py

# This file defines the main cultural agent application using the Agent Development Kit (ADK).
# It sets up intent handlers and registers them with the agent application.

# Note: The exact import paths for 'agent_application' and 'IntentHandler'
# might vary based on the specific version or structure of the ADK provided.
# This implementation is based on common patterns found in ADK examples like goo.gle/ice-cream-agent-code.
try:
    from agent_sdk import agent_application, IntentHandler, types
    # types might be needed for specific request/response objects if the SDK uses them.
    # For a simple text response, it might not be strictly necessary.
except ImportError:
    # Provide a fallback mock if the SDK is not available in the environment,
    # to allow for basic script execution without the full ADK.
    print("Warning: agent_sdk not found. Using mock objects for IntentHandler and agent_application.")

    # Mock types if not available - to be used by mock request/response
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
            self.session_state = {} # Or appropriate session object

    class types: # Keep this class to group mock types
        AgentRequest = MockAgentRequest
        AgentResponse = MockAgentResponse
        # Add other necessary mocked types if your handlers use them.

    class IntentHandler:
        def __init__(self, request: types.AgentRequest): # Use the mock type
            self.request = request
            self.response = types.AgentResponse()

        def handle(self):
            pass # To be implemented by subclasses

    class AgentApplication:
        def __init__(self):
            self.handlers = {}
            print("Mock AgentApplication created.")

        def add_intent_handler(self, intent_name, handler_class):
            self.handlers[intent_name] = handler_class
            print(f"Mock: Registered {handler_class.__name__} for intent '{intent_name}'")

        def run(self, port=8080): # Mock run method
            print(f"Mock AgentApplication 'running' (handlers registered: {list(self.handlers.keys())})")
            # In a real ADK, this would start a server or entry point.

# Define Intent Handlers:
# Each handler is responsible for processing a specific intent.

class WelcomeHandler(IntentHandler):
    """
    Handles the 'Welcome' intent, typically triggered when a user starts interacting
    with the agent.
    """
    def handle(self):
        """
        Sets a greeting message as the response.
        """
        print("WelcomeHandler: Handling intent.")
        self.response.fulfillment_text = "Bem-vindo ao Agente Cultural de São Paulo! Como posso ajudar?"
        # In a more complex scenario, you might set session parameters or cards here.
        # Example: self.response.session_state.params["last_handler"] = "WelcomeHandler"
        print(f"WelcomeHandler: Response set to: '{self.response.fulfillment_text}'")


# To add more intent handlers:
# 1. Define a new class that inherits from IntentHandler.
#    e.g., class EventSearchHandler(IntentHandler):
# 2. Implement the `handle(self)` method within that class to process the intent
#    and set the appropriate response using `self.response.fulfillment_text = "..."`
#    or other response fields.
# 3. Register the new handler with the application instance below, associating it
#    with the corresponding intent name from your Dialogflow CX agent (or other NLU).
#    e.g., app.add_intent_handler("search_event", EventSearchHandler)


# --- Mock Event Data ---
# Shared mock event data for handlers to use.
# In a real scenario, this data would come from scraper functions.
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
    """
    Handles intents related to finding events, potentially filtered by type and date.
    Example intent name: "FindEventsByTypeDate"
    """
    def handle(self):
        """
        Extracts parameters, fetches (mock) event data, filters it, and formats a response.
        """
        print("FindEventsHandler: Handling intent.")

        # 1. Extract parameters from the request
        # These parameter names ('eventType', 'date') should match what's defined
        # in your Dialogflow CX intent or other NLU.
        # The ADK request object (self.request) would provide methods to get these.
        # Example: event_type = self.request.get_parameter('eventType')
        #          event_date = self.request.get_parameter('date') # Assuming date is a string like "2024-08-17"

        # Using the mock get_parameter method
        event_type_param = self.request.get_parameter('eventType') # e.g., "Exposição", "Música"
        date_param = self.request.get_parameter('date') # e.g., "2024-09-15", "hoje", "amanhã"

        print(f"FindEventsHandler: Extracted parameters: eventType='{event_type_param}', date='{date_param}'")

        # 2. Fetch event data
        # In a real implementation, this is where you would call your scraper functions.
        # from scrapers.fablab_scraper import scrape_fablab_events
        # from scrapers.cultura_sp_scraper import scrape_cultura_sp_events # (which is currently mock)
        #
        # print("FindEventsHandler: Simulating calls to scraper functions...")
        # fablab_events = scrape_fablab_events()
        # cultura_sp_events = scrape_cultura_sp_events() # This will return mock data
        # all_events = fablab_events + cultura_sp_events

        # For this mock handler, using the shared predefined list of diverse events:
        current_events = SHARED_MOCK_EVENTS
        # In a real scenario, you'd also normalize date_param (e.g., "hoje" to actual date)
        # For this mock, we'll assume date_param is either None or a string "YYYY-MM-DD".

        # 3. Filter events based on parameters
        filtered_events = []
        if not event_type_param and not date_param:
            # No filters provided, could return some popular events or a prompt to specify
            # For now, let's return a few upcoming events if no filters.
            # This part would need more sophisticated logic in a real agent.
            # filtered_events = sorted(current_events, key=lambda x: x['date'])[:3] # Example: first 3 by date
            print("FindEventsHandler: No specific filters provided by user. Placeholder: returning all mock events for now.")
            filtered_events = current_events # For simplicity in mock
        else:
            for event in current_events:
                match_type = True
                match_date = True

                if event_type_param:
                    # Simple case-insensitive category match for mock.
                    # Real NLU might provide a canonical event type.
                    if event_type_param.lower() not in event['category'].lower():
                        match_type = False

                if date_param:
                    # Simple date string match for mock.
                    # Real date handling is more complex (ranges, "hoje", "amanhã", etc.)
                    if date_param != event['date']:
                        match_date = False

                if match_type and match_date:
                    filtered_events.append(event)

        print(f"FindEventsHandler: Found {len(filtered_events)} events after filtering.")

        # 4. Format the response
        if filtered_events:
            event_titles = [event['title'] for event in filtered_events]
            response_text = f"Encontrei {len(filtered_events)} eventos"
            if event_type_param:
                response_text += f" do tipo '{event_type_param}'"
            if date_param:
                response_text += f" para a data {date_param}"
            response_text += f": {'; '.join(event_titles)}."
            # For more detail, could add: "Quer saber mais sobre algum deles?"
        else:
            response_text = "Desculpe, não encontrei eventos"
            if event_type_param:
                response_text += f" do tipo '{event_type_param}'"
            if date_param:
                response_text += f" para a data {date_param}"
            response_text += ". Gostaria de tentar outra busca?"

        self.response.fulfillment_text = response_text
        print(f"FindEventsHandler: Response set to: '{self.response.fulfillment_text}'")


class FindEventsNearLocationHandler(IntentHandler):
    """
    Handles intents related to finding events near a specified location.
    Example intent name: "FindEventsNearLocation"
    """
    def handle(self):
        """
        Extracts location parameter, simulates geocoding (mock), fetches event data (mock),
        filters by mock location, and formats a response.
        """
        print("FindEventsNearLocationHandler: Handling intent.")

        # 1. Extract location parameter
        location_query = self.request.get_parameter('location') # e.g., "Vila Mariana", "Avenida Paulista"
        print(f"FindEventsNearLocationHandler: Extracted location_query='{location_query}'")

        if not location_query:
            self.response.fulfillment_text = "Por favor, especifique um local para que eu possa encontrar eventos próximos."
            print(f"FindEventsNearLocationHandler: Response set to: '{self.response.fulfillment_text}' (no location provided)")
            return

        # 2. Geocode the location query (Simulated)
        # In a real implementation, this is where you would call:
        # from utils.maps import get_geocode
        # GOOGLE_API_KEY = "YOUR_KEY_FROM_CONFIG" # Load this securely
        # geocoded_location = get_geocode(GOOGLE_API_KEY, location_query)
        # For this mock, we'll just use the location_query string directly for filtering,
        # or simulate a geocode result if we wanted to test lat/lon logic later.
        print(f"FindEventsNearLocationHandler: Simulating geocoding for '{location_query}'.")
        # Mock geocoded_location (not used in current simple filter, but for future reference):
        # if "vila mariana" in location_query.lower():
        #     mock_lat_lng = {'latitude': -23.5870, 'longitude': -46.6330}
        # else:
        #     mock_lat_lng = None

        # 3. Fetch event data (using shared mock data)
        current_events = SHARED_MOCK_EVENTS

        # 4. Filter events based on the mock location query
        # This is a very basic string containment check for mock purposes.
        # A real implementation would use the geocoded_location (lat/lng)
        # and compare with event lat/lng, calculating distances.
        filtered_events = []
        location_query_lower = location_query.lower()
        for event in current_events:
            if location_query_lower in event.get('location', '').lower():
                filtered_events.append(event)

        print(f"FindEventsNearLocationHandler: Found {len(filtered_events)} events containing '{location_query}' in their location string.")

        # 5. Format the response
        if filtered_events:
            event_titles = [event['title'] for event in filtered_events]
            response_text = f"Encontrei {len(filtered_events)} eventos perto de '{location_query}': {'; '.join(event_titles)}."
        else:
            response_text = f"Desculpe, não encontrei eventos perto de '{location_query}'. Gostaria de tentar outro local?"

        self.response.fulfillment_text = response_text
        print(f"FindEventsNearLocationHandler: Response set to: '{self.response.fulfillment_text}'")


# Create the Agent Application instance
# This application will manage all the intent handlers.
ADK_SDK_AVAILABLE = 'agent_application' in globals()

if ADK_SDK_AVAILABLE:
    app = agent_application.AgentApplication()
else:
    # Use the mock class directly if SDK is not available
    app = AgentApplication()


# Register Intent Handlers
# Map intent names (as defined in your NLU/Dialogflow CX) to their handler classes.
app.add_intent_handler("DefaultWelcomeIntent", WelcomeHandler) # Standard Dialogflow Welcome Intent
app.add_intent_handler("welcome", WelcomeHandler) # A common custom welcome intent name
app.add_intent_handler("FindEventsByTypeDate", FindEventsHandler)
app.add_intent_handler("FindEventsNearLocation", FindEventsNearLocationHandler) # Register the new handler


# The main execution block for the agent.
# In a real ADK deployment, this script might be invoked by a server (like gunicorn or uvicorn)
# or the ADK might provide its own command-line tools to run the agent.
# This block demonstrates how the application could be started if the SDK supports a local run.
if __name__ == '__main__':
    print("Cultural Agent Application - Main Block")
    print("This script defines the agent handlers and application.")

    # The following 'app.run()' is conceptual for local testing if the SDK supports it directly.
    # In many ADK scenarios, you deploy this application to a cloud environment,
    # and it's run by the ADK's serving infrastructure.
    # If the SDK has a local development server, this is where you'd start it.

    # For example, if the SDK provides a simple run method:
    # if hasattr(app, 'run') and callable(getattr(app, 'run')):
    #     print("Attempting to 'run' the agent application (mock or real)...")
    #     try:
    #         # Some ADKs might take the script itself or specific arguments.
    #         # This is a generic placeholder.
    #         app.run() # Or app.run(port=8080) or similar
    #     except Exception as e:
    #         print(f"Error trying to run app: {e}")
    #         print("This might be normal if the SDK expects a different execution environment.")
    # else:
    #     print("Agent application created but no direct 'run' method found or SDK not fully available.")
    #     print("Registered handlers in mock/real app:", app.handlers if hasattr(app, 'handlers') else "N/A")

    # For now, just confirming instantiation and handler registration (especially if using mocks)
    if (ADK_SDK_AVAILABLE and isinstance(app, agent_application.AgentApplication)) or \
       (not ADK_SDK_AVAILABLE and isinstance(app, AgentApplication)): # checks mock too
        print("AgentApplication instantiated successfully.")
        if hasattr(app, 'handlers'): # Check for mocked or real handlers attribute
             print(f"Registered handlers: {app.handlers}")
        elif hasattr(app, '_name_to_handler_map'): # Common in some Google ADK versions
            print(f"Registered handlers (from _name_to_handler_map): {app._name_to_handler_map}")

    # To actually test intent handling locally without a full ADK server,
    # you might need to simulate a request object and call a handler directly.
    # Example (conceptual, depends on SDK's request/response structure):
    print("\n--- Conceptual Handler Test ---")
    if not ADK_SDK_AVAILABLE: # Only run mock test if actual SDK is not present
        print("Running conceptual test with MOCK request for 'FindEventsByTypeDate'...")
        try:
            # Test case 1: With parameters
            mock_params_case1 = {'eventType': "Música", 'date': "2024-09-15"}
            mock_request_case1 = types.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=mock_params_case1)

            handler_class_case1 = app.handlers.get("FindEventsByTypeDate")
            if handler_class_case1:
                print(f"\nTesting FindEventsByTypeDate with params: {mock_params_case1}")
                handler_instance_case1 = handler_class_case1(mock_request_case1)
                handler_instance_case1.handle()
                print(f"Response: {handler_instance_case1.response.fulfillment_text}")
            else:
                print("Could not find handler for 'FindEventsByTypeDate'.")

            # Test case 2 for FindEventsByTypeDate: No parameters (or only one)
            mock_params_case2 = {'eventType': "Exposição"}
            mock_request_case2 = types.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=mock_params_case2)
            if handler_class_case1: # Reusing handler_class_case1 as it's the same class
                print(f"\nTesting FindEventsByTypeDate with params: {mock_params_case2}")
                handler_instance_case2 = handler_class_case1(mock_request_case2)
                handler_instance_case2.handle()
                print(f"Response: {handler_instance_case2.response.fulfillment_text}")

            # Test case 3 for FindEventsByTypeDate: No matching events
            mock_params_case3 = {'eventType': "Dança", 'date': "2024-01-01"}
            mock_request_case3 = types.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=mock_params_case3)
            if handler_class_case1:
                print(f"\nTesting FindEventsByTypeDate with params: {mock_params_case3} (expected no match)")
                handler_instance_case3 = handler_class_case1(mock_request_case3)
                handler_instance_case3.handle()
                print(f"Response: {handler_instance_case3.response.fulfillment_text}")

            print("\n--- Testing FindEventsNearLocationHandler ---")
            handler_class_loc = app.handlers.get("FindEventsNearLocation")
            if handler_class_loc:
                # Test case 1: Location provided
                mock_loc_params1 = {'location': "Vila Mariana"}
                mock_loc_request1 = types.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=mock_loc_params1)
                print(f"\nTesting FindEventsNearLocation with params: {mock_loc_params1}")
                handler_loc_instance1 = handler_class_loc(mock_loc_request1)
                handler_loc_instance1.handle()
                print(f"Response: {handler_loc_instance1.response.fulfillment_text}")

                # Test case 2: Location that doesn't match any mock event
                mock_loc_params2 = {'location': "Jardins"}
                mock_loc_request2 = types.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=mock_loc_params2)
                print(f"\nTesting FindEventsNearLocation with params: {mock_loc_params2} (expected no match)")
                handler_loc_instance2 = handler_class_loc(mock_loc_request2)
                handler_loc_instance2.handle()
                print(f"Response: {handler_loc_instance2.response.fulfillment_text}")

                # Test case 3: No location parameter
                mock_loc_params3 = {}
                mock_loc_request3 = types.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=mock_loc_params3)
                print(f"\nTesting FindEventsNearLocation with params: {mock_loc_params3} (no location)")
                handler_loc_instance3 = handler_class_loc(mock_loc_request3)
                handler_loc_instance3.handle()
                print(f"Response: {handler_loc_instance3.response.fulfillment_text}")
            else:
                print("Could not find handler for 'FindEventsNearLocation'.")

        except Exception as e:
            print(f"Error during conceptual handler test: {e}")
            import traceback
            traceback.print_exc()
            print("(This test might fail if SDK components are not fully available or are mocked differently)")
    else:
        print("Skipping conceptual handler test because ADK_SDK_AVAILABLE is True (real SDK might be present).")


    print("End of main block.")
