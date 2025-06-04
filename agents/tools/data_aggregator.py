"""
Agregador de Dados
-----------------
Este módulo implementa um sistema de agregação de dados de eventos culturais
e museus de São Paulo, coletando informações de diferentes scrapers e
padronizando o formato dos dados para uso no sistema.
"""

# ============================================================================
# Imports
# ============================================================================

import sys
import os
import logging
from typing import List, Dict, Any

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos
from agents.utils.logger import get_logger
from agents.utils.date_utils import standardize_date_format
from agents.state.macro_state import ScraperMemory

# Imports dos scrapers
from agents.scrapers.fablab_scraper import scrape_fablab_events
from agents.scrapers.visite_sao_paulo_scraper import scrape_visite_sao_paulo_events
from agents.scrapers.wikipedia_museus_scraper import scrape_wikipedia_museus_info

# ============================================================================
# Configuração do Logger
# ============================================================================

logger = get_logger(__name__)

# ============================================================================
# Configurações e Constantes
# ============================================================================

# Instância da memória dos scrapers, gerenciada dentro deste módulo
scraper_memory = ScraperMemory(refresh_interval_seconds=3600)

# Prefixos a serem removidos dos nomes de locais do FabLab
FABLAB_PREFIXES_TO_REMOVE = [
    "fablab ", "fab lab ", "ceu ", "centro cultural ", "biblioteca "
]

# ============================================================================
# Funções Auxiliares
# ============================================================================

def _process_fablab_location(item: Dict[str, Any]) -> None:
    """
    Processa a localização de um evento do FabLab, extraindo o bairro.
    
    Args:
        item (Dict[str, Any]): Dicionário contendo os dados do evento
    """
    item_location_str = item.get('location')
    if item_location_str and item_location_str.lower() not in ["n/a", "n/a (disponível no link oficial)"]:
        temp_location = item_location_str.lower()
        extracted_bairro = item_location_str
        for prefix in FABLAB_PREFIXES_TO_REMOVE:
            if temp_location.startswith(prefix):
                extracted_bairro = item_location_str[len(prefix):].strip()
                break
        item['bairro'] = extracted_bairro
    else:
        item['bairro'] = None

def _process_museum_info(item: Dict[str, Any]) -> None:
    """
    Processa informações de museus da Wikipédia, padronizando campos.
    
    Args:
        item (Dict[str, Any]): Dicionário contendo os dados do museu
    """
    item.setdefault('category', 'Museu')
    item.setdefault('time', 'Variado')
    item.setdefault('official_event_link', item.get('source_site'))
    item.setdefault('description', f"Museu: {item.get('title')}")
    
    if 'district' in item:
        item['bairro'] = item.get('district')
        item['location'] = item.get('district', item.get('location'))
    else:
        item['bairro'] = None

def _process_visite_sao_paulo_location(item: Dict[str, Any]) -> None:
    """
    Processa a localização de um evento do Visite São Paulo.
    
    Args:
        item (Dict[str, Any]): Dicionário contendo os dados do evento
    """
    item_location_str = item.get('location')
    if item_location_str and item_location_str.lower() not in ["n/a", "n/a (disponível no link oficial)"]:
        item['bairro'] = item_location_str
    else:
        item['bairro'] = None

# ============================================================================
# Funções Principais
# ============================================================================

