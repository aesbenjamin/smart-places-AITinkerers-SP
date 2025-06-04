"""
Scraper para Museus da Wikipédia
-------------------------------
Este módulo implementa um scraper para extrair informações de museus da cidade
de São Paulo da página da Wikipédia. O scraper busca nome e distrito dos museus
listados na tabela da página e retorna os dados estruturados.
"""

# ============================================================================
# Imports e Configuração
# ============================================================================

import requests
from bs4 import BeautifulSoup
import sys
import os
import logging

# Adiciona o diretório raiz ao sys.path para importação do logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

# ============================================================================
# Constantes
# ============================================================================

# URL da página da Wikipédia com a lista de museus
WIKIPEDIA_MUSEUS_URL = "https://pt.wikipedia.org/wiki/Lista_de_museus_da_cidade_de_S%C3%A3o_Paulo"

# Headers para requisições HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ============================================================================
# Funções Auxiliares
# ============================================================================

def _extract_museum_info(cols):
    """
    Extrai informações de um museu a partir das colunas da tabela.
    
    Args:
        cols (list): Lista de elementos BeautifulSoup representando as colunas da tabela
        
    Returns:
        dict: Dicionário com informações do museu ou None se não for possível extrair
    """
    try:
        # Extrai nome do museu (segunda coluna)
        museum_name_tag = cols[1].find('a')
        museum_name = museum_name_tag.get_text(strip=True) if museum_name_tag else cols[1].get_text(strip=True)
        
        # Extrai distrito (terceira coluna)
        district_name_tag = cols[2].find('a')
        district_name = district_name_tag.get_text(strip=True) if district_name_tag else cols[2].get_text(strip=True)

        if museum_name and district_name:
            return {
                'title': museum_name,
                'district': district_name,
                'source_site': WIKIPEDIA_MUSEUS_URL
            }
    except IndexError:
        logger.debug(f"Linha da tabela com colunas insuficientes")
    except Exception as e:
        logger.warning(f"Erro ao extrair informações do museu: {e}")
    
    return None

# ============================================================================
# Função Principal
# ============================================================================

def scrape_wikipedia_museus_info():
    """
    Extrai informações de museus da página da Wikipédia.
    
    Returns:
        list: Lista de dicionários contendo informações dos museus.
              Retorna lista vazia se a extração falhar ou nenhum museu for encontrado.
    """
    logger.info(f"Iniciando extração de museus da Wikipédia: {WIKIPEDIA_MUSEUS_URL}")
    museus = []
    
    try:
        # Faz a requisição HTTP
        response = requests.get(WIKIPEDIA_MUSEUS_URL, timeout=20, headers=HEADERS)
        response.raise_for_status()
        logger.info("Página de museus da Wikipédia obtida com sucesso.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar URL {WIKIPEDIA_MUSEUS_URL}: {e}")
        return museus

    # Parse do HTML
    soup = BeautifulSoup(response.content, 'html.parser')

    # Encontra a tabela de museus
    table = soup.find('table', class_='wikitable sortable')
    if not table:
        logger.warning("Tabela de museus não encontrada na página.")
        return museus

    # Processa cada linha da tabela (pulando o cabeçalho)
    rows = table.find_all('tr')
    for row in rows[1:]:
        cols = row.find_all('td')
        if len(cols) > 1:
            museum_info = _extract_museum_info(cols)
            if museum_info:
                museus.append(museum_info)
                logger.debug(f"Museu encontrado: {museum_info['title']} - Distrito: {museum_info['district']}")

    logger.info(f"Extração da Wikipédia finalizada. Encontrados {len(museus)} museus.")
    return museus

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    # Configuração do logger para execução direta do script
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    logger.info("Iniciando teste do scraper de museus da Wikipédia...")
    museus = scrape_wikipedia_museus_info()
    
    if museus:
        logger.info(f"Encontrados {len(museus)} museus:")
        # Mostra os primeiros 5 museus encontrados
        for i, museu in enumerate(museus[:5]):
            logger.info(
                f"  {i+1}. "
                f"Nome: {museu.get('title')}, "
                f"Distrito: {museu.get('district')}"
            )
    else:
        logger.info("Nenhum museu encontrado ou erro durante a extração.") 