# utils/maps.py
"""
Utilitários para Interação com Google Maps
----------------------------------------
Este módulo fornece funções utilitárias para interagir com os serviços do Google Maps,
incluindo geocodificação de endereços e obtenção de detalhes de lugares.

O gerenciamento da chave da API é feito internamente através do carregamento do `config.yaml`.
"""

# ============================================================================
# Imports
# ============================================================================

import os
import sys
import googlemaps
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos
from agents.utils.config import load_config
from agents.utils.logger import get_logger

# ============================================================================
# Configuração do Logger
# ============================================================================

logger = get_logger(__name__)

# ============================================================================
# Constantes
# ============================================================================

# Valor placeholder para a chave da API no config.yaml
API_KEY_PLACEHOLDER = "YOUR_GOOGLE_MAPS_API_KEY_HERE"

# ============================================================================
# Funções Auxiliares
# ============================================================================

def _get_maps_api_key() -> str | None:
    """
    Função auxiliar para carregar e recuperar a chave da API do Google Maps do config.yaml.

    Verifica se a configuração pode ser carregada, se a seção 'api_keys' e
    a chave 'google_maps' existem, e se a chave não é o valor placeholder.
    Mensagens de erro apropriadas são registradas se problemas forem encontrados.

    Returns:
        str | None: A chave da API do Google Maps se encontrada e válida, caso contrário None.
    """
    config = load_config()
    if not config:
        logger.error("Falha ao carregar configuração para a chave da API do Maps.")
        return None

    api_key = config.get('api_keys', {}).get('google_maps')

    if not api_key:
        logger.error("Chave da API do Google Maps não encontrada na configuração (api_keys.google_maps).")
        return None
    if api_key == API_KEY_PLACEHOLDER:
        logger.error(f"Chave da API do Google Maps ainda é o valor placeholder ('{API_KEY_PLACEHOLDER}'). Por favor, atualize o config.yaml.")
        return None

    logger.debug("Chave da API do Google Maps recuperada com sucesso da configuração.")
    return api_key

# ============================================================================
# Funções Principais
# ============================================================================

def get_geocode(address: str) -> dict | None:
    """
    Geocodifica uma string de endereço para coordenadas de latitude e longitude usando a API do Google Maps.
    A chave da API é carregada automaticamente do `config.yaml`.

    Args:
        address (str): A string do endereço para geocodificar (ex: "Rua Augusta, São Paulo, SP").

    Returns:
        dict | None: Um dicionário com as chaves 'latitude' e 'longitude' se bem-sucedido
                     (ex: {'latitude': -23.5505, 'longitude': -46.6333}),
                     caso contrário None. Registra erros ou avisos em caso de falha.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return None

    if not address or not isinstance(address, str) or not address.strip():
        logger.error("Endereço para geocodificação está ausente ou é inválido.")
        return None

    gmaps = googlemaps.Client(key=api_key)
    logger.debug(f"Tentando geocodificar endereço: '{address}'")

    try:
        geocode_result = gmaps.geocode(address)

        if geocode_result and len(geocode_result) > 0:
            location = geocode_result[0]['geometry']['location']
            logger.info(f"Geocodificação bem-sucedida para '{address}': Lat {location['lat']}, Lng {location['lng']}")
            return {'latitude': location['lat'], 'longitude': location['lng']}
        else:
            logger.warning(f"Nenhum resultado de geocodificação encontrado para o endereço: {address}")
            return None

    except ApiError as e:
        logger.error(f"Erro na API do Google Maps durante geocodificação para '{address}': {e}", exc_info=True)
    except HTTPError as e:
        logger.error(f"Erro HTTP do Google Maps durante geocodificação para '{address}': {e}", exc_info=True)
    except Timeout:
        logger.error(f"Requisição à API do Google Maps expirou durante geocodificação para '{address}'.")
    except TransportError as e:
        logger.error(f"Erro de Transporte do Google Maps (problema de rede) durante geocodificação para '{address}': {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado durante geocodificação para '{address}': {e}", exc_info=True)

    return None

def get_place_details(place_id: str) -> dict | None:
    """
    Recupera informações detalhadas para um lugar específico usando seu ID do Google Maps.
    A chave da API é carregada automaticamente do `config.yaml`.

    Args:
        place_id (str): O ID do lugar no Google Maps (ex: "ChIJ0xR62sBfzpQR0g0yLNRAwNo").

    Returns:
        dict | None: Um dicionário contendo vários detalhes do lugar (nome, endereço, avaliação, etc.)
                     se bem-sucedido, caso contrário None. Registra erros ou avisos em caso de falha.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return None

    if not place_id or not isinstance(place_id, str) or not place_id.strip():
        logger.error("ID do lugar para busca de detalhes está ausente ou é inválido.")
        return None

    gmaps = googlemaps.Client(key=api_key)

    # Define os campos que você deseja solicitar.
    # Consulte a documentação da API de Detalhes do Lugar do Google Maps para todos os campos disponíveis.
    fields = [
        'name', 'formatted_address', 'rating', 'photo',
        'opening_hours', 'website', 'international_phone_number',
        'geometry',  # Para lat/lng
        'place_id'   # Bom ter para confirmação
    ]
    logger.debug(f"Tentando buscar detalhes do lugar para ID: '{place_id}' com campos: {fields}")

    try:
        place_details_result = gmaps.place(place_id=place_id, fields=fields)

        if place_details_result and place_details_result.get('result'):
            details = place_details_result['result']
            logger.info(f"Detalhes do lugar obtidos com sucesso para '{details.get('name', place_id)}' (ID: {place_id})")
            return details
        else:
            logger.warning(f"Nenhum detalhe do lugar encontrado para ID: {place_id}. Resposta: {place_details_result}")
            return None

    except ApiError as e:
        logger.error(f"Erro na API do Google Maps para ID '{place_id}': {e}", exc_info=True)
    except HTTPError as e:
        logger.error(f"Erro HTTP do Google Maps para ID '{place_id}': {e}", exc_info=True)
    except Timeout:
        logger.error(f"Requisição à API do Google Maps expirou para ID '{place_id}'.")
    except TransportError as e:
        logger.error(f"Erro de Transporte do Google Maps (problema de rede) para ID '{place_id}': {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado para ID '{place_id}': {e}", exc_info=True)

    return None

