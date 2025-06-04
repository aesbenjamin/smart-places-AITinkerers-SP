"""
Testes para o Agente Cultural (CulturalAgentSP)
---------------------------------------------
Este módulo executa os testes para o CulturalAgentSP e suas funcionalidades principais.
"""

# ============================================================================
# Imports
# ============================================================================
import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime
import json
import importlib # Adicionado para reload

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports do módulo do agente
from agents.cultural_agent import (
    WelcomeHelper,
    # root_agent # Não importamos root_agent diretamente aqui para evitar instanciação prematura
)
# A importação de find_events_with_metadata foi removida pois a função não existe mais em cultural_agent.py
from agents import cultural_agent as cultural_agent_module # Importa o módulo para reload
# Para mockar o `Agent` do ADK e `FunctionTool` onde são usados em cultural_agent.py
# Mockaremos também agent_state e agent_artifacts que são usados como globais lá.

from agents.utils.logger import get_logger
from agents.utils.env_setup import setup_environment_variables_and_locale

# ============================================================================
# Configuração do Logger (similar a test_tools.py)
# ============================================================================

log_file_agents = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_agents.log')
agent_file_handler = logging.FileHandler(log_file_agents, mode='w')
agent_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
agent_file_handler.setLevel(logging.DEBUG)

root_logger_agents = logging.getLogger() # Pega o logger raiz
# Adiciona o handler apenas se um semelhante já não existir
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file_agents for h in root_logger_agents.handlers):
    root_logger_agents.addHandler(agent_file_handler)
# Garante que o logger raiz também capture logs DEBUG para o arquivo
if root_logger_agents.level > logging.DEBUG or root_logger_agents.level == logging.NOTSET:
    root_logger_agents.setLevel(logging.DEBUG)

logger_test_agents = get_logger(__name__)

# ============================================================================
# Classe de Teste Base
# ============================================================================

class TestAgentBase(unittest.TestCase):
    """Classe base para testes do agente."""
    
    @classmethod
    def setUpClass(cls):
        logger_test_agents.info(f"\n{'='*60}\nINICIANDO SUITE DE TESTES PARA: {cls.__name__}\n{'='*60}")
        # A configuração de ambiente é feita uma vez por classe de teste, se necessário
        # setup_environment_variables_and_locale() # Pode ser necessário se o agente depender disso na instanciação
        logger_test_agents.info(f"Ambiente para {cls.__name__} configurado.")

    def setUp(self):
        logger_test_agents.info(f"-- Iniciando teste: {self._testMethodName} --")
    
    def tearDown(self):
        logger_test_agents.info(f"-- Finalizando teste: {self._testMethodName} --\n")

# ============================================================================
# Classes de Teste Específicas
# ============================================================================

# A classe TestFindEventsFunction foi removida pois a função find_events_with_metadata
# não existe mais em agents/cultural_agent.py e sua lógica de teste não é mais aplicável aqui.
# A função find_cultural_events_unified, que agora é usada diretamente pelo FunctionTool,
# deve ser testada em tests/test_tools.py.

