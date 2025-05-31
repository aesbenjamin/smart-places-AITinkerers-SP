import unittest
from unittest.mock import MagicMock # Not strictly needed if not mocking methods on instances
import sys
import os
import logging

# Adjust sys.path to allow imports from the parent directory (project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from agents.cultural_agent import (
    WelcomeHandler,
    FindEventsHandler,
    FindEventsNearLocationHandler,
    SHARED_MOCK_EVENTS, # Using the same mock data as the handlers
    types as MockAgentTypes # This is how the mock types are structured in cultural_agent.py
)

class TestAgentHandlers(unittest.TestCase):

    def test_welcome_handler(self):
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="welcome")
        handler = WelcomeHandler(mock_request)
        handler.handle()
        self.assertEqual(handler.response.fulfillment_text, "Bem-vindo ao Agente Cultural de São Paulo! Como posso ajudar?")

    def test_find_events_handler_by_type_and_date(self):
        params = {'eventType': "Música", 'date': "2024-09-15"}
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=params)
        handler = FindEventsHandler(mock_request)
        handler.handle()
        expected_titles = ["Concerto de Jazz no Parque"] # Based on SHARED_MOCK_EVENTS
        self.assertIn(f"Encontrei 1 eventos do tipo 'Música' para a data 2024-09-15: {expected_titles[0]}.", handler.response.fulfillment_text)

    def test_find_events_handler_by_type_only(self):
        params = {'eventType': "Oficina"}
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=params)
        handler = FindEventsHandler(mock_request)
        handler.handle()
        # Expecting "Oficina de Impressão 3D no FabLab"
        self.assertIn("Encontrei 1 eventos do tipo 'Oficina': Oficina de Impressão 3D no FabLab.", handler.response.fulfillment_text)

    def test_find_events_handler_by_date_only(self):
        params = {'date': "2024-09-20"}
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=params)
        handler = FindEventsHandler(mock_request)
        handler.handle()
        # Expecting "Exposição Fotográfica 'Olhares Urbanos'" and "Curso de Pintura Aquarela"
        self.assertIn("Encontrei 2 eventos para a data 2024-09-20: Exposição Fotográfica 'Olhares Urbanos'; Curso de Pintura Aquarela.", handler.response.fulfillment_text)

    def test_find_events_handler_no_params(self):
        # Current mock logic returns all events if no params
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters={})
        handler = FindEventsHandler(mock_request)
        handler.handle()
        self.assertIn(f"Encontrei {len(SHARED_MOCK_EVENTS)} eventos: ", handler.response.fulfillment_text)

    def test_find_events_handler_no_results(self):
        params = {'eventType': "Ballet", 'date': "2025-01-01"}
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsByTypeDate", parameters=params)
        handler = FindEventsHandler(mock_request)
        handler.handle()
        self.assertEqual(handler.response.fulfillment_text, "Desculpe, não encontrei eventos do tipo 'Ballet' para a data 2025-01-01. Gostaria de tentar outra busca?")

    def test_find_events_near_location_handler_success(self):
        params = {'location': "Vila Mariana"} # Matches "Praça da Vila Mariana"
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=params)
        handler = FindEventsNearLocationHandler(mock_request)
        handler.handle()
        self.assertEqual(handler.response.fulfillment_text, "Encontrei 1 eventos perto de 'Vila Mariana': Feira de Artesanato da Vila Mariana.")

    def test_find_events_near_location_handler_partial_match(self):
        params = {'location': "Centro"} # Matches "FabLab Centro"
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=params)
        handler = FindEventsNearLocationHandler(mock_request)
        handler.handle()
        self.assertEqual(handler.response.fulfillment_text, "Encontrei 1 eventos perto de 'Centro': Oficina de Impressão 3D no FabLab.")

    def test_find_events_near_location_handler_no_location_param(self):
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsNearLocation", parameters={})
        handler = FindEventsNearLocationHandler(mock_request)
        handler.handle()
        self.assertEqual(handler.response.fulfillment_text, "Por favor, especifique um local para que eu possa encontrar eventos próximos.")

    def test_find_events_near_location_handler_no_results(self):
        params = {'location': "Atlantis"}
        mock_request = MockAgentTypes.AgentRequest(intent_display_name="FindEventsNearLocation", parameters=params)
        handler = FindEventsNearLocationHandler(mock_request)
        handler.handle()
        self.assertEqual(handler.response.fulfillment_text, "Desculpe, não encontrei eventos perto de 'Atlantis'. Gostaria de tentar outro local?")


if __name__ == '__main__':
    logging.disable(logging.CRITICAL)
    try:
        unittest.main()
    finally:
        logging.disable(logging.NOTSET)
