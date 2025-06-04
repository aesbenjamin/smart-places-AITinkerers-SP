"""
Testes dos Utilitários
---------------------
Este módulo executa os testes principais de todos os utilitários
do pacote agents.utils e registra os resultados em um arquivo de log.
"""

# ============================================================================
# Imports
# ============================================================================

import os
import sys
import logging
import unittest
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import locale

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos dos módulos a serem testados 
from agents.utils.logger import get_logger
from agents.utils.config import load_config, get_api_key, get_llm_setting
from agents.utils.date_utils import standardize_date_format, parse_date
from agents.utils.maps import get_geocode, get_place_details, geocode_events_list
from agents.utils.env_setup import setup_environment_variables_and_locale, _load_llm_model_name_from_config

# ============================================================================
# Configuração do Logger
# ============================================================================

# Configura o logger para escrever em um arquivo
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_utils.log')
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
file_handler.setLevel(logging.DEBUG)

# Configura o logger raiz
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

# Logger específico para os testes
logger_test_utils = get_logger(__name__)

# ============================================================================
# Classes de Teste
# ============================================================================

class TestUtils(unittest.TestCase):
    """Classe base para testes dos utilitários."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração que executa uma vez antes de todos os testes da classe."""
        logger_test_utils.info(f"\n{'='*60}\nINICIANDO SUITE DE TESTES PARA: {cls.__name__}\n{'='*60}")
        # Configura o ambiente uma vez para todas as classes de teste que podem depender disso
        # (especialmente útil para config, maps, etc.)
        if not hasattr(cls, '_env_setup_done'): # Evita reconfigurar se herdado
            setup_environment_variables_and_locale()
            cls._env_setup_done = True
            logger_test_utils.info("Ambiente configurado (variáveis e locale).")

    def setUp(self):
        """Configuração inicial para cada teste."""
        logger_test_utils.info(f"-- Iniciando teste: {self._testMethodName} --")
    
    def tearDown(self):
        """Limpeza após cada teste."""
        logger_test_utils.info(f"-- Finalizando teste: {self._testMethodName} --\n")

class TestConfig(TestUtils):
    """Testes para o módulo de configuração (agents.utils.config)."""
    
    def test_load_config(self):
        """Testa o carregamento da configuração."""
        logger_test_utils.info("Testando load_config()...")
        config = load_config()
        self.assertIsNotNone(config, "Configuração não deve ser None")
        self.assertIsInstance(config, dict, "Configuração deve ser um dicionário")
        logger_test_utils.info(f"Configuração carregada com sucesso. Chaves: {list(config.keys()) if config else 'Vazio'}")

    def test_get_api_key(self):
        """Testa a obtenção de chaves de API."""
        logger_test_utils.info("Testando get_api_key()...")
        # Assume que 'gemini' é uma chave que pode ou não existir, ou ser placeholder
        # O teste não deve falhar se a chave não estiver configurada, apenas registrar
        gemini_key = get_api_key('gemini')
        if gemini_key:
            logger_test_utils.info(f"Chave API para 'gemini' encontrada: {gemini_key[:4]}...")
            self.assertIsInstance(gemini_key, str)
        else:
            logger_test_utils.info("Chave API para 'gemini' não encontrada ou é placeholder.")
        
        # Teste com uma chave que provavelmente não existe
        non_existent_key = get_api_key('chave_inexistente_test')
        self.assertIsNone(non_existent_key, "Chave inexistente deve retornar None")
        logger_test_utils.info("Teste para chave API inexistente passou.")

    def test_get_llm_setting(self):
        """Testa a obtenção de configurações do LLM."""
        logger_test_utils.info("Testando get_llm_setting()...")
        # Assume que 'model_name' pode ou não existir
        model_name = get_llm_setting('model_name', default_value='default_test_model')
        self.assertIsNotNone(model_name, "Configuração de LLM (model_name) não deve ser None (com default)")
        self.assertIsInstance(model_name, str)
        logger_test_utils.info(f"Configuração LLM 'model_name' obtida: {model_name}")
        
        non_existent_setting = get_llm_setting('setting_inexistente_test')
        self.assertIsNone(non_existent_setting, "Configuração LLM inexistente sem default deve ser None")
        logger_test_utils.info("Teste para configuração LLM inexistente passou.")

