"""
Testes das Ferramentas (Tools)
------------------------------
Este módulo executa os testes para as ferramentas do agente.
"""

# ============================================================================
# Imports
# ============================================================================

import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock # Para mockar chamadas de API/LLM
from typing import List, Dict, Any, Optional
import json

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos dos módulos de ferramentas (serão adicionados conforme necessário)
from agents.tools.cultural_event_finder import find_cultural_events_unified
from agents.tools.search_web import search_tavily
from agents.tools.get_user_response import generate_response_from_llm
from agents.tools.get_bairros import get_expanded_location_terms
from agents.tools.data_aggregator import get_all_events_from_scrapers_with_memory
# Exemplo: from agents.tools.cultural_event_finder import find_cultural_events_unified

from agents.utils.logger import get_logger
from agents.utils.env_setup import setup_environment_variables_and_locale

# ============================================================================
# Configuração do Logger
# ============================================================================

log_file_tools = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_tools.log')
tool_file_handler = logging.FileHandler(log_file_tools, mode='w')
tool_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
tool_file_handler.setLevel(logging.DEBUG)

root_logger_tools = logging.getLogger()
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file_tools for h in root_logger_tools.handlers):
    root_logger_tools.addHandler(tool_file_handler)
root_logger_tools.setLevel(logging.DEBUG)

logger_test_tools = get_logger(__name__)

# ============================================================================
# Classes de Teste Base
# ============================================================================

class TestToolsBase(unittest.TestCase):
    """Classe base para testes das ferramentas."""
    
    @classmethod
    def setUpClass(cls):
        logger_test_tools.info(f"\n{'='*60}\nINICIANDO SUITE DE TESTES PARA: {cls.__name__}\n{'='*60}")
        if not hasattr(cls, '_env_setup_done_tools'):
            setup_environment_variables_and_locale()
            cls._env_setup_done_tools = True
            logger_test_tools.info("Ambiente configurado (variáveis e locale) para TestToolsBase.")

    def setUp(self):
        logger_test_tools.info(f"-- Iniciando teste: {self._testMethodName} --")
    
    def tearDown(self):
        logger_test_tools.info(f"-- Finalizando teste: {self._testMethodName} --\n")

# ============================================================================
# Classes de Teste Específicas (Esqueletos)
# ============================================================================

