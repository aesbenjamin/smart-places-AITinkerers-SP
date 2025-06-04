"""
Módulo de Busca na Web
---------------------
Este módulo implementa um sistema de busca na web utilizando a API Tavily.
Ele fornece funcionalidades para realizar buscas avançadas com filtros por domínio
e configuração de resultados.
"""

# ============================================================================
# Imports
# ============================================================================

import os
import sys
import yaml
from typing import List, Dict, Any, Optional
from tavily import TavilyClient

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agents.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configurações e Constantes
# ============================================================================

# Variável global para armazenar a chave da API
TAVILY_API_KEY = None

# ============================================================================
# Funções de Configuração
# ============================================================================

def load_tavily_api_key() -> str | None:
    """
    Carrega a chave da API Tavily do arquivo de configuração ou variável de ambiente.
    
    Returns:
        str | None: A chave da API se encontrada, None caso contrário
    """
    global TAVILY_API_KEY

    try:
        # Tenta carregar do config.yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        current_key = None

        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config and isinstance(config.get('api_keys'), dict):
                    current_key = config['api_keys'].get('tavily_api_key')
        
        # Tenta carregar da variável de ambiente
        if not current_key:
            current_key = os.getenv("TAVILY_API_KEY")

        if current_key:
            TAVILY_API_KEY = current_key
            logger.info("Chave da API Tavily carregada com sucesso.")
            return current_key
            
    except Exception as e:
        logger.error(f"Erro ao carregar a chave da API Tavily: {e}")
        TAVILY_API_KEY = None
    
    return None

# ============================================================================
# Funções Principais
# ============================================================================

def search_tavily(
    query: str,
    api_key: Optional[str],
    max_results: int = 5,
    include_domains: List[str] = None,
    exclude_domains: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Realiza uma busca na web usando a API Tavily.

    Args:
        query (str): A string de busca
        api_key (Optional[str]): A chave da API Tavily
        max_results (int, optional): Número máximo de resultados. Defaults to 5
        include_domains (List[str], optional): Lista de domínios para incluir na busca
        exclude_domains (List[str], optional): Lista de domínios para excluir da busca

    Returns:
        List[Dict[str, Any]]: Lista de resultados da busca, ou lista vazia em caso de erro
    """
    
    if not api_key:
        logger.warning("Chave da API Tavily não fornecida. Busca não realizada.")
        return []

    try:
        client = TavilyClient(api_key=api_key)
        response_data = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=include_domains,
            exclude_domains=exclude_domains
        )
        logger.info(f"Busca Tavily realizada com sucesso para query: '{query}'")
        return response_data.get('results', [])
    except Exception as e:
        logger.error(f"Erro durante a busca com Tavily para a query '{query}': {e}")
        return []

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    # Carrega a chave da API para testes
    chave_teste_tavily = load_tavily_api_key()
    
    if chave_teste_tavily:
        print("\n--- Teste de Busca Tavily ---")
        
        # Teste 1: Busca por eventos culturais
        test_query_1 = "Eventos culturais gratuitos em São Paulo este fim de semana"
        results_1 = search_tavily(test_query_1, api_key=chave_teste_tavily, max_results=3)
        print(f"\nResultados para: '{test_query_1}'")
        if results_1:
            for i, res in enumerate(results_1):
                print(f"  {i+1}. Título: {res.get('title')}")
                print(f"     URL: {res.get('url')}")
                print(f"     Conteúdo (snippet): {res.get('content', '')[:250]}...") 
        else:
            print("  Nenhum resultado encontrado ou erro na busca.")

        # Teste 2: Busca específica em domínios
        test_query_2 = "Museus de ciência em São Paulo"
        results_2 = search_tavily(
            test_query_2,
            api_key=chave_teste_tavily,
            max_results=2,
            include_domains=["wikipedia.org", "sp.gov.br"]
        )
        print(f"\nResultados para: '{test_query_2}' (apenas wikipedia.org, sp.gov.br)")
        if results_2:
            for i, res in enumerate(results_2):
                print(f"  {i+1}. Título: {res.get('title')}")
                print(f"     URL: {res.get('url')}")
                print(f"     Conteúdo (snippet): {res.get('content', '')[:250]}...")
        else:
            print("  Nenhum resultado encontrado ou erro na busca.")
    else:
        print("\nTeste de Busca Tavily não pode ser executado: SDK ou Chave API não disponíveis.")

__all__ = ['search_tavily', 'load_tavily_api_key']