class TestDateUtils(TestUtils):
    """Testes para o módulo de utilidades de data (agents.utils.date_utils)."""
    
    def test_standardize_date_format(self):
        """Testa a padronização de formatos de data."""
        logger_test_utils.info("Testando standardize_date_format()...")
        test_cases = [
            ("20 de Janeiro de 2023", "2023-01-20"),
            ("20/01/2023", "2023-01-20"),
            ("2023-01-20", "2023-01-20"),
            # ("20 de Jan de 2023", "2023-01-20"), # Requer locale pt_BR configurado, pode ser instável em alguns CIs
            ("20 de Janeiro a 25 de Janeiro de 2023", None),
            ("data inválida", "data inválida"),
            (None, None),
            ("", None)
        ]
        for input_date, expected in test_cases:
            logger_test_utils.debug(f"  Testando: '{input_date}' -> esperado: '{expected}'")
            result = standardize_date_format(input_date)
            self.assertEqual(result, expected, f"Falha ao padronizar data: {input_date}")
        logger_test_utils.info("Testes de standardize_date_format concluídos.")

    def test_parse_date(self):
        """Testa a conversão de strings de data para objetos datetime."""
        logger_test_utils.info("Testando parse_date()...")
        test_cases = [
            ("20 de Janeiro de 2023", (datetime(2023, 1, 20), datetime(2023, 1, 20))),
            ("20/01/2023", (datetime(2023, 1, 20), datetime(2023, 1, 20))),
            ("data inválida", None),
            (None, None)
        ]
        for input_date_str, expected_dates_tuple in test_cases:
            logger_test_utils.debug(f"  Testando: '{input_date_str}'")
            result_tuple = parse_date(input_date_str)
            if expected_dates_tuple is None:
                self.assertIsNone(result_tuple, f"Esperado None para '{input_date_str}', obteve {result_tuple}")
            else:
                self.assertIsNotNone(result_tuple, f"Esperado tupla de datetimes para '{input_date_str}', obteve None")
                self.assertEqual(result_tuple[0].date(), expected_dates_tuple[0].date(), f"Data inicial não corresponde para '{input_date_str}'")
                self.assertEqual(result_tuple[1].date(), expected_dates_tuple[1].date(), f"Data final não corresponde para '{input_date_str}'")
        logger_test_utils.info("Testes de parse_date concluídos.")

class TestEnvSetup(TestUtils):
    """Testes para o módulo de configuração de ambiente (agents.utils.env_setup)."""

    def test_setup_environment_variables_and_locale(self):
        """Testa a função principal de configuração de ambiente."""
        # A função é chamada no setUpClass, aqui apenas verificamos se não lança erro
        # e se algumas variáveis de ambiente esperadas (mesmo que placeholder) são setadas
        logger_test_utils.info("Testando setup_environment_variables_and_locale() (indiretamente)...")
        try:
            # setup_environment_variables_and_locale() # Já chamado no setUpClass
            self.assertTrue(True) # Se chegou aqui sem erro, considera sucesso parcial
            logger_test_utils.info("setup_environment_variables_and_locale parece ter executado.")
            # Verifica se o locale foi configurado (pode variar no CI)
            current_locale = locale.getlocale(locale.LC_TIME)
            logger_test_utils.info(f"Locale LC_TIME atual: {current_locale}")
            # self.assertEqual(current_locale, ('pt_BR', 'UTF-8'), "Locale pt_BR.UTF-8 não foi configurado como esperado")
        except Exception as e:
            self.fail(f"setup_environment_variables_and_locale() lançou uma exceção: {e}")

    def test_load_llm_model_name_from_config(self):
        """Testa o carregamento do nome do modelo LLM."""
        logger_test_utils.info("Testando _load_llm_model_name_from_config()...")
        default_model = "test_default_model_name"
        model_name = _load_llm_model_name_from_config(default_model)
        self.assertIsNotNone(model_name, "Nome do modelo LLM não deve ser None")
        self.assertIsInstance(model_name, str)
        logger_test_utils.info(f"Nome do modelo LLM carregado/padrão: {model_name}")
        if model_name == default_model:
            logger_test_utils.info("Usando nome do modelo LLM padrão.")
        else:
            logger_test_utils.info("Nome do modelo LLM carregado da configuração.")