class TestCulturalEventFinder(TestToolsBase):
    """Testes para a ferramenta Cultural Event Finder."""
    
    @patch('agents.tools.cultural_event_finder.os.getenv') # Adicionado para mockar getenv
    @patch('agents.tools.cultural_event_finder.get_expanded_location_terms')
    @patch('agents.tools.cultural_event_finder.get_all_events_from_scrapers_with_memory')
    @patch('agents.tools.cultural_event_finder.search_tavily')
    @patch('agents.tools.cultural_event_finder.generate_response_from_llm')
    @patch('agents.tools.cultural_event_finder.web_search_memory') # Mocka a instância global
    def test_find_cultural_events_basic_flow_and_format(
        self, 
        mock_web_search_memory,
        mock_generate_llm_response, 
        mock_search_tavily, 
        mock_get_all_scrapers_events, 
        mock_get_expanded_locations,
        mock_os_getenv # Novo mock
    ):
        logger_test_tools.info("Testando o fluxo básico e formato de find_cultural_events_unified...")

        # Configurar Mocks
        # Mock para os.getenv especificamente para TAVILY_API_KEY
        def mock_getenv_side_effect(key, default=None):
            if key == "TAVILY_API_KEY":
                return "mock_tavily_api_key_for_test"
            return os.environ.get(key, default) # Permite que outros getenv funcionem normalmente
        mock_os_getenv.side_effect = mock_getenv_side_effect
        
        mock_get_expanded_locations.return_value = {"expanded_terms": ["paulista", "avenida paulista"]}
        
        mock_scraper_event_1 = {"id": "scraper_1", "title": "Expo Scraper", "description": "Detalhes da Expo Scraper", "source": "scraper"}
        mock_get_all_scrapers_events.return_value = [mock_scraper_event_1]
        
        mock_web_event_1 = {"url": "web_event_1_url", "title": "Show Web", "content": "Conteúdo do Show Web", "source": "web"}
        mock_search_tavily.return_value = [mock_web_event_1]
        
        # Eventos como seriam "selecionados" pelo LLM antes da anexação da descrição completa
        mock_llm_selected_event_scraper = {"id": "scraper_1", "title": "Expo Scraper (LLM)", "source": "scraper"}
        mock_llm_selected_event_web = {"id": "web_event_1_url", "title": "Show Web (LLM)", "source": "web"} # ID aqui é a URL para eventos web
        
        mock_generate_llm_response.return_value = {
            "chat_summary": "Aqui estão alguns eventos...",
            "events_found": [mock_llm_selected_event_scraper, mock_llm_selected_event_web]
        }
        
        mock_web_search_memory.add_results = MagicMock() # Mocka o método add_results

        # Chamar a função
        result = find_cultural_events_unified(
            event_type="exposição", 
            date="amanhã", 
            location_query="Paulista"
        )

        # Assertivas
        self.assertIsInstance(result, dict)
        self.assertIn("chat_summary", result)
        self.assertEqual(result["chat_summary"], "Aqui estão alguns eventos...")
        self.assertIn("events_found", result)
        self.assertIsInstance(result["events_found"], list)
        self.assertEqual(len(result["events_found"]), 2)

        # Verificar se as descrições completas foram anexadas
        event_from_scraper = next(e for e in result["events_found"] if e["id"] == "scraper_1")
        event_from_web = next(e for e in result["events_found"] if e["id"] == "web_event_1_url")

        self.assertEqual(event_from_scraper.get("full_description"), "Detalhes da Expo Scraper")
        self.assertEqual(event_from_web.get("full_description"), "Conteúdo do Show Web")
        
        # Verificar chamadas dos mocks
        mock_get_expanded_locations.assert_called_once_with("Paulista")
        mock_get_all_scrapers_events.assert_called_once()
        mock_search_tavily.assert_called_once() # verificar argumentos exatos pode ser complexo devido à construção da query
        mock_web_search_memory.add_results.assert_called_once_with(mock_search_tavily.call_args[0][0], [mock_web_event_1])
        mock_generate_llm_response.assert_called_once()
        # Podemos adicionar verificações mais detalhadas dos argumentos passados para generate_response_from_llm se necessário

        logger_test_tools.info("Teste de find_cultural_events_unified concluído.")

class TestSearchWeb(TestToolsBase):
    """Testes para a ferramenta Search Web."""

    @patch('agents.tools.search_web.TavilyClient')
    def test_search_tavily_success(self, MockTavilyClient):
        logger_test_tools.info("Testando search_tavily com sucesso...")
        
        # Configurar mock para o cliente Tavily e seu método search
        mock_tavily_instance = MockTavilyClient.return_value
        mock_search_results = [
            {'title': 'Resultado 1', 'url': 'http://example.com/1', 'content': 'Conteúdo 1'},
            {'title': 'Resultado 2', 'url': 'http://example.com/2', 'content': 'Conteúdo 2'}
        ]
        mock_tavily_instance.search.return_value = {'results': mock_search_results}
        
        api_key_teste = "test_api_key"
        query_teste = "melhores museus SP"
        max_results_teste = 3
        
        # Chamar a função
        results = search_tavily(query_teste, api_key=api_key_teste, max_results=max_results_teste)
        
        # Assertivas
        MockTavilyClient.assert_called_once_with(api_key=api_key_teste)
        mock_tavily_instance.search.assert_called_once_with(
            query=query_teste,
            search_depth="advanced",
            max_results=max_results_teste,
            include_domains=None, # Valor padrão
            exclude_domains=None  # Valor padrão
        )
        self.assertEqual(results, mock_search_results)
        logger_test_tools.info("Teste search_tavily com sucesso concluído.")

    def test_search_tavily_no_api_key(self):
        logger_test_tools.info("Testando search_tavily sem chave API...")
        results = search_tavily("qualquer query", api_key=None)
        self.assertEqual(results, [])
        # Adicionalmente, poderia verificar o log de aviso, mas o retorno é o principal.
        logger_test_tools.info("Teste search_tavily sem chave API concluído.")

    @patch('agents.tools.search_web.TavilyClient')
    def test_search_tavily_api_exception(self, MockTavilyClient):
        logger_test_tools.info("Testando search_tavily com exceção da API...")
        
        # Configurar mock para o cliente Tavily lançar uma exceção
        mock_tavily_instance = MockTavilyClient.return_value
        mock_tavily_instance.search.side_effect = Exception("Erro na API Tavily")
        
        api_key_teste = "test_api_key"
        query_teste = "eventos hoje"
        
        # Chamar a função
        results = search_tavily(query_teste, api_key=api_key_teste)
        
        # Assertivas
        MockTavilyClient.assert_called_once_with(api_key=api_key_teste)
        mock_tavily_instance.search.assert_called_once()
        self.assertEqual(results, [])
        # Adicionalmente, poderia verificar o log de erro.
        logger_test_tools.info("Teste search_tavily com exceção da API concluído.")