def get_all_events_from_scrapers_with_memory() -> List[Dict[str, Any]]:
    """
    Coleta e processa eventos de todos os scrapers configurados, utilizando um cache em memória.
    Padroniza datas e adiciona IDs únicos e informações de bairro quando aplicável.
    
    Returns:
        List[Dict[str, Any]]: Lista de eventos processados e padronizados
    """
    global scraper_memory
    
    if scraper_memory.should_refresh():
        logger.info("Data Aggregator: Memória de scrapers desatualizada ou vazia. Iniciando coleta...")
        all_items = []
        
        # Lista de scrapers a serem executados
        scrapers_to_run = [
            ("FabLab", scrape_fablab_events),
            ("Visite São Paulo", scrape_visite_sao_paulo_events),
            ("Museus da Wikipédia", scrape_wikipedia_museus_info)
        ]

        # Processa cada scraper
        for scraper_name, scraper_func in scrapers_to_run:
            try:
                logger.info(f"Data Aggregator: Buscando dados do {scraper_name}...")
                items = scraper_func()
                
                if items:
                    logger.info(f"Data Aggregator: Coletados {len(items)} itens do {scraper_name}. Processando...")
                    processed_items_count = 0
                    
                    for i, item in enumerate(items):
                        # Padroniza a data
                        original_date_str = item.get('date')
                        item['date'] = standardize_date_format(original_date_str) if original_date_str else None
                        
                        # Adiciona ID único
                        item['id'] = f"{scraper_name}_{i}_{item.get('title', '').replace(' ', '_')}"

                        # Processa informações específicas de cada tipo de scraper
                        if scraper_name == "Museus da Wikipédia":
                            _process_museum_info(item)
                        elif scraper_name == "FabLab":
                            _process_fablab_location(item)
                        else:  # Visite São Paulo e outros futuros
                            _process_visite_sao_paulo_location(item)
                        
                        all_items.append(item)
                        processed_items_count += 1
                        
                    logger.info(f"Data Aggregator: Processados e adicionados {processed_items_count} itens do {scraper_name}.")
                else:
                    logger.info(f"Data Aggregator: Nenhum item retornado pelo scraper {scraper_name}.")
                    
            except Exception as e:
                logger.error(f"Data Aggregator: Erro ao buscar itens do {scraper_name}: {e}", exc_info=True)
        
        # Atualiza a memória com os novos dados
        scraper_memory.update_events(all_items)
        logger.info(f"Data Aggregator: Total de itens combinados de todos os scrapers e armazenados na memória: {len(all_items)}.")
    else:
        logger.info("Data Aggregator: Usando dados de scrapers da memória (ainda válidos).")
    
    return scraper_memory.get_events()

# ============================================================================
# Exports
# ============================================================================

__all__ = ['get_all_events_from_scrapers_with_memory']

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    print("\n=== Testes do Agregador de Dados ===\n")
    
    # Configuração básica de logging para testes
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Lista de casos de teste
    test_cases = [
        {
            "nome": "Teste de coleta completa",
            "descricao": "Testa a coleta de dados de todos os scrapers"
        },
        {
            "nome": "Teste de processamento de localização FabLab",
            "descricao": "Testa o processamento de localizações do FabLab",
            "dados_teste": {
                "location": "fablab Butantã",
                "title": "Oficina de Robótica"
            }
        },
        {
            "nome": "Teste de processamento de museu",
            "descricao": "Testa o processamento de informações de museus",
            "dados_teste": {
                "title": "Museu do Ipiranga",
                "district": "Ipiranga",
                "source_site": "https://www.museudoipiranga.org.br"
            }
        },
        {
            "nome": "Teste de processamento Visite São Paulo",
            "descricao": "Testa o processamento de eventos do Visite São Paulo",
            "dados_teste": {
                "location": "Centro Cultural São Paulo",
                "title": "Exposição de Arte"
            }
        }
    ]
    
    # Executa os testes
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Teste {i}: {test_case['nome']} ---")
        print(f"Descrição: {test_case['descricao']}")
        
        try:
            if "dados_teste" in test_case:
                # Testa funções de processamento específicas
                item = test_case['dados_teste'].copy()
                
                if "fablab" in test_case['nome'].lower():
                    _process_fablab_location(item)
                    print("\nResultado do processamento FabLab:")
                elif "museu" in test_case['nome'].lower():
                    _process_museum_info(item)
                    print("\nResultado do processamento Museu:")
                else:
                    _process_visite_sao_paulo_location(item)
                    print("\nResultado do processamento Visite São Paulo:")
                
                print(f"Item original: {test_case['dados_teste']}")
                print(f"Item processado: {item}")
            else:
                # Testa a função principal de coleta
                print("\nColetando dados de todos os scrapers...")
                results = get_all_events_from_scrapers_with_memory()
                
                print(f"\nTotal de itens coletados: {len(results)}")
                if results:
                    print("\nExemplo do primeiro item:")
                    print(f"Título: {results[0].get('title')}")
                    print(f"Local: {results[0].get('location')}")
                    print(f"Bairro: {results[0].get('bairro')}")
                    print(f"Data: {results[0].get('date')}")
                    print(f"Categoria: {results[0].get('category')}")
                
        except Exception as e:
            print(f"Erro durante o teste: {str(e)}")
        
        print("\n" + "="*50) 