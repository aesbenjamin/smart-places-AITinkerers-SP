"""
Utilitário de Configuração
-------------------------
Este módulo lida com o carregamento e o acesso às configurações do
aplicativo a partir de um arquivo YAML.
"""

import os
import sys
import yaml
from typing import Any, Dict, Optional

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos
from agents.utils.logger import get_logger

logger = get_logger(__name__)

# O config.yaml agora está em agents/config.yaml
# __file__ em agents/utils/config.py refere-se a agents/utils/config.py
# O diretório pai de utils é agents/
CONFIG_FILE_NAME = 'config.yaml'
AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = os.path.join(AGENTS_DIR, CONFIG_FILE_NAME)

_config_cache: Optional[Dict[str, Any]] = None

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Carrega o arquivo de configuração YAML.

    Args:
        config_path (str): O caminho para o arquivo de configuração.
                           O padrão é 'config.yaml' no diretório 'agents'.

    Returns:
        Dict[str, Any]: Um dicionário contendo as configurações.
                        Retorna um dicionário vazio se o arquivo não for encontrado ou houver um erro.
    """
    global _config_cache
    if _config_cache is not None:
        logger.debug(f"Retornando configuração do cache.")
        return _config_cache

    try:
        logger.debug(f"Tentando carregar configuração de: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        if config_data is None:
            logger.warning(f"Arquivo de configuração {config_path} está vazio ou não é YAML válido.")
            _config_cache = {}
            return {}
        
        logger.info(f"Configuração carregada com sucesso de {config_path}")
        _config_cache = config_data
        return config_data
    except FileNotFoundError:
        logger.error(f"Arquivo de configuração não encontrado em {config_path}. Retornando configuração vazia.")
        _config_cache = {}
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Erro ao fazer parse do arquivo YAML de configuração {config_path}: {e}. Retornando configuração vazia.")
        _config_cache = {}
        return {}
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar configuração de {config_path}: {e}", exc_info=True)
        _config_cache = {}
        return {}

def get_api_key(service_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Obtém uma chave de API do arquivo de configuração.

    Args:
        service_name (str): O nome do serviço (ex: 'google_maps', 'gemini', 'tavily').
        config (Optional[Dict[str, Any]]): Opcional, a configuração já carregada.

    Returns:
        Optional[str]: A chave da API se encontrada, caso contrário None.
    """
    if config is None:
        config = load_config()
    
    # Mapeamento de nomes de serviço curtos para os nomes reais das chaves no YAML
    key_name_map = {
        "gemini": "gemini_api_key",
        "tavily": "tavily_api_key"
        # Outros mapeamentos podem ser adicionados aqui se necessário.
    }

    # Usar o nome mapeado se existir, caso contrário, usar o service_name original.
    actual_key_name_to_lookup = key_name_map.get(service_name, service_name)
    
    api_keys_dict = config.get('api_keys', {})
    api_key = api_keys_dict.get(actual_key_name_to_lookup)
    
    if not api_key:
        logger.warning(f"Chave de API para '{actual_key_name_to_lookup}' (solicitada como '{service_name}') não encontrada no arquivo de configuração.")
    # Ajustar a verificação de placeholder para cobrir ambos os nomes
    elif api_key == f"SUA_CHAVE_{service_name.upper()}_AQUI" or \
         (actual_key_name_to_lookup != service_name and api_key == f"SUA_CHAVE_{actual_key_name_to_lookup.upper()}_AQUI"):
        logger.warning(f"Chave de API para '{actual_key_name_to_lookup}' (solicitada como '{service_name}') parece ser um placeholder. Verifique o config.yaml.")
        return None # Não retornar placeholder
    return api_key

def get_llm_setting(setting_name: str, default_value: Any = None, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Obtém uma configuração do LLM do arquivo de configuração.

    Args:
        setting_name (str): O nome da configuração (ex: 'model_name').
        default_value (Any): Valor padrão a ser retornado se a configuração não for encontrada.
        config (Optional[Dict[str, Any]]): Opcional, a configuração já carregada.

    Returns:
        Any: O valor da configuração ou o valor padrão.
    """
    if config is None:
        config = load_config()
    
    return config.get('llm_settings', {}).get(setting_name, default_value)

# Seção de Testes Locais (opcional, mas útil para depuração)
if __name__ == '__main__':
    print("Executando testes locais para agents.utils.config...")
    
    # Teste 1: Carregar configuração
    print("\n--- Teste 1: Carregar Configuração ---")
    cfg = load_config()
    if cfg:
        print("Configuração carregada com sucesso.")
        # print(f"Conteúdo (parcial): {list(cfg.keys())}")
    else:
        print("Falha ao carregar configuração ou configuração vazia.")

    # Teste 2: Obter chaves de API
    print("\n--- Teste 2: Obter Chaves de API ---")
    google_maps_key = get_api_key('google_maps', cfg)
    gemini_key = get_api_key('gemini', cfg)
    tavily_key = get_api_key('tavily', cfg)

    print(f"Chave Google Maps: {'Encontrada' if google_maps_key else 'Não Encontrada/Placeholder'}")
    print(f"Chave Gemini: {'Encontrada' if gemini_key else 'Não Encontrada/Placeholder'}")
    print(f"Chave Tavily: {'Encontrada' if tavily_key else 'Não Encontrada/Placeholder'}")

    # Teste 3: Obter configurações do LLM
    print("\n--- Teste 3: Obter Configurações do LLM ---")
    model_name = get_llm_setting('model_name', 'default_model', cfg)
    temperature = get_llm_setting('temperature', 0.7, cfg)
    print(f"Nome do Modelo LLM: {model_name}")
    print(f"Temperatura LLM: {temperature}")
    
    # Teste 4: Cache de configuração
    print("\n--- Teste 4: Cache de Configuração ---")
    cfg_cached = load_config() # Deve usar o cache
    if cfg is cfg_cached: # Verifica se é o mesmo objeto
        print("Cache de configuração funcionando corretamente.")
    else:
        print("ERRO: Cache de configuração não parece estar funcionando.")

    print("\nFim dos testes de agents.utils.config.")

__all__ = ['load_config', 'get_api_key', 'get_llm_setting']