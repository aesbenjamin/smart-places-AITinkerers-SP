"""
Geração de Respostas do Usuário
-----------------------------
Este módulo implementa a geração de respostas para consultas do usuário
usando o modelo LLM Gemini. Ele processa dados de eventos de diferentes
fontes (scrapers e busca web) e gera respostas estruturadas com sugestões
de eventos relevantes.

O módulo utiliza o SDK do Google Gemini para processamento de linguagem
natural e geração de respostas em formato JSON estruturado.
"""

# ============================================================================
# Imports
# ============================================================================

import os
import sys
import json
import yaml
import logging
import google.generativeai as genai
from typing import List, Dict, Any, Optional, Union

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos
from agents.utils.logger import get_logger



# ============================================================================
# Configuração do Logger
# ============================================================================

logger = get_logger(__name__)

# ============================================================================
# Configurações e Constantes
# ============================================================================

# Nome padrão do modelo LLM
DEFAULT_LLM_MODEL_NAME = "gemini-1.5-flash-latest"

# ============================================================================
# Funções Auxiliares
# ============================================================================

def _load_llm_config() -> Dict[str, str]:
    """
    Carrega configurações do LLM do arquivo config.yaml.
    
    Returns:
        Dict[str, str]: Dicionário com as configurações do LLM
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
    llm_config = {"model_name": DEFAULT_LLM_MODEL_NAME}

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Carrega a chave da API do Gemini
            if config_data and isinstance(config_data.get('api_keys'), dict):
                gemini_api_key = config_data['api_keys'].get('gemini_api_key')
                if gemini_api_key and isinstance(gemini_api_key, str):
                    llm_config["api_key"] = gemini_api_key
                    logger.info("Chave da API do Gemini carregada do config.yaml")
                else:
                    logger.warning("Chave da API do Gemini não encontrada ou inválida em 'api_keys' no config.yaml")
            else:
                logger.warning("Seção 'api_keys' não encontrada no config.yaml")
            
            # Carrega o nome do modelo
            if config_data and isinstance(config_data.get('llm_settings'), dict):
                loaded_model_name = config_data['llm_settings'].get('model_name')
                if loaded_model_name and isinstance(loaded_model_name, str):
                    llm_config["model_name"] = loaded_model_name
                    logger.info(f"Nome do modelo LLM carregado do config.yaml: {loaded_model_name}")
                else:
                    logger.warning(f"'model_name' não encontrado ou inválido em 'llm_settings' no config.yaml. Usando padrão: {DEFAULT_LLM_MODEL_NAME}")
            else:
                logger.warning(f"Seção 'llm_settings' não encontrada no config.yaml. Usando padrão: {DEFAULT_LLM_MODEL_NAME}")
        except yaml.YAMLError as e:
            logger.error(f"Erro ao ler YAML do config.yaml: {e}. Usando padrão: {DEFAULT_LLM_MODEL_NAME}")
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar config.yaml: {e}. Usando padrão: {DEFAULT_LLM_MODEL_NAME}")
    else:
        logger.warning(f"Arquivo config.yaml não encontrado em {config_path}. Usando modelo LLM padrão: {DEFAULT_LLM_MODEL_NAME}")
    return llm_config

def _sanitize_string_for_prompt(text: Optional[Any]) -> str:
    """
    Limpa uma string para inclusão segura em um prompt LLM.
    
    Args:
        text (Optional[Any]): Texto a ser sanitizado
        
    Returns:
        str: Texto sanitizado seguro para uso em prompts
    """
    if text is None:
        return "N/A"
    s = str(text)
    s = s.replace('\\\\', '\\\\\\\\')
    s = s.replace('"', '\\\\"')
    s = s.replace("'", "\\\\'")
    s = s.replace('\\n', ' ')
    s = s.replace('\\r', '')
    return s

# ============================================================================
# Configuração Inicial
# ============================================================================

# Carrega a configuração do LLM uma vez quando o módulo é importado
LLM_CONFIG = _load_llm_config()

# ============================================================================
# Funções Principais
# ============================================================================

def generate_response_from_llm(
    user_query_details: Dict[str, Optional[str]],
    scraped_events: List[Dict[str, Any]],
    web_search_results: List[Dict[str, Any]],
    max_suggestions: int = 5
) -> Dict[str, Any]:
    """
    Gera uma resposta para o usuário usando o LLM (Gemini) para encontrar eventos.
    
    Args:
        user_query_details (Dict[str, Optional[str]]): Detalhes da consulta do usuário
        scraped_events (List[Dict[str, Any]]): Lista de eventos dos scrapers
        web_search_results (List[Dict[str, Any]]): Resultados da busca web
        max_suggestions (int): Número máximo de sugestões a retornar
        
    Returns:
        Dict[str, Any]: Resposta formatada contendo resumo do chat e eventos encontrados
    """
    current_llm_model_name = LLM_CONFIG.get("model_name", DEFAULT_LLM_MODEL_NAME)
    fallback_error_response = {
        "chat_summary": "Desculpe, estou com dificuldades técnicas para processar sua solicitação.",
        "events_found": []
    }


    # Construção do prompt
    prompt_parts = []
    
    # 1. Contextualização da Tarefa e Consulta do Usuário
    prompt_parts.append("Sua tarefa é analisar a consulta do usuário e os dados de eventos fornecidos para gerar uma lista de candidatos a eventos em formato JSON.")
    prompt_parts.append("Analise a consulta do usuário:")
    prompt_parts.append(f"  - Tipo de interesse principal: {_sanitize_string_for_prompt(user_query_details.get('event_type', 'Qualquer'))}")
    if user_query_details.get('date'):
        prompt_parts.append(f"  - Data de interesse: {_sanitize_string_for_prompt(user_query_details.get('date'))}")
    
    original_location_query = user_query_details.get('location_query')
    expanded_location_terms_str = user_query_details.get('expanded_location_terms')

    if original_location_query:
        prompt_parts.append(f"  - Localização de interesse (original): {_sanitize_string_for_prompt(original_location_query)}")
    
    if expanded_location_terms_str and expanded_location_terms_str != original_location_query:
        formatted_terms_for_prompt = f"'{_sanitize_string_for_prompt(expanded_location_terms_str)}'"
        prompt_parts.append(f"  - Para uma busca mais ampla, considere também os seguintes termos de localização relacionados (tratados como um texto único): {formatted_terms_for_prompt}")
    
    prompt_parts.append("\nConsidere os seguintes dados de eventos e resultados de busca web para construir sua lista JSON de candidatos.")
    prompt_parts.append("PRIORIZE eventos que correspondam BEM ao TIPO de interesse, DATA e LOCALIZAÇÃO (original ou expandida).")
    prompt_parts.append("Para eventos gastronômicos, procure por palavras como 'gastronomia', 'comida', 'festival', 'restaurante', 'bar', 'drink', 'cerveja', 'vinho', etc., no título, descrição ou categoria.")

    # 2. Dados dos Scrapers
    if scraped_events:
        prompt_parts.append("\n--- Dados de Eventos e Museus Locais (Scrapers) ---")
        max_scraped_to_show = 75
        events_to_show_count = min(len(scraped_events), max_scraped_to_show)
        if len(scraped_events) > events_to_show_count:
            prompt_parts.append(f"(Analisando os primeiros {events_to_show_count} de {len(scraped_events)} itens dos scrapers. A seleção priorizará relevância.)")
        events_to_show = scraped_events[:events_to_show_count]
        for i, event in enumerate(events_to_show):
            title = _sanitize_string_for_prompt(event.get('title', 'N/A'))
            date_info = _sanitize_string_for_prompt(event.get('date_str') or event.get('date', 'N/A'))
            location_info = _sanitize_string_for_prompt(event.get('bairro') or event.get('location', 'N/A'))
            address_info = _sanitize_string_for_prompt(event.get('address', 'N/A'))
            category_info = _sanitize_string_for_prompt(event.get('category') or event.get('type', 'N/A'))
            description_text = str(event.get('description', ''))
            description_info = _sanitize_string_for_prompt(description_text)
            link_info = _sanitize_string_for_prompt(event.get('official_event_link', 'N/A'))
            original_id = _sanitize_string_for_prompt(event.get('id', f'scraper_item_{i+1}'))
            event_str = f"Item Scraper {i+1}: ID_ORIGINAL: {original_id}, Título: {title}, Data: {date_info}, Local/Bairro: {location_info}, Endereço: {address_info}, Categoria: {category_info}, Descrição: {description_info}, Link: {link_info}"
            prompt_parts.append(event_str)
    else:
        prompt_parts.append("\nNenhum dado de eventos ou museus locais (scrapers) foi encontrado.")

    # 3. Dados da Busca na Web
    if web_search_results:
        prompt_parts.append("\n--- Dados da Busca na Web (Tavily) ---")
        web_to_show_count = min(len(web_search_results), 5)
        if len(web_search_results) > web_to_show_count:
            prompt_parts.append(f"(Mostrando os primeiros {web_to_show_count} de {len(web_search_results)} resultados da web)")
        web_results_to_show = web_search_results[:web_to_show_count]
        for i, result in enumerate(web_results_to_show):
            title = _sanitize_string_for_prompt(result.get('title', 'N/A'))
            url = _sanitize_string_for_prompt(result.get('url', f'web_item_{i+1}'))
            content_text = str(result.get('response') or result.get('raw_content') or result.get('content', ''))
            content_info = _sanitize_string_for_prompt(content_text)
            web_str = f"Resultado Web {i+1}: ID_ORIGINAL: {url}, Título: {title}, URL: {url}, Conteúdo: {content_info}"
            prompt_parts.append(web_str)

    # 4. Instruções para o LLM
    prompt_parts.append("\n--- INSTRUÇÕES CRÍTICAS PARA A SAÍDA JSON ---")
    prompt_parts.append("1. Sua ÚNICA tarefa é gerar um objeto JSON. Não adicione NENHUM texto, comentários, ou explicações antes ou depois do JSON.")
    prompt_parts.append("2. O objeto JSON DEVE ter uma única chave principal: 'event_candidates'.")
    prompt_parts.append("3. O valor de 'event_candidates' DEVE ser uma LISTA de objetos.")
    prompt_parts.append("4. Cada objeto na lista 'event_candidates' representa um evento e DEVE ter AS SEGUINTES CHAVES EXATAS (strings):")
    prompt_parts.append("   - 'id': String (O valor de ID_ORIGINAL do item de scraper ou web que você usou para criar este candidato. Ex: \"FabLab_3_AlgumEvento\" ou \"http://example.com/page\"). DEVE CORRESPONDER AO ID_ORIGINAL DO ITEM FONTE.")
    prompt_parts.append("   - 'name': String (nome do evento/local).")
    prompt_parts.append("   - 'location_details': String (endereço COMPLETO ou detalhes suficientes para geocodificação, ex: 'MASP, Avenida Paulista, 1578, Bela Vista, São Paulo, SP'. Se tiver bairro/distrito, inclua). SE NÃO HOUVER DETALHE DE LOCALIZAÇÃO, USE \"São Paulo\" COMO FALLBACK.")
    prompt_parts.append("   - 'type': String (categoria, ex: 'Museu', 'Show', 'Festival Gastronômico', 'Evento de Comida').")
    prompt_parts.append("   - 'date_info': String (data, período ou 'N/A' se não especificado). Para datas como 'sábado que vem', tente manter essa descrição amigável se uma data exata não puder ser inferida dos dados do evento.")
    prompt_parts.append("   - 'source': String ('scraper' ou 'web').")
    prompt_parts.append("   - 'details_link': String (URL ou string vazia se não houver).")
    prompt_parts.append(f"5. Selecione no máximo {max_suggestions} eventos/locais MAIS RELEVANTES para a consulta do usuário. Priorize correspondências fortes nos critérios de tipo, data e localização.")
    prompt_parts.append("6. Se nenhum evento relevante for encontrado, o valor de 'event_candidates' DEVE ser uma lista vazia ( [] ). NÃO invente eventos.")
    prompt_parts.append("7. NÃO inclua `json` ou ```json ... ``` na sua saída. A saída deve ser o JSON puro.")

    prompt_parts.append("\nAgora, gere o objeto JSON contendo APENAS a chave 'event_candidates' e sua lista de eventos. NADA MAIS.")

    full_prompt = "\n".join(prompt_parts)

    logger.debug(f"Usando modelo LLM: {current_llm_model_name}")
    logger.debug(f"Prompt LLM (primeiras 500 chars):\n{full_prompt[:500]}...")
    logger.debug(f"Prompt LLM (últimas 300 chars):\n...{full_prompt[-300:]}")

    llm_event_candidates = []
    try:
        model = genai.GenerativeModel(current_llm_model_name)
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content(full_prompt, generation_config=generation_config)
        
        raw_response_text = response.text
        logger.debug(f"Resposta bruta do LLM (esperado JSON puro):\n{raw_response_text}")
        
        parsed_llm_json = json.loads(raw_response_text)
        
        if isinstance(parsed_llm_json, dict) and 'event_candidates' in parsed_llm_json and isinstance(parsed_llm_json['event_candidates'], list):
            llm_event_candidates = parsed_llm_json['event_candidates']
            validated_candidates = []
            for cand_event in llm_event_candidates:
                if isinstance(cand_event, dict) and \
                   'id' in cand_event and \
                   'name' in cand_event and \
                   'location_details' in cand_event and \
                   'type' in cand_event and \
                   'date_info' in cand_event and \
                   'source' in cand_event and \
                   'details_link' in cand_event:
                    validated_candidates.append(cand_event)
                else:
                    logger.warning(f"Evento candidato do LLM descartado por falta de campos obrigatórios ou formato incorreto: {cand_event}")
            llm_event_candidates = validated_candidates
            logger.info(f"LLM retornou {len(llm_event_candidates)} candidatos a eventos válidos.")
        else:
            logger.error(f"Estrutura JSON da resposta do LLM é inválida ou não contém 'event_candidates' como uma lista. Resposta: {parsed_llm_json}")

    except json.JSONDecodeError as json_err:
        logger.error(f"Falha ao decodificar JSON da resposta do LLM: {json_err}. Resposta bruta recebida: '{raw_response_text}'")
    except Exception as e:
        logger.error(f"Erro crítico ao gerar/processar resposta do LLM: {e}")
        error_details = str(e)
        if hasattr(e, 'message'): error_details = e.message
        elif hasattr(e, 'args') and e.args: error_details = str(e.args[0])
        
        prompt_feedback_info = ""
        if 'response' in locals() and response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            prompt_feedback_info = f" Feedback do prompt: {response.prompt_feedback}"
        
        raw_text_info = ""
        if 'raw_response_text' in locals() and raw_response_text:
             raw_text_info = f" Resposta bruta do LLM: {raw_response_text[:200]}..."

        return {**fallback_error_response, "chat_summary": f"Falha na comunicação com o assistente de IA: {error_details}.{prompt_feedback_info}{raw_text_info}"}

    # Construção do chat_summary
    chat_summary = ""
    if not llm_event_candidates:
        if 'parsed_llm_json' in locals() and not (isinstance(parsed_llm_json, dict) and 'event_candidates' in parsed_llm_json):
             chat_summary = f"O assistente de IA retornou dados em um formato inesperado. Não consegui encontrar eventos para sua busca (tipo: {user_query_details.get('event_type', 'N/A')}, data: {user_query_details.get('date', 'N/A')}, local: {user_query_details.get('location_query', 'N/A')})."
        else:
            chat_summary = f"Não encontrei eventos que correspondam exatamente à sua busca (tipo: {user_query_details.get('event_type', 'N/A')}, data: {user_query_details.get('date', 'N/A')}, local: {user_query_details.get('location_query', 'N/A')}). Que tal tentar uma busca com critérios diferentes ou mais amplos?"
    else:
        num_found = len(llm_event_candidates)
        effective_max_suggestions = max_suggestions
        
        event_names = [event.get('name', 'Evento sem nome') for event in llm_event_candidates[:3]]
        event_list_str = ", ".join(event_names)

        if num_found == 1:
            chat_summary = f"Encontrei 1 evento que pode te interessar: {event_list_str}. Veja os detalhes e o mapa!"
        elif num_found <= effective_max_suggestions:
            chat_summary = f"Encontrei {num_found} eventos que podem te interessar, como: {event_list_str}. Veja os detalhes e o mapa!"
        else:
            chat_summary = f"Encontrei {num_found} eventos! Os primeiros são: {event_list_str}. Mostrando os {effective_max_suggestions} mais relevantes nos detalhes e mapa. Para ver mais, você pode refinar sua busca."
            llm_event_candidates = llm_event_candidates[:effective_max_suggestions]
    
    final_response = {
        "chat_summary": chat_summary,
        "events_found": llm_event_candidates
    }
    return final_response

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    print("\n=== Testes da Ferramenta de Geração de Respostas ===\n")
    
    # Configuração da API Key para o teste standalone
    try:
        # Configura a API usando a chave do config.yaml
        if "api_key" in LLM_CONFIG:
            genai.configure(api_key=LLM_CONFIG["api_key"])
            logger.info("Chave Gemini configurada para o teste standalone (via config.yaml).")
        else:
            logger.error("Chave da API do Gemini não encontrada no config.yaml")
            print("\nERRO: Chave da API do Gemini não encontrada no config.yaml")
            print("Por favor, verifique se a chave está configurada corretamente em:")
            print("config.yaml -> api_keys -> gemini_api_key")
    except Exception as e:
        logger.error(f"Erro ao configurar genai com API key: {e}")
        print("\nERRO: Falha ao configurar a API do Gemini.")
        print("Por favor, verifique se:")
        print("1. A chave da API está correta no config.yaml")
        print("2. A chave tem permissões para acessar a API do Gemini")
        print("3. A chave está ativa no Console do Google Cloud")

    # Lista de casos de teste
    test_cases = [
        {
            "nome": "Teste com dados completos",
            "descricao": "Testa a geração de resposta com dados de scrapers e web",
            "query": {
                'event_type': 'show de rock',
                'date': 'próximo sábado',
                'location_query': 'República, São Paulo'
            },
            "scraped_events": [
                {
                    'id': 'fab1_rockclassico',
                    'title': 'Show Rock Clássico',
                    'date_str': '2024-08-10',
                    'bairro': 'República',
                    'location': 'República, São Paulo',
                    'address': 'Rua do Rock, 123, República, São Paulo, SP',
                    'category': 'Música',
                    'description': 'Banda cover tocando sucessos do rock clássico dos anos 70 e 80.',
                    'official_event_link': 'http://fab.lab/rockclassic'
                },
                {
                    'id': 'wiki1_diversidade',
                    'title': 'Museu da Diversidade Musical',
                    'date_str': 'Permanente',
                    'bairro': 'Sé',
                    'location': 'Sé, São Paulo',
                    'address': 'Praça da Guitarra, S/N, Sé, São Paulo, SP',
                    'category': 'Museu',
                    'description': 'Explora a rica história de diversos gêneros musicais.',
                    'official_event_link': 'http://museu.mus.br'
                }
            ],
            "web_results": [
                {
                    'title': 'Agenda de Shows Rock em SP para Sábado',
                    'url': 'http://guia.rocksaopaulo.com/proximo-sabado',
                    'response': 'Os melhores shows de rock para o próximo sábado na cidade de São Paulo.',
                    'raw_content': 'Conteúdo bruto do guia rock sp...'
                },
                {
                    'title': 'Festival Indie no Centro Velho de SP',
                    'url': 'http://festival.indie.sp.br',
                    'response': 'Bandas independentes se apresentam no coração de São Paulo.',
                    'raw_content': 'Conteúdo bruto do festival indie...'
                }
            ]
        },
        {
            "nome": "Teste com dados vazios",
            "descricao": "Testa a geração de resposta sem dados de eventos",
            "query": {
                'event_type': 'show de rock',
                'date': 'próximo sábado',
                'location_query': 'República, São Paulo'
            },
            "scraped_events": [],
            "web_results": []
        }
    ]
    
    # Executa os testes
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Teste {i}: {test_case['nome']} ---")
        print(f"Descrição: {test_case['descricao']}")
        
        try:
            # Verifica se a API está configurada tentando criar um modelo
            try:
                model = genai.GenerativeModel(DEFAULT_LLM_MODEL_NAME)
                resposta_dict = generate_response_from_llm(
                    test_case['query'],
                    test_case['scraped_events'],
                    test_case['web_results'],
                    max_suggestions=3
                )
                
                print("\n--- Resposta Gerada ---")
                if isinstance(resposta_dict, dict):
                    print(f"Chat Summary: {resposta_dict.get('chat_summary')}")
                    events_found = resposta_dict.get('events_found', [])
                    print(f"Events Found ({len(events_found)}):")
                    if not events_found:
                        print("  Nenhum evento encontrado.")
                    for i, event in enumerate(events_found):
                        print(f"  {i+1}. Name: {event.get('name')}")
                        print(f"     Location: {event.get('location_details')}")
                        print(f"     Type: {event.get('type')}, Date: {event.get('date_info')}")
                        print(f"     Source: {event.get('source')}, Link: {event.get('details_link')}")
                else:
                    print(f"ERRO: Resposta não foi um dicionário: {resposta_dict}")
            except Exception as e:
                error_msg = str(e)
                if "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in error_msg:
                    print("\nERRO: A chave da API não tem as permissões necessárias.")
                    print("Por favor, verifique se:")
                    print("1. A chave tem acesso à API do Gemini")
                    print("2. A chave está ativa no Console do Google Cloud")
                    print("3. O projeto tem a API do Gemini habilitada")
                else:
                    print(f"\nLLM não pôde ser testado: {error_msg}")
                
        except Exception as e:
            print(f"Erro durante o teste: {str(e)}")
        
        print("\n" + "="*50)

# ============================================================================
# Exports
# ============================================================================

__all__ = ['generate_response_from_llm']