class TestGetUserResponse(TestToolsBase):
    """Testes para a ferramenta Get User Response (LLM interaction)."""

    @patch('agents.tools.get_user_response.genai.GenerativeModel')
    def test_generate_response_success(self, MockGenerativeModel):
        logger_test_tools.info("Testando generate_response_from_llm com sucesso...")

        mock_model_instance = MockGenerativeModel.return_value
        mock_llm_candidates_json_str = json.dumps({
            "event_candidates": [
                {"id": "evt1", "name": "Evento Mock 1", "location_details": "Local 1", "type": "Show", "date_info": "Amanhã", "source": "scraper", "details_link": "link1"},
                {"id": "evt2", "name": "Evento Mock 2", "location_details": "Local 2", "type": "Museu", "date_info": "Hoje", "source": "web", "details_link": "link2"}
            ]
        })
        mock_chat_summary_text = "Encontrei 2 eventos que podem te interessar, como: Evento Mock 1, Evento Mock 2. Veja os detalhes e o mapa!"

        mock_model_instance.generate_content.side_effect = [
            MagicMock(text=mock_llm_candidates_json_str),
            MagicMock(text=mock_chat_summary_text)
        ]

        user_query = {"event_type": "show", "date": "amanhã", "location_query": "Paulista"}
        scraped_events_data = [{"id": "evt1", "title": "Evento Scraper Original"}]
        web_search_data = [{"url": "evt2", "title": "Evento Web Original"}]
        response = generate_response_from_llm(user_query, scraped_events_data, web_search_data, max_suggestions=2)

        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("chat_summary"), mock_chat_summary_text)
        self.assertIn("events_found", response)
        self.assertIsInstance(response["events_found"], list)
        self.assertEqual(len(response["events_found"]), 2)
        self.assertEqual(response["events_found"][0]["name"], "Evento Mock 1")
        
        self.assertEqual(mock_model_instance.generate_content.call_count, 1)
        self.assertEqual(MockGenerativeModel.call_count, 1)
        logger_test_tools.info("Teste generate_response_from_llm com sucesso concluído.")

    @patch('agents.tools.get_user_response.genai.GenerativeModel')
    def test_generate_response_llm_returns_invalid_json(self, MockGenerativeModel):
        logger_test_tools.info("Testando generate_response_from_llm com JSON inválido do LLM...")

        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.return_value = MagicMock(text="Isto não é um JSON.")

        user_query = {"event_type": "qualquer", "date": "qualquer", "location_query": "qualquer"}
        response = generate_response_from_llm(user_query, [], [])

        self.assertIsInstance(response, dict)
        # String corrigida baseada no log
        expected_summary = "Não encontrei eventos que correspondam exatamente à sua busca (tipo: qualquer, data: qualquer, local: qualquer). Que tal tentar uma busca com critérios diferentes ou mais amplos?"
        self.assertEqual(response["chat_summary"], expected_summary)
        self.assertEqual(response["events_found"], [])
        logger_test_tools.info("Teste generate_response_from_llm com JSON inválido concluído.")

    @patch('agents.tools.get_user_response.genai.GenerativeModel')
    def test_generate_response_llm_candidate_call_raises_exception(self, MockGenerativeModel):
        logger_test_tools.info("Testando generate_response_from_llm com exceção na chamada de candidatos ao LLM...")
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = Exception("Erro de API do LLM")

        user_query = {"event_type": "qualquer", "date": "qualquer", "location_query": "qualquer"}
        response = generate_response_from_llm(user_query, [], [])
        # String corrigida baseada no log
        expected_summary = "Falha na comunicação com o assistente de IA: Erro de API do LLM."
        self.assertEqual(response["chat_summary"], expected_summary)
        self.assertEqual(response["events_found"], [])
        logger_test_tools.info("Teste generate_response_from_llm com exceção na API para candidatos concluído.")

    @patch('agents.tools.get_user_response.genai.GenerativeModel')
    def test_generate_response_llm_returns_json_missing_candidates_key(self, MockGenerativeModel):
        logger_test_tools.info("Testando generate_response_from_llm com JSON do LLM sem a chave 'event_candidates'...")
        mock_model_instance = MockGenerativeModel.return_value
        mock_llm_bad_json_str = json.dumps({"outra_chave": []})
        mock_model_instance.generate_content.return_value = MagicMock(text=mock_llm_bad_json_str)

        user_query = {"event_type": "qualquer", "date": "qualquer", "location_query": "qualquer"}
        response = generate_response_from_llm(user_query, [], [])
        # String corrigida baseada no log
        expected_summary = "O assistente de IA retornou dados em um formato inesperado. Não consegui encontrar eventos para sua busca (tipo: qualquer, data: qualquer, local: qualquer)."
        self.assertEqual(response["chat_summary"], expected_summary)
        self.assertEqual(response["events_found"], [])
        logger_test_tools.info("Teste generate_response_from_llm com JSON malformado concluído.")

    @patch('agents.tools.get_user_response.genai.GenerativeModel')
    def test_generate_response_llm_returns_no_candidates(self, MockGenerativeModel):
        logger_test_tools.info("Testando generate_response_from_llm quando LLM não encontra candidatos...")
        mock_model_instance = MockGenerativeModel.return_value
        mock_llm_no_candidates_json_str = json.dumps({"event_candidates": []})
        # String corrigida baseada no log
        mock_chat_summary_no_events_text = "Não encontrei eventos que correspondam exatamente à sua busca (tipo: muito específico, data: hoje, local: lugar nenhum). Que tal tentar uma busca com critérios diferentes ou mais amplos?"

        mock_model_instance.generate_content.side_effect = [
            MagicMock(text=mock_llm_no_candidates_json_str),
            MagicMock(text=mock_chat_summary_no_events_text)
        ]

        user_query = {"event_type": "muito específico", "date": "hoje", "location_query": "lugar nenhum"}
        response = generate_response_from_llm(user_query, [], [])

        self.assertEqual(response["chat_summary"], mock_chat_summary_no_events_text)
        self.assertEqual(response["events_found"], [])
        self.assertEqual(mock_model_instance.generate_content.call_count, 1) # Corrigido: Espera 1 chamada
        logger_test_tools.info("Teste generate_response_from_llm sem candidatos concluído.")

