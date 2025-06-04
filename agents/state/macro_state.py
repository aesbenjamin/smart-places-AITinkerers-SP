"""
Gerenciamento de Estado do Sistema
--------------------------------
Este módulo implementa classes para gerenciar o estado do sistema, incluindo
cache de eventos extraídos por scrapers e resultados de buscas na web.
"""

# ============================================================================
# Imports
# ============================================================================

import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# ============================================================================
# Classes de Gerenciamento de Estado
# ============================================================================

class ScraperMemory:
    """
    Gerencia o cache de eventos extraídos pelos scrapers.
    
    Esta classe mantém uma lista de eventos em memória e controla quando
    eles precisam ser atualizados com base em um intervalo de tempo.
    """
    
    def __init__(self, refresh_interval_seconds: int = 3600):
        """
        Inicializa o gerenciador de memória dos scrapers.
        
        Args:
            refresh_interval_seconds (int): Intervalo em segundos para atualização
                                          dos eventos (padrão: 1 hora)
        """
        self._events: List[Dict[str, Any]] = []
        self._last_updated: float = 0.0
        self._refresh_interval: int = refresh_interval_seconds
        # Nota: Poderia adicionar um lock se o acesso for concorrente

    def get_events(self) -> List[Dict[str, Any]]:
        """
        Retorna a lista atual de eventos.
        
        Returns:
            List[Dict[str, Any]]: Lista de eventos armazenados
        """
        return self._events

    def update_events(self, new_events: List[Dict[str, Any]]):
        """
        Atualiza a lista de eventos e registra o momento da atualização.
        
        Args:
            new_events (List[Dict[str, Any]]): Nova lista de eventos
        """
        self._events = new_events
        self._last_updated = time.time()
        print(f"INFO (ScraperMemory): Memória de scrapers atualizada com {len(self._events)} eventos.")

    def should_refresh(self) -> bool:
        """
        Verifica se os eventos precisam ser atualizados.
        
        Returns:
            bool: True se os eventos precisam ser atualizados, False caso contrário
        """
        if not self._events:  # Se não tem eventos, precisa carregar
            return True
        return (time.time() - self._last_updated) > self._refresh_interval


class WebSearchMemory:
    """
    Gerencia o cache de resultados de buscas na web.
    
    Esta classe mantém um dicionário de resultados de busca, cada um com
    seu próprio timestamp de expiração.
    """
    
    def __init__(self, refresh_interval_seconds: int = 1800):
        """
        Inicializa o gerenciador de cache de buscas.
        
        Args:
            refresh_interval_seconds (int): Intervalo em segundos para expiração
                                          do cache (padrão: 30 minutos)
        """
        self.search_cache: Dict[str, Dict[str, Any]] = {}
        self.refresh_interval = timedelta(seconds=refresh_interval_seconds)

    def add_results(self, query_key: str, results: List[Dict[str, Any]]):
        """
        Adiciona ou atualiza resultados de busca no cache.
        
        Args:
            query_key (str): Chave da busca
            results (List[Dict[str, Any]]): Resultados da busca
        """
        self.search_cache[query_key] = {
            "timestamp": datetime.now(),
            "data": results
        }
        print(f"INFO (WebSearchMemory): Resultados da busca para '{query_key}' "
              f"adicionados/atualizados ({len(results)} resultados).")

    def get_results(self, query_key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtém resultados de busca do cache se ainda forem válidos.
        
        Args:
            query_key (str): Chave da busca
            
        Returns:
            Optional[List[Dict[str, Any]]]: Resultados da busca ou None se expirados
        """
        if query_key in self.search_cache:
            cached_item = self.search_cache[query_key]
            if datetime.now() - cached_item["timestamp"] < self.refresh_interval:
                print(f"INFO (WebSearchMemory): Retornando resultados cacheados para '{query_key}'.")
                return cached_item["data"]
            else:
                print(f"INFO (WebSearchMemory): Cache para '{query_key}' expirado. Removendo.")
                del self.search_cache[query_key]
        return None

    def clear_all_cache(self):
        """
        Limpa todo o cache de busca.
        """
        self.search_cache = {}
        print("INFO (WebSearchMemory): Todo o cache foi limpo.")

# ============================================================================
# Testes
# ============================================================================

if __name__ == '__main__':
    # Teste do ScraperMemory
    print("\n=== Testando ScraperMemory ===")
    sm = ScraperMemory(refresh_interval_seconds=5)  # Intervalo curto para teste
    print(f"Precisa atualizar scrapers? {sm.should_refresh()}")
    
    mock_events_batch1 = [{'id': 1, 'title': 'Evento A'}, {'id': 2, 'title': 'Evento B'}]
    sm.update_events(mock_events_batch1)
    print(f"Eventos na memória: {len(sm.get_events())}")
    print(f"Precisa atualizar scrapers? {sm.should_refresh()}")
    
    print("Esperando 6 segundos...")
    time.sleep(6)
    print(f"Precisa atualizar scrapers após espera? {sm.should_refresh()}")

    # Teste do WebSearchMemory
    print("\n=== Testando WebSearchMemory ===")
    wsm = WebSearchMemory(refresh_interval_seconds=10)  # Intervalo de 10s para teste
    
    # Teste 1: Busca inicial
    query1 = "eventos em SP"
    results1 = wsm.get_results(query1)
    print(f"Resultados para '{query1}' (inicial): {results1}")

    # Teste 2: Adicionar e recuperar resultados
    mock_search_results_1 = [{'title': 'Resultado Web 1', 'url': 'http://example.com/1'}]
    wsm.add_results(query1, mock_search_results_1)
    results1_after_add = wsm.get_results(query1)
    print(f"Resultados para '{query1}' (após adicionar): "
          f"{len(results1_after_add) if results1_after_add else 'Nenhum'}")

    # Teste 3: Múltiplas buscas
    query2 = "museus gratuitos"
    mock_search_results_2 = [{'title': 'Museu Grátis A'}, {'title': 'Museu Grátis B'}]
    wsm.add_results(query2, mock_search_results_2)
    results2_after_add = wsm.get_results(query2)
    print(f"Resultados para '{query2}' (após adicionar): "
          f"{len(results2_after_add) if results2_after_add else 'Nenhum'}")

    # Teste 4: Expiração do cache
    print("Esperando 5 segundos (cache de query1 ainda deve estar válido)...")
    time.sleep(5)
    results1_after_5s = wsm.get_results(query1)
    print(f"Resultados para '{query1}' (após 5s): "
          f"{len(results1_after_5s) if results1_after_5s else 'Nenhum'}")
    
    print("Esperando mais 6 segundos (cache de query1 deve expirar)...")
    time.sleep(6)  # Total 11s > 10s de refresh_interval
    results1_after_11s = wsm.get_results(query1)
    print(f"Resultados para '{query1}' (após 11s): {results1_after_11s}")

    # Teste 5: Cache ainda válido para outra query
    results2_still_valid = wsm.get_results(query2)
    print(f"Resultados para '{query2}' (ainda válido): "
          f"{len(results2_still_valid) if results2_still_valid else 'Nenhum'}")

    # Teste 6: Limpar cache
    wsm.clear_all_cache()
    print(f"Resultados para '{query2}' após limpar tudo: {wsm.get_results(query2)}")
