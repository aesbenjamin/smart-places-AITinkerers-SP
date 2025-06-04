"""
Localizador de Eventos Culturais
-------------------------------
Este módulo implementa um sistema unificado para busca de eventos culturais,
museus e atividades de lazer em São Paulo, integrando dados de scrapers locais
e busca na web (Tavily) para fornecer recomendações relevantes.
"""

# ============================================================================
# Imports
# ============================================================================

import sys
import os
from typing import Optional, Dict, Any
import logging

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos
from agents.tools.search_web import search_tavily
from agents.tools.get_bairros import get_expanded_location_terms
from agents.tools.get_user_response import generate_response_from_llm
from agents.tools.data_aggregator import get_all_events_from_scrapers_with_memory
from agents.state.macro_state import WebSearchMemory

# ============================================================================
# Configuração do Logger
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# Configurações e Constantes
# ============================================================================

# Memória para buscas na web, gerenciada dentro deste módulo
web_search_memory = WebSearchMemory()

# ============================================================================
# Funções Principais
# ============================================================================

def find_cultural_events_unified(
    event_type: Optional[str] = None,
    date: Optional[str] = None,
    location_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Busca eventos culturais, museus e atividades de lazer em São Paulo.

    Esta ferramenta integra dados de scrapers locais e busca na web (Tavily)
    para encontrar opções relevantes. Em seguida, utiliza um modelo de linguagem
    para analisar os resultados e compilar uma lista de sugestões, juntamente
    com um resumo para o chat. A ferramenta também anexa descrições completas
    aos eventos encontrados.

    Args:
        event_type (Optional[str]): O tipo de evento ou interesse do usuário
        date (Optional[str]): A data ou período de interesse
        location_query (Optional[str]): A localização de interesse

    Returns:
        Dict[str, Any]: Dicionário contendo "chat_summary" e "events_found"
    """
    logger.info(f"Cultural Event Finder: find_cultural_events_unified invocada com: tipo='{event_type}', data='{date}', local='{location_query}'")
    
    # Expande termos de localização usando get_expanded_location_terms
    expanded_locations = []
    if location_query:
        logger.info(f"Expandindo termos de localização para: '{location_query}'")
        try:
            expanded_terms_dict = get_expanded_location_terms(location_query)
            expanded_locations_list = expanded_terms_dict.get("expanded_terms", [])
            if isinstance(expanded_locations_list, list) and expanded_locations_list:
                expanded_locations = [str(term).lower() for term in expanded_locations_list if term]
                logger.info(f"Termos de localização expandidos de '{location_query}' para {expanded_locations}.")
            else:
                logger.warning(f"Não foram retornados termos expandidos válidos para '{location_query}'.")
        except Exception as e:
            logger.error(f"Erro ao expandir termos de localização para '{location_query}': {e}.")
    
    # Coleta dados dos scrapers usando get_all_events_from_scrapers_with_memory
    logger.info("Coletando todos os eventos e informações de museus (via data_aggregator)...")
    all_event_data = get_all_events_from_scrapers_with_memory()
    logger.info(f"Total de {len(all_event_data)} itens carregados via data_aggregator.")
    
    # Realiza busca na web usando search_tavily
    web_search_data = []
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    if tavily_api_key and (location_query or event_type or date):
        web_query_parts = []
        if event_type: web_query_parts.append(event_type)
        if location_query: web_query_parts.append(f"em {location_query}")
        if date: web_query_parts.append(f"em {date}")
        web_query = f"Eventos culturais ou atividades {' '.join(web_query_parts)} em São Paulo"
        
        try:
            logger.info(f"Realizando busca na web com Tavily. Query: '{web_query}'")
            web_search_data = search_tavily(web_query, api_key=tavily_api_key, max_results=7)
            if web_search_data:
                logger.info(f"Busca na web retornou {len(web_search_data)} resultados.")
                web_search_memory.add_results(web_query, web_search_data)
            else:
                logger.info("Busca na web não retornou resultados.")
        except Exception as e:
            logger.error(f"Erro durante a busca na web com Tavily: {e}", exc_info=True)
    else:
        if not tavily_api_key:
            logger.info("Pulando busca na web: Chave API Tavily não configurada.")
        else:
            logger.info("Pulando busca na web pois não há critérios suficientes.")
    
    # Gera resposta final usando generate_response_from_llm
    logger.info("Delegando a geração da resposta final para o LLM...")
    contextual_location = ", ".join(expanded_locations) if expanded_locations else location_query
    
    final_structured_response = generate_response_from_llm(
        user_query_details={
            'event_type': event_type,
            'date': date,
            'location_query': location_query,
            'expanded_location_terms': contextual_location
        },
        scraped_events=all_event_data,
        web_search_results=web_search_data,
        max_suggestions=3
    )
    
    # Anexa descrições completas aos eventos selecionados
    if final_structured_response and isinstance(final_structured_response.get('events_found'), list):
        logger.info("Anexando descrições completas aos eventos selecionados pelo LLM...")
        events_from_llm = final_structured_response['events_found']
        
        # Cria mapas para busca rápida
        scraped_data_map = {item.get('id'): item for item in all_event_data if item.get('id')}
        web_data_map = {item.get('url'): item for item in web_search_data if item.get('url')}
        
        # Anexa descrições
        for llm_event in events_from_llm:
            original_id = llm_event.get('id')
            source = llm_event.get('source')
            full_description = "Descrição completa não encontrada."
            
            if original_id and source == 'scraper':
                original_item = scraped_data_map.get(original_id)
                if original_item:
                    full_description = original_item.get('description', "N/A Scraper")
            elif original_id and source == 'web':
                original_item = web_data_map.get(original_id)
                if original_item:
                    full_description = original_item.get('content') or original_item.get('raw_content') or original_item.get('response', "N/A Web")
            
            llm_event['full_description'] = full_description
        
        logger.info(f"Descrições completas anexadas a {len(events_from_llm)} eventos.")
    
    logger.info(f"Resposta estruturada final: {str(final_structured_response)[:300]}...")
    return final_structured_response

# ============================================================================
# Exports
# ============================================================================

__all__ = ['find_cultural_events_unified']

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    print("\n=== Testes do Localizador de Eventos Culturais ===\n")
    
    # Configuração básica de logging para testes
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Lista de casos de teste
    test_cases = [
        {
            "nome": "Busca por eventos culturais na Paulista",
            "params": {
                "event_type": "eventos culturais",
                "location_query": "Paulista"
            }
        },
        {
            "nome": "Busca por museus no centro",
            "params": {
                "event_type": "museus",
                "location_query": "centro"
            }
        },
        {
            "nome": "Busca por eventos neste fim de semana",
            "params": {
                "date": "este fim de semana"
            }
        },
        {
            "nome": "Busca por eventos infantis no Ibirapuera",
            "params": {
                "event_type": "eventos infantis",
                "location_query": "Ibirapuera",
                "date": "próximos dias"
            }
        }
    ]
    
    # Executa os testes
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Teste {i}: {test_case['nome']} ---")
        try:
            result = find_cultural_events_unified(**test_case['params'])
            
            # Exibe resumo dos resultados
            if result and isinstance(result, dict):
                print("\nResumo do Chat:")
                print(result.get('chat_summary', 'Nenhum resumo disponível'))
                
                events = result.get('events_found', [])
                print(f"\nEventos encontrados: {len(events)}")
                for j, event in enumerate(events, 1):
                    print(f"\n{j}. {event.get('title', 'Sem título')}")
                    print(f"   Local: {event.get('location', 'Local não especificado')}")
                    print(f"   Data: {event.get('date', 'Data não especificada')}")
                    print(f"   Fonte: {event.get('source', 'Fonte não especificada')}")
            else:
                print("Nenhum resultado encontrado ou resposta inválida.")
                
        except Exception as e:
            print(f"Erro durante o teste: {str(e)}")
        
        print("\n" + "="*50) 