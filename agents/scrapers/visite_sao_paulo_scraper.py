"""
Scraper para o Visite São Paulo
------------------------------
Este módulo implementa um scraper para extrair informações de eventos do site
Visite São Paulo. O scraper busca eventos disponíveis no calendário do portal
e retorna os dados estruturados.
"""

# ============================================================================
# Imports e Configuração
# ============================================================================

import requests
from bs4 import BeautifulSoup
import sys
import os
from urllib.parse import urljoin
import re
import logging

# Adiciona o diretório raiz ao sys.path para importação do logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

# ============================================================================
# Constantes
# ============================================================================

# URLs base
BASE_URL = "https://visitesaopaulo.com"
EVENTS_URL = f"{BASE_URL}/calendario-eventos/"

# Headers para requisições HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ============================================================================
# Funções Auxiliares
# ============================================================================

def _extract_date_from_text(text):
    """
    Extrai uma data de um texto usando diferentes padrões.
    
    Args:
        text (str): Texto que pode conter uma data
        
    Returns:
        str: Data encontrada ou "N/A"
    """
    if not text:
        return "N/A"
    
    # Padrão para datas em português (ex: "15 de Março de 2024")
    if " de " in text.lower() and len(text) > 4:
        return text
    
    # Padrão para datas numéricas (ex: "15/03/2024" ou "15-03-2024")
    if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-](\d{2}|\d{4})$', text.strip()):
        return text.strip()
    
    return "N/A"

def _find_details_link(element):
    """
    Procura por um link de detalhes em um elemento e seus filhos.
    
    Args:
        element (BeautifulSoup): Elemento HTML para procurar
        
    Returns:
        str: URL do link de detalhes ou "N/A"
    """
    # Procura por link direto com texto "detalhes"
    details_link = element.find('a', string=lambda text: text and text.strip().lower() == 'detalhes')
    if details_link and details_link.get('href'):
        return urljoin(BASE_URL, details_link['href'])
    
    # Verifica se o elemento pai é um link
    if element.parent and element.parent.name == 'a':
        parent_link = element.parent.get('href')
        if parent_link:
            return urljoin(BASE_URL, parent_link)
    
    return "N/A"

def _find_section_category(h3_element):
    """
    Tenta inferir a categoria do evento a partir do título da seção.
    
    Args:
        h3_element (BeautifulSoup): Elemento h3 do evento
        
    Returns:
        str: Categoria do evento ou "N/A"
    """
    section_h2 = h3_element.find_previous('h2')
    if section_h2 and section_h2.text.strip():
        return section_h2.text.strip()
    return "N/A"

# ============================================================================
# Função Principal
# ============================================================================

def scrape_visite_sao_paulo_events():
    """
    Extrai dados de eventos do site Visite São Paulo.
    
    Returns:
        list: Lista de dicionários contendo informações dos eventos.
              Retorna lista vazia se a extração falhar ou nenhum evento for encontrado.
    """
    logger.info(f"Iniciando extração de eventos do Visite São Paulo da URL: {EVENTS_URL}")
    events = []

    try:
        response = requests.get(EVENTS_URL, timeout=20, headers=HEADERS)
        response.raise_for_status()
        logger.info(f"URL acessada com sucesso: {EVENTS_URL}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar URL {EVENTS_URL}: {e}")
        return events

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Encontra todos os elementos h3 que podem ser títulos de eventos
    event_elements = soup.find_all('h3')
    logger.info(f"Encontrados {len(event_elements)} possíveis títulos de eventos (h3).")

    for h3_element in event_elements:
        # Inicializa o dicionário do evento com valores padrão
        event = {
            'title': "N/A",
            'description': "N/A (disponível no link oficial)",
            'date': "N/A",
            'time': "N/A",
            'location': "N/A (disponível no link oficial)",
            'category': "N/A",
            'official_event_link': "N/A",
            'source_site': BASE_URL
        }

        try:
            # Extrai o título do evento
            event_title = h3_element.text.strip()
            if not event_title or len(event_title) < 5:
                logger.debug(f"Pulando elemento h3, título muito curto ou vazio: '{event_title}'")
                continue
            
            event['title'] = event_title

            # Procura por data e link nos elementos próximos
            current_element = h3_element
            date_found = False

            # Verifica os próximos 5 elementos em busca de data e link
            for _ in range(5):
                next_sibling = current_element.find_next_sibling()
                if not next_sibling:
                    break
                current_element = next_sibling

                # Tenta encontrar a data
                if not date_found:
                    possible_date_text = ""
                    if current_element.name in ['p', 'span', 'div']:
                        possible_date_text = current_element.get_text(separator=' ', strip=True)
                    elif current_element.string and current_element.string.strip():
                        possible_date_text = current_element.string.strip()
                    
                    if possible_date_text:
                        date = _extract_date_from_text(possible_date_text)
                        if date != "N/A":
                            event['date'] = date
                            date_found = True
                            logger.debug(f"Data encontrada para '{event_title}': {event['date']}")

                # Tenta encontrar o link de detalhes
                details_link = _find_details_link(current_element)
                if details_link != "N/A":
                    event['official_event_link'] = details_link
                    logger.debug(f"Link de detalhes encontrado para '{event_title}': {event['official_event_link']}")
                    break

            # Tenta inferir a categoria do evento
            event['category'] = _find_section_category(h3_element)

            # Adiciona o evento se tiver informações mínimas necessárias
            if event['title'] != "N/A" and event['official_event_link'] != "N/A" and event['date'] != "N/A":
                events.append(event)
                logger.debug(f"Evento processado com sucesso: {event_title} | Data: {event['date']} | Link: {event['official_event_link']}")
            else:
                logger.debug(f"Evento ignorado: {event_title} - faltando data ou link (Data: {event['date']}, Link: {event['official_event_link']})")

        except Exception as e:
            logger.error(f"Erro ao processar elemento h3 '{h3_element.text.strip() if h3_element else 'H3 Desconhecido'}': {e}", exc_info=True)
            continue

    if not events:
        logger.info(f"Nenhum evento encontrado em {EVENTS_URL}.")
    else:
        logger.info(f"Extração do Visite São Paulo concluída. Encontrados {len(events)} eventos.")
    
    return events

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    # Configuração do logger para execução direta do script
    if not logger.handlers or not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        # Remove handlers existentes para evitar saídas duplicadas
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    logger.info("Iniciando teste do scraper do Visite São Paulo...")
    eventos = scrape_visite_sao_paulo_events()
    
    if eventos:
        logger.info(f"Encontrados {len(eventos)} eventos:")
        for i, evento in enumerate(eventos):
            logger.info(
                f"Evento {i+1}: "
                f"Título='{evento.get('title')}', "
                f"Data='{evento.get('date')}', "
                f"Link='{evento.get('official_event_link')}'"
            )
    else:
        logger.info("Nenhum evento encontrado. Isso pode ser devido a mudanças na estrutura do site, renderização via JavaScript, ou nenhum evento atual correspondendo aos critérios.") 