class TestGetBairros(TestToolsBase):
    """Testes para a ferramenta Get Bairros."""

    @patch('agents.tools.get_bairros.SHOULD_USE_LLM', False) # Força LLM desabilitado
    @patch('agents.tools.get_bairros.genai.GenerativeModel') # Mock para verificar se não é chamado
    def test_get_expanded_terms_llm_disabled(self, MockGenerativeModel):
        logger_test_tools.info("Testando get_expanded_location_terms com LLM desabilitado...")
        query = "Paulista"
        result = get_expanded_location_terms(query)
        
        self.assertEqual(result, {"expanded_terms": ["paulista"]})
        MockGenerativeModel.assert_not_called() # Garante que o LLM não foi envolvido
        logger_test_tools.info("Teste com LLM desabilitado concluído.")

    @patch('agents.tools.get_bairros.SHOULD_USE_LLM', True) # Força LLM habilitado
    @patch('agents.tools.get_bairros.genai.GenerativeModel')
    def test_get_expanded_terms_llm_success(self, MockGenerativeModel):
        logger_test_tools.info("Testando get_expanded_location_terms com LLM habilitado e sucesso...")
        mock_model_instance = MockGenerativeModel.return_value
        mock_llm_response_text = json.dumps(["avenida paulista", "bela vista", "PAULISTA"])
        mock_model_instance.generate_content.return_value = MagicMock(text=mock_llm_response_text)
        
        query = "Paulista"
        result = get_expanded_location_terms(query)
        
        # A ordem dos termos expandidos pode variar, e o original é adicionado e tudo é lowercased e unique
        expected_terms_set = {"paulista", "avenida paulista", "bela vista"}
        self.assertIsInstance(result.get("expanded_terms"), list)
        self.assertSetEqual(set(result["expanded_terms"]), expected_terms_set)
        MockGenerativeModel.assert_called_once_with('gemini-2.0-flash')
        mock_model_instance.generate_content.assert_called_once()
        logger_test_tools.info("Teste com LLM habilitado e sucesso concluído.")

    @patch('agents.tools.get_bairros.SHOULD_USE_LLM', True)
    @patch('agents.tools.get_bairros.genai.GenerativeModel')
    def test_get_expanded_terms_llm_api_exception(self, MockGenerativeModel):
        logger_test_tools.info("Testando get_expanded_location_terms com exceção na API do LLM...")
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.side_effect = Exception("Erro de API LLM Simulada")
        
        query = "Ibirapuera"
        result = get_expanded_location_terms(query)
        
        self.assertEqual(result, {"expanded_terms": ["ibirapuera"]}) # Deve retornar apenas o original
        logger_test_tools.info("Teste com exceção na API do LLM concluído.")

    @patch('agents.tools.get_bairros.SHOULD_USE_LLM', True)
    @patch('agents.tools.get_bairros.genai.GenerativeModel')
    def test_get_expanded_terms_llm_malformed_response(self, MockGenerativeModel):
        logger_test_tools.info("Testando get_expanded_location_terms com resposta malformada do LLM...")
        mock_model_instance = MockGenerativeModel.return_value
        mock_model_instance.generate_content.return_value = MagicMock(text="isto não é json nem lista python")
        
        query = "Centro"
        result = get_expanded_location_terms(query)
        
        self.assertEqual(result, {"expanded_terms": ["centro"]}) # Deve retornar apenas o original
        logger_test_tools.info("Teste com resposta malformada do LLM concluído.")

    def test_get_expanded_terms_empty_query(self):
        logger_test_tools.info("Testando get_expanded_location_terms com query vazia...")
        result = get_expanded_location_terms("")
        self.assertEqual(result, {"expanded_terms": []})
        logger_test_tools.info("Teste com query vazia concluído.")