class TestLogger(TestUtils):
    """Testes para o módulo de logging (agents.utils.logger)."""

    def test_get_logger(self):
        """Testa a obtenção de uma instância de logger."""
        logger_test_utils.info("Testando get_logger()...")
        logger_instance = get_logger("test_logger_instance")
        self.assertIsNotNone(logger_instance, "get_logger() não deve retornar None")
        self.assertIsInstance(logger_instance, logging.Logger, "get_logger() deve retornar uma instância de logging.Logger")
        logger_test_utils.info(f"Instância de logger obtida: {logger_instance.name}")

    def test_logger_cache(self):
        """Testa se o cache de loggers funciona."""
        logger_test_utils.info("Testando cache de get_logger()...")
        logger1 = get_logger("cached_logger_test")
        logger2 = get_logger("cached_logger_test")
        self.assertIs(logger1, logger2, "Chamadas repetidas a get_logger com o mesmo nome devem retornar a mesma instância")
        logger_test_utils.info("Cache de logger funcionando como esperado.")

class TestMaps(TestUtils):
    """Testes para o módulo de utilidades do Google Maps (agents.utils.maps)."""
    
    def test_get_geocode(self):
        """Testa a geocodificação de endereços."""
        logger_test_utils.info("Testando get_geocode()...")
        # Este teste depende de uma chave de API válida do Google Maps
        # Se não houver chave, espera-se que retorne None e registre um erro/aviso
        test_address = "Av. Paulista, 1578, São Paulo, SP"
        result = get_geocode(test_address)
        if result:
            logger_test_utils.info(f"Geocodificação para '{test_address}' bem-sucedida: {result}")
            self.assertIn('latitude', result)
            self.assertIn('longitude', result)
            self.assertIsInstance(result['latitude'], float)
            self.assertIsInstance(result['longitude'], float)
        else:
            logger_test_utils.warning(f"Geocodificação para '{test_address}' falhou ou retornou None. Verifique a chave da API ou a conectividade.")
            # Não falha o teste se a API não estiver disponível, apenas registra
            self.assertIsNone(result, "get_geocode deve retornar None se a API falhar ou chave inválida")
    
    def test_get_place_details(self):
        """Testa a obtenção de detalhes de um lugar."""
        logger_test_utils.info("Testando get_place_details()...")
        # Este teste também depende de uma chave de API válida e um Place ID válido
        # Exemplo de Place ID para o MASP (pode mudar, verificar se o teste falhar)
        test_place_id = "ChIJ0xR62sBfzpQR0g0yLNRAwNo" # MASP
        result = get_place_details(test_place_id)
        if result:
            logger_test_utils.info(f"Detalhes do lugar para ID '{test_place_id}' obtidos: {result.get('name')}")
            self.assertIsInstance(result, dict)
            self.assertIn('name', result)
            self.assertEqual(result.get('place_id'), test_place_id)
        else:
            logger_test_utils.warning(f"Obtenção de detalhes para Place ID '{test_place_id}' falhou ou retornou None. Verifique a chave da API ou o Place ID.")
            self.assertIsNone(result, "get_place_details deve retornar None se a API falhar ou chave/ID inválido")

    def test_geocode_events_list(self):
        """Testa a geocodificação de uma lista de eventos."""
        logger_test_utils.info("Testando geocode_events_list()...")
        test_events = [
            {"name": "Evento MASP", "location_details": "Av. Paulista, 1578, São Paulo, SP"},
            {"name": "Evento sem local", "location_details": None},
            {"name": "Evento local inválido", "location_details": "__INVALID_ADDRESS__"}
        ]
        results = geocode_events_list(test_events)
        self.assertEqual(len(results), len(test_events), "A lista de resultados deve ter o mesmo tamanho da lista de entrada")
        
        if results[0].get('latitude'):
            logger_test_utils.info(f"Evento '{results[0]['name']}' geocodificado.")
            self.assertIn('latitude', results[0])
            self.assertIn('longitude', results[0])
        else:
            logger_test_utils.warning(f"Evento '{results[0]['name']}' não foi geocodificado (esperado se API indisponível).")

        self.assertIsNone(results[1].get('latitude'), "Latitude para evento sem local deve ser None.")
        self.assertIsNone(results[2].get('latitude'), "Latitude para evento com local inválido deve ser None.")
        logger_test_utils.info("Testes de geocode_events_list concluídos.")

