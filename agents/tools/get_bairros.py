"""
Expansor de Localizações
-----------------------
Este módulo implementa um sistema para expandir termos de localização em São Paulo,
usando um modelo de linguagem (LLM) quando disponível e um dicionário predefinido
como fallback. O sistema ajuda a melhorar buscas por locais incluindo bairros
adjacentes e nomes alternativos.
"""

# ============================================================================
# Imports
# ============================================================================

import os
import sys
import ast
import json
from typing import List, Dict
import yaml
import google.generativeai as genai

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agents.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configurações e Constantes
# ============================================================================

# Flags de controle
SHOULD_USE_LLM = False
API_KEY_LOADED = False

# ============================================================================
# Configuração da API
# ============================================================================

def _configure_api():
    """
    Configura a API do Gemini, tentando carregar a chave do config.yaml
    ou da variável de ambiente.
    
    Returns:
        bool: True se a configuração foi bem-sucedida, False caso contrário
    """

    try:
        # Tenta carregar do config.yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        api_key = None

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                api_keys_dict = config.get('api_keys', {})
                api_key = api_keys_dict.get('gemini_api_key')
            
            if api_key:
                genai.configure(api_key=api_key)
                logger.info(f"Chave Gemini API carregada com sucesso de {config_path}.")
                return True
            else:
                logger.warning(f"'gemini_api_key' não encontrada em {config_path}.")

        # Tenta carregar da variável de ambiente
        env_api_key = os.getenv("GOOGLE_API_KEY")
        if env_api_key:
            genai.configure(api_key=env_api_key)
            logger.info("Chave Gemini API carregada da variável de ambiente GOOGLE_API_KEY.")
            return True
        else:
            if os.path.exists(config_path):
                logger.warning("Chave Gemini API não encontrada no config.yaml nem na variável de ambiente GOOGLE_API_KEY.")
            else:
                logger.warning(f"Arquivo {config_path} não encontrado e chave GOOGLE_API_KEY não definida.")
            return False

    except yaml.YAMLError as e:
        logger.error(f"Erro ao ler o arquivo YAML de configuração: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro ao configurar a API Gemini: {e}")
        return False

# Configura a API ao importar o módulo
API_KEY_LOADED = _configure_api()
SHOULD_USE_LLM = API_KEY_LOADED

# ============================================================================
# Funções Principais
# ============================================================================

def _clean_llm_response(response_text: str) -> str:
    """
    Limpa a resposta do LLM removendo marcadores de código e espaços extras.
    
    Args:
        response_text (str): Texto da resposta do LLM
        
    Returns:
        str: Texto limpo
    """
    cleaned_text = response_text.strip()
    
    # Remove marcadores de bloco de código
    if cleaned_text.startswith("```json\n") and cleaned_text.endswith("\n```"):
        cleaned_text = cleaned_text[len("```json\n"):-len("\n```")]
    elif cleaned_text.startswith("```") and cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[len("```"):-len("```")]
    
    return cleaned_text.strip()

def _parse_llm_response(cleaned_text: str, location_query: str) -> List[str]:
    """
    Tenta fazer o parse da resposta do LLM como JSON ou Python literal.
    
    Args:
        cleaned_text (str): Texto limpo da resposta do LLM
        location_query (str): Query original para mensagens de erro
        
    Returns:
        List[str]: Lista de termos expandidos ou lista vazia se falhar
    """
    try:
        # Tenta parsear como JSON
        parsed_list = json.loads(cleaned_text)
        if isinstance(parsed_list, list):
            return [str(term).lower() for term in parsed_list]
    except json.JSONDecodeError:
        try:
            # Tenta parsear como literal Python
            parsed_list = ast.literal_eval(cleaned_text)
            if isinstance(parsed_list, list):
                return [str(term).lower() for term in parsed_list]
        except (ValueError, SyntaxError):
            pass
    
    logger.warning(f"Falha ao decodificar resposta do LLM para '{location_query}': {cleaned_text}")
    return []

def get_expanded_location_terms(location_query: str) -> Dict[str, List[str]]:
    """
    Expande uma consulta de localização para incluir termos relacionados.
    
    Args:
        location_query (str): Localização fornecida pelo usuário (ex: "Paulista")
        
    Returns:
        Dict[str, List[str]]: Dicionário com a chave "expanded_terms" contendo
                             o termo original e termos expandidos
    """
    if not location_query:
        return {"expanded_terms": []}

    location_query_lower = location_query.lower()
    expanded_terms = []

    # Tenta usar o LLM se disponível
    if SHOULD_USE_LLM:
        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = (
                f"Para a localização de referência na cidade de São Paulo: '{location_query}', liste bairros adjacentes, "
                f"sinônimos ou nomes pelos quais essa região é comumente conhecida. "
                f"Retorne APENAS uma lista JSON de strings. Por exemplo, se a entrada for 'Paulista', "
                f"a saída deve ser algo como: [\"avenida paulista\", \"bela vista\", \"consolação\", \"jardim paulista\"]."
                f"Se não souber ou a localização for muito genérica, retorne uma lista vazia: []."
            )

            response = model.generate_content(prompt)
            cleaned_response = _clean_llm_response(response.text)
            expanded_terms.extend(_parse_llm_response(cleaned_response, location_query))
            
        except Exception as e:
            logger.warning(f"Erro durante a chamada ao LLM para '{location_query}': {e}")


    # Garante que o termo original esteja na lista e remove duplicatas
    final_terms = [location_query_lower]
    if expanded_terms:
        for term in expanded_terms:
            term_lower = term.lower()
            if term_lower not in final_terms:
                final_terms.append(term_lower)
    
    return {"expanded_terms": final_terms}

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':

    # Lista de locais para teste
    test_locations = [
        "Paulista", "MASP", "Ibirapuera", "Pinheiros",
        "Centro", "Vila Madalena", "Estádio do Morumbi", "Rua Augusta"
    ]

    # Testa cada local
    for loc in test_locations:
        print(f"\nProcessando: '{loc}'")
        result_dict = get_expanded_location_terms(loc)
        print(f"Local original: '{loc}' -> Termos expandidos: {result_dict}")
