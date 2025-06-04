"""
Configuração de Ambiente
------------------------
Este módulo configura o ambiente da aplicação, incluindo:
- Carregamento de variáveis de ambiente de um arquivo .env (se existir).
- Definição de chaves de API como variáveis de ambiente a partir do config.yaml.
- Configuração do locale para pt_BR.UTF-8 para manipulação de datas.
"""

import os
import sys
import locale
from typing import Dict, Any, Optional

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos
from agents.utils.config import load_config, get_api_key, get_llm_setting
from agents.utils.logger import get_logger

logger = get_logger(__name__)

def _set_env_var_from_config(key_name: str, config_service_name: str, config: Dict[str, Any]) -> None:
    """Define uma variável de ambiente a partir de uma chave de API no config."""
    api_key = get_api_key(config_service_name, config)
    if api_key:
        os.environ[key_name] = api_key
        logger.info(f"{key_name} definida em os.environ a partir do config.yaml.")
    # Não logar warning aqui, get_api_key já faz isso.

def _set_llm_env_vars_from_config(config: Dict[str, Any]) -> None:
    """Define variáveis de ambiente para configurações do LLM."""
    # Exemplo: Se você tiver uma configuração específica de LLM para definir como variável de ambiente
    # Por exemplo, se o SDK do Vertex AI precisasse de GOOGLE_PROJECT_ID
    google_project_id = get_llm_setting('google_project_id', None, config)
    if google_project_id:
        os.environ['GOOGLE_CLOUD_PROJECT'] = google_project_id
        logger.info(f"GOOGLE_CLOUD_PROJECT definida como '{google_project_id}' a partir do config.yaml.")
    
    # Adicionar outras configurações de LLM para variáveis de ambiente conforme necessário
    # Ex: os.environ['VERTEX_AI_REGION'] = get_llm_setting('vertex_ai_region', 'us-central1', config)

def setup_environment_variables_and_locale() -> None:
    """Carrega e define as variáveis de ambiente e configura o locale."""
    logger.info("Iniciando configuração de variáveis de ambiente e locale...")
    
    # Carrega a configuração (agents/utils/config.py cuidará de encontrar agents/config.yaml)
    config = load_config()
    if not config:
        logger.warning("Configuração não carregada. Algumas variáveis de ambiente podem não ser definidas.")
        # Mesmo sem config, tentar configurar o locale
        try:
            locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
            logger.info("Locale LC_TIME definido para pt_BR.UTF-8 (tentativa padrão).")
        except locale.Error as e:
            logger.warning(f"Falha ao definir o locale para pt_BR.UTF-8 (tentativa padrão): {e}. Verifique se o locale está instalado no sistema.")
        return

    # Definir chaves de API como variáveis de ambiente
    _set_env_var_from_config('GOOGLE_API_KEY', 'gemini', config)
    _set_env_var_from_config('TAVILY_API_KEY', 'tavily', config)
    _set_env_var_from_config('GOOGLE_MAPS_API_KEY', 'google_maps', config) # Se você usar uma chave específica para o Maps

    # Definir outras variáveis de ambiente relacionadas ao LLM
    _set_llm_env_vars_from_config(config)
    
    # Configurar o locale para datas em português
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        logger.info("Locale LC_TIME definido para pt_BR.UTF-8.")
    except locale.Error as e:
        logger.warning(f"Falha ao definir o locale para pt_BR.UTF-8: {e}. Verifique se o locale está instalado no sistema.")
    
    logger.info("Configuração de ambiente finalizada.")

def _load_llm_model_name_from_config(default_model_name: str) -> str:
    """
    Carrega o nome do modelo LLM do arquivo de configuração.
    Retorna o nome do modelo padrão se não for encontrado.
    """
    model_name = get_llm_setting('model_name', default_model_name)
    if model_name != default_model_name:
        logger.info(f"Nome do modelo LLM carregado do config.yaml: {model_name}")
    else:
        logger.info(f"Usando nome do modelo LLM padrão: {default_model_name} (não encontrado em config.yaml ou igual ao padrão).")
    return model_name

# Bloco de execução para teste local (opcional)
if __name__ == '__main__':
    print("Executando teste local de agents.utils.env_setup...")
    setup_environment_variables_and_locale()
    print("\nVariáveis de ambiente relevantes após a configuração:")
    print(f"  GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')}")
    print(f"  TAVILY_API_KEY: {os.getenv('TAVILY_API_KEY')}")
    print(f"  GOOGLE_MAPS_API_KEY: {os.getenv('GOOGLE_MAPS_API_KEY')}")
    print(f"  GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    
    print(f"\nLocale atual para LC_TIME: {locale.getlocale(locale.LC_TIME)}")
    
    # Testar _load_llm_model_name_from_config
    test_default_model = "test-default-flash"
    loaded_model = _load_llm_model_name_from_config(test_default_model)
    print(f"Modelo LLM carregado para teste: {loaded_model}")
    print("\nTeste local de agents.utils.env_setup concluído.")

__all__ = ['setup_environment_variables_and_locale', '_load_llm_model_name_from_config'] 