"""
Agente Cultural de São Paulo (CulturalAgentSP)
---------------------------------------------
Este módulo implementa um agente especializado em eventos culturais, museus e atividades
de lazer em São Paulo, utilizando o Google ADK (Agent Development Kit) e integrando
diversas ferramentas de busca e processamento de dados.
"""

# ============================================================================
# Imports e Configuração do Ambiente
# ============================================================================

import sys
import os
from datetime import datetime, timedelta

from typing import Dict, Any, AsyncIterator

# Imports relativos para módulos dentro do pacote 'agents'
from .utils.logger import get_logger, current_session_id_var
from .utils.env_setup import setup_environment_variables_and_locale, _load_llm_model_name_from_config
from .prompts import get_global_instructions, get_agent_instruction
from .tools.cultural_event_finder import find_cultural_events_unified

# Configura o ambiente (chaves API em os.environ e locale)
setup_environment_variables_and_locale()

# Imports para o Google ADK
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

import google.generativeai as genai

ADK_AVAILABLE = True
GEMINI_SDK_CONFIGURABLE = True

# O logger principal do módulo é obtido sem session_id na inicialização do módulo.
# Os loggers para interações específicas usarão o ContextVar.
module_init_logger = get_logger(__name__)

# ============================================================================
# Constantes e Configurações
# ============================================================================

DEFAULT_ADK_LLM_MODEL_NAME = "gemini-1.5-flash-latest"

# ============================================================================
# Classe de Agente Personalizada para Lidar com Logs de Sessão
# ============================================================================

class CulturalAgentSPImpl(Agent):
    """
    Implementação personalizada do CulturalAgentSP que configura o logging de sessão
    usando contextvars.
    """
    async def _run_async_impl(self, ctx: Any) -> AsyncIterator[Any]:
        """
        Sobrescreve o método base para definir o session_id no ContextVar antes
        de executar a lógica do agente, e limpá-lo depois.
        ctx virá do ADK e terá o session_id.
        Event será o tipo de evento que o ADK espera ser retornado.
        """
        session_id_to_use = None
        
        # Prioridade 1: Tentar obter o ID da sessão da conversa (mais específico)
        if hasattr(ctx, 'session') and hasattr(ctx.session, 'id') and ctx.session.id:
            session_id_to_use = ctx.session.id
            # module_init_logger.info(f"_run_async_impl: Usando ctx.session.id: {session_id_to_use}") # Log opcional para depuração
        # Prioridade 2: Se não houver ctx.session.id, tentar ctx.user_id
        elif hasattr(ctx, 'user_id') and ctx.user_id:
            session_id_to_use = ctx.user_id
            # module_init_logger.info(f"_run_async_impl: Usando ctx.user_id como fallback: {session_id_to_use}") # Log opcional para depuração
        
        if not session_id_to_use:
            # Fallback final para um ID genérico se nenhum dos anteriores for encontrado ou for None/vazio
            module_init_logger.warning(f"_run_async_impl: Nao foi possivel encontrar ctx.session.id nem ctx.user_id. Usando fallback para session_id.")
            session_id_to_use = "unknown_session_id_adk_v013_fallback"
        
        session_id = str(session_id_to_use) # Garante que é uma string para o nome do arquivo e logs

        token = None
        method_logger = None # Será inicializado após definir o ContextVar
        try:
            if session_id and session_id.strip():
                token = current_session_id_var.set(session_id)
                method_logger = get_logger(__name__ + "._run_async_impl")
                method_logger.info(f"ContextVar current_session_id_var definido para: {session_id}. Iniciando processamento do agente.")

                # Registrar a entrada do usuário
                if hasattr(ctx, 'user_content') and ctx.user_content and hasattr(ctx.user_content, 'parts'):
                    user_input_texts = []
                    for part in ctx.user_content.parts:
                        if hasattr(part, 'text') and part.text:
                            user_input_texts.append(part.text)
                    if user_input_texts:
                        full_user_input = " ".join(user_input_texts)
                        method_logger.info(
                            "Entrada do Usuário", 
                            extra={"user_input": full_user_input, "agent_response": ""}
                        )
            else:
                module_init_logger.warning("_run_async_impl chamado sem session_id válido (ctx.session.id ou ctx.user_id podem estar ausentes ou vazios). Usando logger do módulo.")
                method_logger = module_init_logger
            
            # Chama a implementação original do LlmAgent/Agent
            async for event in super()._run_async_impl(ctx):
                # Registrar a resposta do agente
                if method_logger and hasattr(event, 'content') and event.content and hasattr(event.content, 'parts') and hasattr(event, 'author') and event.author == self.name:
                    agent_response_texts = []
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            agent_response_texts.append(part.text)
                        elif hasattr(part, 'function_call') and part.function_call: # ADK v0.1.3 usa function_call
                            fc = part.function_call
                            fc_name = getattr(fc, 'name', 'N/A')
                            fc_args = getattr(fc, 'args', {})
                            agent_response_texts.append(f"Chamada de função: {fc_name}(args={fc_args})")
                        elif hasattr(part, 'functionCall') and part.functionCall: # Gemini SDK pode usar functionCall (maiúsculo C)
                            fc = part.functionCall
                            fc_name = getattr(fc, 'name', 'N/A')
                            fc_args = getattr(fc, 'args', {})
                            agent_response_texts.append(f"Chamada de função: {fc_name}(args={fc_args})")
                            
                    if agent_response_texts:
                        full_agent_response = " ".join(agent_response_texts)
                        method_logger.info(
                            "Resposta do Agente", 
                            extra={"user_input": "", "agent_response": full_agent_response}
                        )
                yield event
            
            if method_logger and session_id and session_id.strip():
                method_logger.info(f"Processamento do agente concluído para sessão: {session_id}.")

        except Exception as e:
            if method_logger: # Se o logger de método (com session_id) foi inicializado
                method_logger.error(f"Erro durante super()._run_async_impl para sessão {session_id or 'DESCONHECIDA'}: {e}", exc_info=True)
            else: # Fallback para o logger de inicialização do módulo
                module_init_logger.error(f"Erro durante super()._run_async_impl para sessão {session_id or 'DESCONHECIDA'} (antes do logger da sessão ser configurado): {e}", exc_info=True)
            raise # Re-levanta a exceção para que o ADK possa lidar com ela
        finally:
            if token is not None:
                current_session_id_var.reset(token)
                if method_logger: # Deve existir se token não for None
                    method_logger.info(f"ContextVar current_session_id_var resetado para sessão: {session_id}.")
            elif method_logger and session_id and session_id.strip(): # Caso o token não tenha sido definido mas o logger sim
                method_logger.debug(f"Tentativa de reset de ContextVar para sessão {session_id}, mas o token não foi definido (session_id pode ter sido inválido inicialmente ou fallback).")
            elif method_logger: # Se method_logger foi atribuído ao module_init_logger
                method_logger.debug(f"ContextVar não foi definido (session_id inválido), nenhum reset necessário.")

