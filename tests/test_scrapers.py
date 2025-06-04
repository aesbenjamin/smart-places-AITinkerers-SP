"""
Testes dos Scrapers
-------------------
Este módulo executa os testes para os scrapers do projeto.
"""

# ============================================================================
# Imports
# ============================================================================

import os
import sys
import logging
import unittest
from typing import List, Dict, Any, Optional

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos dos módulos de scraper (serão adicionados conforme necessário)
from agents.scrapers.wikipedia_museus_scraper import scrape_wikipedia_museus_info, WIKIPEDIA_MUSEUS_URL
from agents.scrapers.visite_sao_paulo_scraper import scrape_visite_sao_paulo_events, BASE_URL as VISITE_SP_BASE_URL
from agents.scrapers.fablab_scraper import scrape_fablab_events, FABLAB_URL
# Exemplo: from agents.scrapers.fablab_scraper import scrape_fablab_livre_sp

from agents.utils.logger import get_logger
from agents.utils.env_setup import setup_environment_variables_and_locale

# ============================================================================
# Configuração do Logger
# ============================================================================

log_file_scrapers = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_scrapers.log')
scraper_file_handler = logging.FileHandler(log_file_scrapers, mode='w')
scraper_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
scraper_file_handler.setLevel(logging.DEBUG)

# Configura o logger raiz para incluir o handler dos scrapers
# Evita adicionar múltiplas vezes se já configurado por test_utils
root_logger_scrapers = logging.getLogger()
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file_scrapers for h in root_logger_scrapers.handlers):
    root_logger_scrapers.addHandler(scraper_file_handler)
root_logger_scrapers.setLevel(logging.DEBUG) # Garante que o logger raiz capture DEBUG

logger_test_scrapers = get_logger(__name__)

# ============================================================================
# Classes de Teste Base
# ============================================================================

class TestScrapersBase(unittest.TestCase):
    """Classe base para testes dos scrapers."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração que executa uma vez antes de todos os testes da classe."""
        logger_test_scrapers.info(f"\n{'='*60}\nINICIANDO SUITE DE TESTES PARA: {cls.__name__}\n{'='*60}")
        if not hasattr(cls, '_env_setup_done_scrapers'):
            setup_environment_variables_and_locale() # Para garantir que dependências como config funcionem
            cls._env_setup_done_scrapers = True
            logger_test_scrapers.info("Ambiente configurado (variáveis e locale) para TestScrapersBase.")

    def setUp(self):
        """Configuração inicial para cada teste."""
        logger_test_scrapers.info(f"-- Iniciando teste: {self._testMethodName} --")
    
    def tearDown(self):
        """Limpeza após cada teste."""
        logger_test_scrapers.info(f"-- Finalizando teste: {self._testMethodName} --\n")

# ============================================================================
# Classes de Teste Específicas (Esqueletos)
# ============================================================================

class TestWikipediaMuseusScraper(TestScrapersBase):
    """Testes para o Wikipedia Museus Scraper."""
    
    # @unittest.skip("Testes para WikipediaMuseusScraper ainda não implementados.")
    def test_scrape_wikipedia_museus_format(self):
        logger_test_scrapers.info("Testando o formato da saída de scrape_wikipedia_museus_info...")
        try:
            data = scrape_wikipedia_museus_info()
            self.assertIsNotNone(data, "A função não deve retornar None.")
            self.assertIsInstance(data, list, "A função deve retornar uma lista.")
            
            if data: # Só prossiga se a lista não estiver vazia
                logger_test_scrapers.info(f"Scraper retornou {len(data)} museus. Verificando o primeiro.")
                first_museum = data[0]
                self.assertIsInstance(first_museum, dict, "Cada item na lista deve ser um dicionário.")
                
                expected_keys = ['title', 'district', 'source_site']
                for key in expected_keys:
                    self.assertIn(key, first_museum, f"Chave esperada '{key}' não encontrada no dicionário do museu.")
                
                if 'title' in first_museum:
                    self.assertIsInstance(first_museum['title'], str, "O título do museu deve ser uma string.")
                if 'district' in first_museum:
                    self.assertIsInstance(first_museum['district'], str, "O distrito do museu deve ser uma string.")
                if 'source_site' in first_museum:
                    self.assertEqual(first_museum['source_site'], WIKIPEDIA_MUSEUS_URL, "A URL da fonte não corresponde à esperada.")
            else:
                logger_test_scrapers.warning("O scraper não retornou nenhum museu. O teste de formato do item individual será pulado.")
        except Exception as e:
            logger_test_scrapers.error(f"Erro durante o teste de scrape_wikipedia_museus_format: {e}", exc_info=True)
            self.fail(f"O scraper lançou uma exceção durante o teste: {e}")