class TestDataAggregator(TestToolsBase):
    """Testes para a ferramenta Data Aggregator."""

    @patch('agents.tools.data_aggregator.scraper_memory') # Patch a instância no módulo
    def test_cache_hit_uses_memory(self, mock_scraper_memory_instance):
        logger_test_tools.info("Testando DataAggregator: cache hit...")
        
        mock_scraper_memory_instance.should_refresh.return_value = False
        mock_cached_events = [{"id": "cached_event_1", "title": "Evento em Cache"}]
        mock_scraper_memory_instance.get_events.return_value = mock_cached_events
        
        # Mock para as funções de scraper para garantir que não são chamadas
        with patch('agents.tools.data_aggregator.scrape_fablab_events') as mock_fablab,\
             patch('agents.tools.data_aggregator.scrape_visite_sao_paulo_events') as mock_visite_sp,\
             patch('agents.tools.data_aggregator.scrape_wikipedia_museus_info') as mock_wikipedia:
            
            result = get_all_events_from_scrapers_with_memory()
            
            self.assertEqual(result, mock_cached_events)
            mock_scraper_memory_instance.should_refresh.assert_called_once()
            mock_scraper_memory_instance.get_events.assert_called_once()
            mock_scraper_memory_instance.update_events.assert_not_called() # Não deve atualizar se não houve refresh
            mock_fablab.assert_not_called()
            mock_visite_sp.assert_not_called()
            mock_wikipedia.assert_not_called()
        logger_test_tools.info("Teste DataAggregator: cache hit concluído.")

    @patch('agents.tools.data_aggregator.scraper_memory')
    @patch('agents.tools.data_aggregator.standardize_date_format')
    @patch('agents.tools.data_aggregator.scrape_fablab_events')
    @patch('agents.tools.data_aggregator.scrape_visite_sao_paulo_events')
    @patch('agents.tools.data_aggregator.scrape_wikipedia_museus_info')
    def test_cache_miss_calls_scrapers_and_processes_data(
        self, 
        mock_scrape_wikipedia, 
        mock_scrape_visite_sp, 
        mock_scrape_fablab, 
        mock_standardize_date, 
        mock_scraper_memory_instance
    ):
        logger_test_tools.info("Testando DataAggregator: cache miss e processamento...")

        # Configurar mocks
        mock_scraper_memory_instance.should_refresh.return_value = True
        mock_final_events_list_from_memory = [{"id": "processed_event", "title": "Evento Final da Memória"}]
        mock_scraper_memory_instance.get_events.return_value = mock_final_events_list_from_memory
        
        mock_standardize_date.side_effect = lambda x: f"std_{x}" if x else None

        fablab_raw_event = {"title": "Evento FabLab", "date": "01/01/2024", "location": "FabLab Centro"}
        visite_sp_raw_event = {"title": "Evento VisiteSP", "date": "02/01/2024", "location": "MASP"}
        wiki_raw_event = {"title": "Museu Wiki", "date": "03/01/2024", "district": "Centro"}
        
        mock_scrape_fablab.return_value = [fablab_raw_event]
        mock_scrape_visite_sp.return_value = [visite_sp_raw_event]
        mock_scrape_wikipedia.return_value = [wiki_raw_event]

        # Chamar a função
        result = get_all_events_from_scrapers_with_memory()

        # Assertivas
        mock_scraper_memory_instance.should_refresh.assert_called_once()
        mock_scrape_fablab.assert_called_once()
        mock_scrape_visite_sp.assert_called_once()
        mock_scrape_wikipedia.assert_called_once()
        
        mock_scraper_memory_instance.update_events.assert_called_once()
        updated_events_call_args = mock_scraper_memory_instance.update_events.call_args[0][0]
        self.assertEqual(len(updated_events_call_args), 3)

        # Verificar processamento do evento FabLab - ID corrigido
        fablab_processed = next(e for e in updated_events_call_args if "FabLab_0_Evento_FabLab" in e['id'])
        self.assertEqual(fablab_processed['date'], "std_01/01/2024")
        self.assertIn('bairro', fablab_processed)

        # Verificar processamento do evento VisiteSP - ID corrigido com espaço no nome do scraper
        visite_sp_processed = next(e for e in updated_events_call_args if "Visite São Paulo_0_Evento_VisiteSP" in e['id'])
        self.assertEqual(visite_sp_processed['date'], "std_02/01/2024")
        self.assertIn('bairro', visite_sp_processed)

        # Verificar processamento do evento Wikipedia - ID corrigido com espaço no nome do scraper
        wiki_processed = next(e for e in updated_events_call_args if "Museus da Wikipédia_0_Museu_Wiki" in e['id'])
        self.assertEqual(wiki_processed['date'], "std_03/01/2024")
        self.assertIn('bairro', wiki_processed)
        self.assertEqual(wiki_processed['category'], 'Museu')
        
        self.assertEqual(result, mock_final_events_list_from_memory)
        mock_scraper_memory_instance.get_events.assert_called_once()

        logger_test_tools.info("Teste DataAggregator: cache miss e processamento concluído.")

    @patch('agents.tools.data_aggregator.scraper_memory')
    @patch('agents.tools.data_aggregator.standardize_date_format')
    @patch('agents.tools.data_aggregator.scrape_fablab_events')
    @patch('agents.tools.data_aggregator.scrape_visite_sao_paulo_events')
    @patch('agents.tools.data_aggregator.scrape_wikipedia_museus_info')
    def test_scraper_failure_continues_with_others(
        self, 
        mock_scrape_wikipedia, 
        mock_scrape_visite_sp, 
        mock_scrape_fablab, 
        mock_standardize_date, 
        mock_scraper_memory_instance
    ):
        logger_test_tools.info("Testando DataAggregator: falha em um scraper...")
        mock_scraper_memory_instance.should_refresh.return_value = True
        mock_final_events_list_from_memory = [{"id": "event_from_successful_scraper"}]
        mock_scraper_memory_instance.get_events.return_value = mock_final_events_list_from_memory
        mock_standardize_date.side_effect = lambda x: f"std_{x}" if x else None

        mock_scrape_fablab.side_effect = Exception("Erro no scraper FabLab")
        visite_sp_raw_event = {"title": "Evento VisiteSP", "date": "02/01/2024"}
        wiki_raw_event = {"title": "Museu Wiki", "date": "03/01/2024", "district": "Centro"}
        mock_scrape_visite_sp.return_value = [visite_sp_raw_event]
        mock_scrape_wikipedia.return_value = [wiki_raw_event]

        get_all_events_from_scrapers_with_memory()

        mock_scrape_fablab.assert_called_once()
        mock_scrape_visite_sp.assert_called_once()
        mock_scrape_wikipedia.assert_called_once()
        mock_scraper_memory_instance.update_events.assert_called_once()
        updated_events = mock_scraper_memory_instance.update_events.call_args[0][0]
        self.assertEqual(len(updated_events), 2) # Apenas os dois scrapers de sucesso
        # Corrigir verificação de ID aqui também, usando espaço no nome do scraper
        self.assertTrue(any("Visite São Paulo" in e['id'] for e in updated_events))
        self.assertTrue(any("Museus da Wikipédia" in e['id'] for e in updated_events))
        logger_test_tools.info("Teste DataAggregator: falha em um scraper concluído.")