# ============================================================================
# Inicialização do Agente
# ============================================================================

tool_instance = FunctionTool(func=find_cultural_events_unified)

adk_model_name_to_use = _load_llm_model_name_from_config(DEFAULT_ADK_LLM_MODEL_NAME)
module_init_logger.info(f"Instanciando Agente ADK ({CulturalAgentSPImpl.__name__}) com modelo: {adk_model_name_to_use}")

# Agora instanciamos nossa classe personalizada
root_agent = CulturalAgentSPImpl(
    name="CulturalAgentSP",
    description="Um assistente especializado em eventos culturais, museus e atividades de lazer na cidade de São Paulo.",
    instruction=get_agent_instruction(),
    tools=[tool_instance],
    model=adk_model_name_to_use
)

# ============================================================================
# Classe Auxiliar WelcomeHelper
# ============================================================================

class WelcomeHelper:
    """Classe auxiliar para gerenciar mensagens de boas-vindas."""
    def get_welcome_message(self) -> str:
        module_init_logger.info("WelcomeHelper: Generating welcome message.")
        return "Bem-vindo ao Agente Cultural de São Paulo! Como posso ajudar?"

# ============================================================================
# Bloco Principal de Execução (Testes Locais)
# ============================================================================

if __name__ == "__main__":

    module_init_logger.info("Agente Cultural - Teste Local. Execute como 'python -m agents.cultural_agent' para imports relativos.")
    
    gemini_api_key_from_env = os.getenv("GOOGLE_API_KEY")
    if gemini_api_key_from_env:
        try:
            genai.configure(api_key=gemini_api_key_from_env)
            module_init_logger.info("SDK Gemini: GOOGLE_API_KEY configurada via os.environ.")
        except Exception as e: 
            module_init_logger.error(f"Falha ao genai.configure() no teste local: {e}")
    else: 
        module_init_logger.warning("SDK Gemini: GOOGLE_API_KEY não definida em os.environ.")

    if not os.getenv("TAVILY_API_KEY"):
        module_init_logger.warning("SDK Tavily: TAVILY_API_KEY não encontrada em os.environ.")
    else: 
        module_init_logger.info("SDK Tavily: TAVILY_API_KEY encontrada em os.environ.")

    print(f"\n{WelcomeHelper().get_welcome_message()}\n")
    print("\n--- Teste de Cenário: Crianças na Paulista (Fim de Semana) ---")
    today = datetime.now()
    saturday = today + timedelta((5 - today.weekday() + 7) % 7)
    saturday_desc = f"próximo sábado ({saturday.strftime('%d/%m')})"
    test_queries_main = [
        {"event_type": "crianças", "date": saturday_desc, "location_query": "Paulista", "desc": f"Crianças Paulista {saturday_desc}"},
    ]
    for query_params in test_queries_main:
        print(f"\nBuscando para '{query_params['desc']}':")
        try:
            result = find_cultural_events_unified(
                event_type=query_params["event_type"],
                date=query_params["date"],
                location_query=query_params["location_query"]
            )
            print(f"Resultado ({query_params['desc']}):")
            print(f"  Resposta: {result.get('response')}")
            print(f"  Estado: {result.get('state_delta')}")
            print(f"  Artefatos: {result.get('artifact_delta')}")
            print(f"  Metadados de Uso: {result.get('usage_metadata')}")
            print('-'*50)
        except Exception as e:
            module_init_logger.error(f"Erro no teste para '{query_params['desc']}': {e}", exc_info=True)
            print(f"Erro ao processar query '{query_params['desc']}'. Verifique os logs.")
    print("\n--- Fim dos Testes Locais ---")
    if ADK_AVAILABLE: 
        print("Para interagir com o agente ADK: execute 'adk web' ou 'adk run agents' no diretório raiz do projeto.")

# ============================================================================
# Exports
# ============================================================================

__all__ = ['root_agent']