class TestVisiteSaoPauloScraper(TestScrapersBase):
    """Testes para o Visite São Paulo Scraper."""

    # @unittest.skip("Testes para VisiteSaoPauloScraper ainda não implementados.")
    def test_scrape_visite_sao_paulo_format(self):
        logger_test_scrapers.info("Testando o formato da saída de scrape_visite_sao_paulo_events...")
        try:
            data = scrape_visite_sao_paulo_events()
            self.assertIsNotNone(data, "A função não deve retornar None.")
            self.assertIsInstance(data, list, "A função deve retornar uma lista.")

            if data: # Só prossiga se a lista não estiver vazia
                logger_test_scrapers.info(f"Scraper retornou {len(data)} eventos. Verificando o primeiro.")
                first_event = data[0]
                self.assertIsInstance(first_event, dict, "Cada item na lista deve ser um dicionário.")
                
                expected_keys = [
                    'title', 'description', 'date', 'time',
                    'location', 'category', 'official_event_link', 'source_site'
                ]
                for key in expected_keys:
                    self.assertIn(key, first_event, f"Chave esperada '{key}' não encontrada no dicionário do evento.")
                
                if 'title' in first_event:
                    self.assertIsInstance(first_event['title'], str, "O título do evento deve ser uma string.")
                # Adicionar mais verificações de tipo para outras chaves se necessário

                if 'source_site' in first_event:
                    self.assertEqual(first_event['source_site'], VISITE_SP_BASE_URL, "A URL da fonte não corresponde à esperada.")
            else:
                logger_test_scrapers.warning("O scraper Visite São Paulo não retornou nenhum evento. O teste de formato do item individual será pulado.")
        except Exception as e:
            logger_test_scrapers.error(f"Erro durante o teste de scrape_visite_sao_paulo_format: {e}", exc_info=True)
            self.fail(f"O scraper Visite São Paulo lançou uma exceção durante o teste: {e}")

class TestFablabScraper(TestScrapersBase):
    """Testes para o FabLab Livre SP Scraper."""

    # @unittest.skip("Testes para FablabScraper ainda não implementados.")
    def test_scrape_fablab_format(self):
        logger_test_scrapers.info("Testando o formato da saída de scrape_fablab_events...")
        try:
            data = scrape_fablab_events()
            self.assertIsNotNone(data, "A função não deve retornar None.")
            self.assertIsInstance(data, list, "A função deve retornar uma lista.")

            if data: # Só prossiga se a lista não estiver vazia
                logger_test_scrapers.info(f"Scraper FabLab retornou {len(data)} eventos. Verificando o primeiro.")
                first_event = data[0]
                self.assertIsInstance(first_event, dict, "Cada item na lista deve ser um dicionário.")
                
                expected_keys = [
                    'title', 'official_event_link', 'date', 'time',
                    'location', 'categories', 'description', 'source_site'
                ]
                for key in expected_keys:
                    self.assertIn(key, first_event, f"Chave esperada '{key}' não encontrada no dicionário do evento FabLab.")
                
                if 'title' in first_event:
                    self.assertIsInstance(first_event['title'], str, "O título do evento FabLab deve ser uma string.")
                
                if 'source_site' in first_event:
                    # O FABLAB_URL é a URL de busca, o source_site pode ser o domínio base.
                    # Vamos verificar se o source_site é parte do FABLAB_URL ou o próprio.
                    self.assertTrue(FABLAB_URL.startswith(first_event['source_site']) or first_event['source_site'] == "https://www.fablablivresp.prefeitura.sp.gov.br", 
                                    f"A URL da fonte '{first_event['source_site']}' não corresponde à esperada baseada em '{FABLAB_URL}'.")
            else:
                logger_test_scrapers.warning("O scraper FabLab não retornou nenhum evento. O teste de formato do item individual será pulado.")
        except Exception as e:
            logger_test_scrapers.error(f"Erro durante o teste de scrape_fablab_format: {e}", exc_info=True)
            self.fail(f"O scraper FabLab lançou uma exceção durante o teste: {e}")

# ============================================================================
# Função Principal de Teste
# ============================================================================

def run_all_scraper_tests():
    """Executa todos os testes de scrapers e registra os resultados."""
    logger_test_scrapers.info("\n" + "="*70 + "\nINICIANDO EXECUÇÃO COMPLETA DOS TESTES DE SCRAPERS\n" + "="*70)
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWikipediaMuseusScraper))
    suite.addTest(unittest.makeSuite(TestVisiteSaoPauloScraper))
    suite.addTest(unittest.makeSuite(TestFablabScraper))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    logger_test_scrapers.info("\n" + "="*70 + "\nRESULTADO FINAL DOS TESTES DE SCRAPERS\n" + "="*70)
    logger_test_scrapers.info(f"Testes executados: {result.testsRun}")
    logger_test_scrapers.info(f"Falhas: {len(result.failures)}")
    logger_test_scrapers.info(f"Erros: {len(result.errors)}")
    logger_test_scrapers.info(f"Testes pulados: {len(result.skipped)}") # Adicionado para contar testes pulados
    
    if result.failures:
        logger_test_scrapers.error("\nDetalhes das Falhas:")
        for i, (test_case, traceback_str) in enumerate(result.failures, 1):
            logger_test_scrapers.error(f"Falha {i}: {test_case}\n{traceback_str}")
    
    if result.errors:
        logger_test_scrapers.error("\nDetalhes dos Erros:")
        for i, (test_case, traceback_str) in enumerate(result.errors, 1):
            logger_test_scrapers.error(f"Erro {i}: {test_case}\n{traceback_str}")
            
    logger_test_scrapers.info("="*70 + "\nFIM DA EXECUÇÃO DOS TESTES DE SCRAPERS\n" + "="*70)
    return result.wasSuccessful()

# ============================================================================
# Execução do Script
# ============================================================================

if __name__ == '__main__':
    success = run_all_scraper_tests()
    print(f"\nExecução dos testes de scrapers concluída. Verifique o arquivo '{log_file_scrapers}' para logs detalhados.")
    print(f"Sucesso geral dos testes de scrapers: {success}")
    sys.exit(0 if success else 1)