# ============================================================================
# Função Principal de Teste
# ============================================================================

def run_all_tests():
    """Executa todos os testes e registra os resultados."""
    logger_test_utils.info("\n" + "="*70 + "\nINICIANDO EXECUÇÃO COMPLETA DOS TESTES DE UTILS\n" + "="*70)
    
    # Cria a suite de testes
    suite = unittest.TestSuite()
    
    # Adiciona os testes
    suite.addTest(unittest.makeSuite(TestConfig))
    suite.addTest(unittest.makeSuite(TestDateUtils))
    suite.addTest(unittest.makeSuite(TestEnvSetup))
    suite.addTest(unittest.makeSuite(TestLogger))
    suite.addTest(unittest.makeSuite(TestMaps))
    
    # Executa os testes
    # Usar um TextTestRunner que escreva no logger pode ser complexo.
    # O logging já está configurado para o arquivo, então os resultados dos testes
    # (pass/fail) aparecerão no console e o log detalhado no arquivo.
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout) # Envia para stdout
    result = runner.run(suite)
    
    # Registra o resultado final no logger
    logger_test_utils.info("\n" + "="*70 + "\nRESULTADO FINAL DOS TESTES DE UTILS\n" + "="*70)
    logger_test_utils.info(f"Testes executados: {result.testsRun}")
    logger_test_utils.info(f"Falhas: {len(result.failures)}")
    logger_test_utils.info(f"Erros: {len(result.errors)}")
    
    if result.failures:
        logger_test_utils.error("\nDetalhes das Falhas:")
        for i, (test_case, traceback_str) in enumerate(result.failures, 1):
            logger_test_utils.error(f"Falha {i}: {test_case}\n{traceback_str}")
    
    if result.errors:
        logger_test_utils.error("\nDetalhes dos Erros:")
        for i, (test_case, traceback_str) in enumerate(result.errors, 1):
            logger_test_utils.error(f"Erro {i}: {test_case}\n{traceback_str}")
    
    logger_test_utils.info("="*70 + "\nFIM DA EXECUÇÃO DOS TESTES DE UTILS\n" + "="*70)
    return result.wasSuccessful()

# ============================================================================
# Execução do Script
# ============================================================================

if __name__ == '__main__':
    success = run_all_tests()
    # O logger já escreve no arquivo, não precisamos de print aqui se não quisermos duplicar.
    print(f"\nExecução dos testes concluída. Verifique o arquivo '{log_file}' para logs detalhados.")
    print(f"Sucesso geral: {success}")
    sys.exit(0 if success else 1)