def geocode_events_list(events_data: list[dict[str, any]]) -> list[dict[str, any]]:
    """
    Itera sobre uma lista de dicionários de eventos, tenta geocodificar cada um
    usando o campo 'location_details' e adiciona 'latitude' e 'longitude'.

    Args:
        events_data: Uma lista de dicionários, onde cada dicionário representa
                     um evento e deve conter uma chave 'location_details' (str)
                     para geocodificação.

    Returns:
        A mesma lista de eventos, com chaves 'latitude' e 'longitude' adicionadas
        aos dicionários dos eventos que puderam ser geocodificados. Eventos que
        não puderam ser geocodificados não terão essas chaves (ou terão None).
    """
    if not events_data:
        logger.info("geocode_events_list: Recebida lista de eventos vazia ou None.")
        return []

    geocoded_events = []
    api_key = _get_maps_api_key()

    if not api_key:
        logger.error("geocode_events_list: Chave da API Google Maps não disponível. Não é possível geocodificar eventos.")
        for event in events_data:
            event['latitude'] = None
            event['longitude'] = None
        return events_data

    logger.info(f"geocode_events_list: Iniciando geocodificação para {len(events_data)} eventos.")
    for event in events_data:
        processed_event = event.copy()
        location_str = processed_event.get('location_details')

        if location_str and isinstance(location_str, str) and location_str.strip():
            logger.debug(f"Geocodificando: '{location_str}' para o evento '{processed_event.get('name', 'N/A')}'")
            coords = get_geocode(location_str)
            if coords:
                processed_event['latitude'] = coords.get('latitude')
                processed_event['longitude'] = coords.get('longitude')
                logger.info(f"Sucesso ao geocodificar '{location_str}': Lat {coords.get('latitude')}, Lng {coords.get('longitude')}")
            else:
                processed_event['latitude'] = None
                processed_event['longitude'] = None
                logger.warning(f"Falha ao geocodificar '{location_str}' para o evento '{processed_event.get('name', 'N/A')}'")
        else:
            processed_event['latitude'] = None
            processed_event['longitude'] = None
            logger.warning(f"Campo 'location_details' ausente, vazio ou inválido para o evento '{processed_event.get('name', 'N/A')}'. Pulando geocodificação.")

        geocoded_events.append(processed_event)

    logger.info(f"geocode_events_list: Geocodificação concluída. {sum(1 for e in geocoded_events if e.get('latitude') is not None)} eventos geocodificados com sucesso.")
    return geocoded_events

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    print("\n=== Testes dos Utilitários do Google Maps ===\n")
    
    # Carrega configuração e chave da API
    config = load_config()
    api_key = config.get('api_keys', {}).get('google_maps') if config else None

    if api_key and api_key != API_KEY_PLACEHOLDER:
        gmaps_client = googlemaps.Client(key=api_key)
        
        # Teste de Geocodificação
        print("\n--- Teste de Geocodificação ---")
        endereco_teste = "Museu de Arte de São Paulo Assis Chateaubriand - MASP, Avenida Paulista, 1578, Bela Vista, São Paulo"
        resultado_geocode = get_geocode(endereco_teste)
        if resultado_geocode:
            print(f"Geocodificação para '{endereco_teste}': {resultado_geocode}")

        # Teste de Detalhes do Lugar
        print("\n--- Teste de Detalhes do Lugar ---")
        try:
            print(f"Buscando ID do lugar para: {endereco_teste}")
            resultado_busca = gmaps_client.find_place(
                input=endereco_teste,
                input_type='textquery',
                fields=['place_id', 'name']
            )
            
            if resultado_busca and resultado_busca.get('candidates'):
                candidato = resultado_busca['candidates'][0]
                place_id = candidato.get('place_id')
                nome_lugar = candidato.get('name')
                print(f"ID do lugar encontrado para '{nome_lugar}': {place_id}")
                
                detalhes = get_place_details(place_id)
                if detalhes:
                    print("\nDetalhes do lugar:")
                    print(f"  Nome: {detalhes.get('name')}")
                    print(f"  Endereço: {detalhes.get('formatted_address')}")
                    print(f"  Avaliação: {detalhes.get('rating', 'N/A')}")
                    if 'opening_hours' in detalhes and isinstance(detalhes['opening_hours'], dict):
                        print(f"  Horário de Funcionamento: {detalhes['opening_hours'].get('weekday_text', 'N/A')}")
            else:
                print(f"Não foi possível encontrar o ID do lugar para o MASP. Resposta: {resultado_busca}")
        except Exception as e:
            print(f"Erro ao buscar ID do lugar para o MASP: {e}")

        # Teste de Geocodificação de Lista de Eventos
        print("\n--- Teste de Geocodificação de Lista de Eventos ---")
        eventos_teste = [
            {"name": "Evento no MASP", "location_details": "Museu de Arte de São Paulo Assis Chateaubriand, Avenida Paulista, 1578, Bela Vista, São Paulo", "type": "Exposição"},
            {"name": "Show no Parque Ibirapuera", "location_details": "Parque Ibirapuera, São Paulo", "type": "Show"},
            {"name": "Peça no Teatro Renault", "location_details": "Teatro Renault, Av. Brigadeiro Luís Antônio, 411 - República, São Paulo", "type": "Teatro"},
            {"name": "Evento em Local Desconhecido", "location_details": "Ksvjbnksadv Asdkjvb Asdkjbv", "type": "Outro"},
            {"name": "Evento sem local", "location_details": None, "type": "Palestra"},
            {"name": "Evento com local vazio", "location_details": " ", "type": "Workshop"}
        ]
        
        eventos_geocodificados = geocode_events_list(eventos_teste)
        print("\nResultados da geocodificação:")
        for i, evento in enumerate(eventos_geocodificados):
            print(f"  Evento {i+1}: {evento.get('name')}")
            print(f"    Local: {evento.get('location_details')}")
            print(f"    Coordenadas: Lat {evento.get('latitude')}, Lng {evento.get('longitude')}")
    else:
        print("\nAVISO: Testes da API do Google Maps não serão executados.")
        if not config:
            print("Motivo: Não foi possível carregar a configuração (verifique os logs de utils.config).")
        elif not api_key:
            print("Motivo: Chave da API do Google Maps não encontrada no config.yaml (api_keys.google_maps).")
        elif api_key == API_KEY_PLACEHOLDER:
            print(f"Motivo: Chave da API no config.yaml ainda é o valor placeholder ('{API_KEY_PLACEHOLDER}').")
        print("\nPara executar os testes, configure uma chave válida da API do Google Maps no config.yaml")
        print("e certifique-se de que as APIs de Geocodificação e Places estão habilitadas.")

# ============================================================================
# Exports
# ============================================================================

__all__ = ['get_geocode', 'get_place_details', 'geocode_events_list']