class TestAgentInitialization(TestAgentBase):
    """Testes para a inicialização e configuração do root_agent."""

    @patch('agents.utils.env_setup._load_llm_model_name_from_config')
    @patch('agents.prompts.get_agent_instruction')
    @patch('google.adk.agents.Agent')
    def test_root_agent_instantiated_correctly(
        self,
        MockAdkAgent,
        mock_get_instruction,
        mock_load_model_name_from_env_setup
    ):
        logger_test_agents.info("Testando a instanciação correta do root_agent...")

        # Configurar valores de retorno para os mocks
        mock_instructions_text = "Instruções mockadas para o agente."
        mock_get_instruction.return_value = mock_instructions_text
        
        mock_model_name = "gemini-test-model"
        mock_load_model_name_from_env_setup.return_value = mock_model_name
        
        # Gerenciar manualmente o patch para FunctionTool
        patcher_function_tool = patch('google.adk.tools.FunctionTool')
        MockFunctionTool_manual = patcher_function_tool.start()
        self.addCleanup(patcher_function_tool.stop)

        # Configurar o valor de retorno para o mock manual de FunctionTool
        # Este é o objeto que Agent receberá em sua lista de tools
        mock_tool_instance = MagicMock(name="ManuallyMockedToolInstance")
        MockFunctionTool_manual.return_value = mock_tool_instance

        # Recarregar o módulo do agente para acionar sua lógica de inicialização
        # com os mocks ativos
        importlib.reload(cultural_agent_module)
        
        # Assertivas
        mock_load_model_name_from_env_setup.assert_called_once_with(cultural_agent_module.DEFAULT_ADK_LLM_MODEL_NAME)
        mock_get_instruction.assert_called_once()
        
        # Verificar se FunctionTool foi chamado corretamente
        MockFunctionTool_manual.assert_called_once_with(func=cultural_agent_module.find_cultural_events_unified)
        
        # Verificar se Agent foi chamado corretamente
        MockAdkAgent.assert_called_once_with(
            name="CulturalAgentSP",
            description="Um assistente especializado em eventos culturais, museus e atividades de lazer na cidade de São Paulo.",
            instruction=mock_instructions_text,
            tools=[mock_tool_instance], # Deve ser a instância retornada pelo MockFunctionTool_manual
            model=mock_model_name
        )
        
        # Verificar se as referências do agente no módulo são o que esperamos (o retorno do mock de Agent)
        self.assertEqual(cultural_agent_module.agent, MockAdkAgent.return_value)
        self.assertEqual(cultural_agent_module.root_agent, MockAdkAgent.return_value)

        logger_test_agents.info("Teste de instanciação do root_agent concluído.")

class TestWelcomeHelper(TestAgentBase):
    """Testes para a classe WelcomeHelper."""
    
    def test_get_welcome_message(self):
        logger_test_agents.info("Testando WelcomeHelper.get_welcome_message...")
        helper = WelcomeHelper()
        expected_message = "Bem-vindo ao Agente Cultural de São Paulo! Como posso ajudar?"
        self.assertEqual(helper.get_welcome_message(), expected_message)
        logger_test_agents.info("Teste de WelcomeHelper.get_welcome_message concluído.")

# ============================================================================
# Função Principal de Teste
# ============================================================================

def run_all_agent_tests():
    logger_test_agents.info("\n" + "="*70 + "\nINICIANDO EXECUÇÃO COMPLETA DOS TESTES DE AGENTES\n" + "="*70)
    
    suite = unittest.TestSuite()
    # suite.addTest(unittest.makeSuite(TestFindEventsFunction)) # Removido
    suite.addTest(unittest.makeSuite(TestAgentInitialization))
    suite.addTest(unittest.makeSuite(TestWelcomeHelper))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    logger_test_agents.info("\n" + "="*70 + "\nRESULTADO FINAL DOS TESTES DE AGENTES\n" + "="*70)
    logger_test_agents.info(f"Testes executados: {result.testsRun}")
    logger_test_agents.info(f"Falhas: {len(result.failures)}")
    logger_test_agents.info(f"Erros: {len(result.errors)}")
    logger_test_agents.info(f"Testes pulados: {len(result.skipped)}")
    
    if result.failures:
        logger_test_agents.error("\nDetalhes das Falhas:")
        for i, (test_case, traceback_str) in enumerate(result.failures, 1):
            logger_test_agents.error(f"Falha {i}: {test_case}\n{traceback_str}")
    
    if result.errors:
        logger_test_agents.error("\nDetalhes dos Erros:")
        for i, (test_case, traceback_str) in enumerate(result.errors, 1):
            logger_test_agents.error(f"Erro {i}: {test_case}\n{traceback_str}")
            
    logger_test_agents.info("="*70 + "\nFIM DA EXECUÇÃO DOS TESTES DE AGENTES\n" + "="*70)
    return result.wasSuccessful()

if __name__ == '__main__':
    # A configuração de ambiente global pode ser chamada aqui se não for por classe
    # setup_environment_variables_and_locale()
    success = run_all_agent_tests()
    print(f"\nExecução dos testes de agentes concluída. Verifique o arquivo '{log_file_agents}' para logs detalhados.")
    print(f"Sucesso geral dos testes de agentes: {success}")
    sys.exit(0 if success else 1)
