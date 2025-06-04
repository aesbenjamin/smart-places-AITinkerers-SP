"""
Scraper para o FabLab Livre SP
-----------------------------
Este módulo implementa um scraper para extrair informações de eventos do site
do FabLab Livre SP (Prefeitura de São Paulo). O scraper busca cursos e eventos
disponíveis no portal e retorna os dados estruturados.
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

# URL base para busca de eventos
FABLAB_URL = "https://www.fablablivresp.prefeitura.sp.gov.br/busca?tipo=curso"
FABLAB_BASE_URL = "https://www.fablablivresp.prefeitura.sp.gov.br"

# Seletores CSS para diferentes estruturas de página
SELECTORS = {
    'event_cards': ['div.views-row', 'article.card-curso'],
    'date_fields': ['div[class*="date"]', 'div[class*="data"]', 'span[class*="date"]', 'span[class*="data"]'],
    'location_fields': ['div[class*="unidade"]', 'div[class*="location"]', 'span[class*="unidade"]', 'span[class*="location"]'],
    'tags_fields': ['div[class*="tags"]', 'div[class*="tematica"]', 'div[class*="area"]', 'div.field--name-field-tags']
}

# ============================================================================
# Funções Auxiliares
# ============================================================================

def _extract_title_and_link(card):
    """
    Extrai o título e link do evento de um card.
    
    Args:
        card (BeautifulSoup): Elemento HTML do card do evento
        
    Returns:
        tuple: (título, link) do evento
    """
    title_link_element = card.find('a', href=True, string=True)
    
    if title_link_element:
        title = title_link_element.text.strip()
        event_link = title_link_element.get('href')
        if event_link and event_link.startswith('http'):
            link = event_link
        elif event_link:
            link = f"https://www.fablablivresp.prefeitura.sp.gov.br{event_link}"
        else:
            link = "N/A"
    else:
        title = "N/A"
        link = "N/A"
    
    return title, link

def _extract_datetime(card, title_link_element):
    """
    Extrai data e hora do evento de um card.
    
    Args:
        card (BeautifulSoup): Elemento HTML do card do evento
        title_link_element (BeautifulSoup): Elemento do link do título
        
    Returns:
        tuple: (data, hora) do evento
    """
    datetime_text = ""
    
    # Tenta encontrar campo específico de data
    for selector in SELECTORS['date_fields']:
        date_field = card.select_one(selector)
        if date_field:
            datetime_text = date_field.text.strip()
            break
    
    # Fallback: busca por texto contendo '*' e '|'
    if not datetime_text:
        all_texts = card.find_all(string=True, recursive=False)
        for text_node in all_texts:
            cleaned_text = text_node.strip()
            if cleaned_text.startswith('*') and '|' in cleaned_text:
                datetime_text = cleaned_text.lstrip('*').strip()
                break
        
        if not datetime_text:
            all_texts_recursive = card.find_all(string=True)
            for text_node in all_texts_recursive:
                cleaned_text = text_node.strip()
                if cleaned_text.startswith('*') and '|' in cleaned_text:
                    if not title_link_element or (title_link_element and cleaned_text not in title_link_element.get_text(strip=True)):
                        datetime_text = cleaned_text.lstrip('*').strip()
                        break

    if datetime_text:
        if "|" in datetime_text:
            date_part, time_part = datetime_text.split("|", 1)
            return date_part.strip(), time_part.strip()
        return datetime_text, "N/A"
    return "N/A", "N/A"

def _extract_location(card, title_link_element):
    """
    Extrai a localização do evento de um card.
    
    Args:
        card (BeautifulSoup): Elemento HTML do card do evento
        title_link_element (BeautifulSoup): Elemento do link do título
        
    Returns:
        str: Localização do evento
    """
    location_element = None
    
    # Tenta encontrar campo específico de localização
    for selector in SELECTORS['location_fields']:
        location_field = card.select_one(selector)
        if location_field and location_field.find('a'):
            location_element = location_field.find('a')
            break
    
    # Fallback: usa o segundo link se existir
    if not location_element:
        all_links = card.find_all('a', href=True, string=True)
        if len(all_links) > 1 and all_links[1] != title_link_element:
            location_element = all_links[1]
    
    return location_element.text.strip() if location_element else "N/A"

def _extract_categories(card, location_element, title_link_element):
    """
    Extrai as categorias do evento de um card.
    
    Args:
        card (BeautifulSoup): Elemento HTML do card do evento
        location_element (BeautifulSoup): Elemento da localização
        title_link_element (BeautifulSoup): Elemento do link do título
        
    Returns:
        str: Categorias do evento separadas por vírgula
    """
    category_texts = []
    
    # Tenta encontrar campo específico de tags
    for selector in SELECTORS['tags_fields']:
        tags_container = card.select_one(selector)
        if tags_container:
            tag_links = tags_container.find_all('a')
            if tag_links:
                category_texts = [tag.text.strip() for tag in tag_links if tag.text.strip()]
            else:
                category_texts = [line.strip() for line in tags_container.text.split('\n') if line.strip() and len(line.strip()) > 1]
            if category_texts:
                break
    
    # Fallback: busca por texto próximo à localização
    if not category_texts and location_element:
        start_node = location_element.parent if location_element.parent else (title_link_element.parent if title_link_element.parent else None)
        if start_node:
            for sibling in start_node.find_next_siblings():
                sibling_text = sibling.get_text(separator=' ', strip=True)
                if sibling_text and len(sibling_text) < 50:
                    category_texts.append(sibling_text)
                if len(category_texts) >= 2:
                    break
    
    # Processa as categorias encontradas
    if category_texts:
        unique_categories = []
        seen_categories = set()
        for cat_text in category_texts:
            split_cats = [c.strip() for c in cat_text.replace('/', ',').split(',') if c.strip()]
            for cat in split_cats:
                if cat.lower() not in seen_categories:
                    unique_categories.append(cat)
                    seen_categories.add(cat.lower())
        return ", ".join(unique_categories)
    
    # Fallback final: infere categoria do título
    event_text_lower = card.find('a', href=True, string=True).text.strip().lower() if card.find('a', href=True, string=True) else ""
    if "oficina" in event_text_lower:
        return "Oficina"
    elif "palestra" in event_text_lower:
        return "Palestra"
    elif "curso" in event_text_lower:
        return "Curso"
    return "Outro"

# ============================================================================
# Função Principal
# ============================================================================

def scrape_fablab_events():
    """
    Extrai dados de eventos do site do FabLab Livre SP.
    
    Returns:
        list: Lista de dicionários contendo informações dos eventos.
              Retorna lista vazia se a extração falhar ou nenhum evento for encontrado.
    """
    events = []
    logger.info(f"Iniciando extração de eventos do FabLab da URL: {FABLAB_URL}")

    try:
        response = requests.get(FABLAB_URL, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar URL {FABLAB_URL}: {e}")
        return events

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Tenta encontrar cards de eventos usando diferentes seletores
    event_cards = None
    for selector in SELECTORS['event_cards']:
        event_cards = soup.select(selector)
        if event_cards:
            logger.info(f"Encontrados {len(event_cards)} cards de eventos usando seletor '{selector}'.")
            break
    
    if not event_cards:
        logger.warning(f"Nenhum card de evento encontrado em {FABLAB_URL}. A estrutura do site pode ter mudado.")
        return events

    # Processa cada card de evento
    for i, card in enumerate(event_cards):
        try:
            # Extrai informações básicas
            title, link = _extract_title_and_link(card)
            date, time = _extract_datetime(card, card.find('a', href=True, string=True))
            location = _extract_location(card, card.find('a', href=True, string=True))
            category = _extract_categories(card, card.find('a', href=True, string=True), card.find('a', href=True, string=True))

            # Cria dicionário do evento
            event = {
                'title': title,
                'official_event_link': link,
                'date': date,
                'time': time,
                'location': location,
                'categories': category,
                'description': "N/A (disponível no link oficial do evento)",
                'source_site': FABLAB_BASE_URL
            }

            # Adiciona à lista se informações essenciais estiverem presentes
            if title != "N/A" and link != "N/A":
                events.append(event)
            else:
                logger.debug(f"Card ignorado por falta de título ou link: {title}")

        except Exception as e:
            logger.error(f"Erro ao processar card de evento FabLab {i}: {e}", exc_info=True)
            continue
    
    if not events:
        logger.warning(f"Nenhum evento válido extraído do FabLab após processar os cards.")
    else:
        logger.info(f"Extração do FabLab concluída. Encontrados {len(events)} eventos.")
    
    return events

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

    logger.info("Iniciando scraper do FabLab para testes...")
    eventos = scrape_fablab_events()
    
    if eventos:
        logger.info(f"Encontrados {len(eventos)} eventos:")
        for i, evento in enumerate(eventos):
            logger.info(
                f"Evento {i+1}: "
                f"Título='{evento.get('title')}', "
                f"Data='{evento.get('date')}', "
                f"Local='{evento.get('location')}', "
                f"Categoria='{evento.get('categories')}'"
            )
    else:
        logger.info("Nenhum evento foi encontrado.")