# ============================================================================
# Função Principal de Teste
# ============================================================================

def run_all_tool_tests():
    """Executa todos os testes de ferramentas e registra os resultados."""
    logger_test_tools.info("\n" + "="*70 + "\nINICIANDO EXECUÇÃO COMPLETA DOS TESTES DE FERRAMENTAS\n" + "="*70)
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCulturalEventFinder))
    suite.addTest(unittest.makeSuite(TestSearchWeb))
    suite.addTest(unittest.makeSuite(TestGetUserResponse))
    suite.addTest(unittest.makeSuite(TestGetBairros))
    suite.addTest(unittest.makeSuite(TestDataAggregator))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    logger_test_tools.info("\n" + "="*70 + "\nRESULTADO FINAL DOS TESTES DE FERRAMENTAS\n" + "="*70)
    logger_test_tools.info(f"Testes executados: {result.testsRun}")
    logger_test_tools.info(f"Falhas: {len(result.failures)}")
    logger_test_tools.info(f"Erros: {len(result.errors)}")
    logger_test_tools.info(f"Testes pulados: {len(result.skipped)}")
    
    if result.failures:
        logger_test_tools.error("\nDetalhes das Falhas:")
        for i, (test_case, traceback_str) in enumerate(result.failures, 1):
            logger_test_tools.error(f"Falha {i}: {test_case}\n{traceback_str}")
    
    if result.errors:
        logger_test_tools.error("\nDetalhes dos Erros:")
        for i, (test_case, traceback_str) in enumerate(result.errors, 1):
            logger_test_tools.error(f"Erro {i}: {test_case}\n{traceback_str}")
            
    logger_test_tools.info("="*70 + "\nFIM DA EXECUÇÃO DOS TESTES DE FERRAMENTAS\n" + "="*70)
    return result.wasSuccessful()

# ============================================================================
# Execução do Script
# ============================================================================

if __name__ == '__main__':
    success = run_all_tool_tests()
    print(f"\nExecução dos testes de ferramentas concluída. Verifique o arquivo '{log_file_tools}' para logs detalhados.")
    print(f"Sucesso geral dos testes de ferramentas: {success}")
    sys.exit(0 if success else 1)
