# Documentação Técnica do Pacote `agents.state`

Este documento fornece uma visão geral técnica dos módulos relacionados ao gerenciamento de estado dentro do pacote `agents.state`. Estes módulos são cruciais para manter informações temporárias ou em cache que o agente pode necessitar durante seu processamento.

---

## `__init__.py`

### Propósito
Este arquivo serve para marcar o diretório `state/` como um pacote Python. Isso é essencial para que o Python reconheça este diretório como um contêiner de módulos, permitindo importações usando a notação de pacote (por exemplo, `from agents.state import macro_state`).

### Conteúdo Principal
- Atualmente, o arquivo está vazio ou contém apenas um comentário. Para sua finalidade como inicializador de pacote, este conteúdo é suficiente.

### Exports
- N/A (o arquivo não define `__all__` e não possui código funcional para exportar).

---

## `macro_state.py`

### Propósito
Este módulo define classes para gerenciar diferentes aspectos do estado ou memória de longo prazo (dentro de uma sessão ou com um tempo de vida definido) do sistema do agente. Especificamente, ele implementa mecanismos de cache para dados coletados por scrapers e para resultados de buscas na web, ajudando a otimizar o desempenho e evitar requisições repetidas a fontes de dados externas.

### Principais Componentes

1.  **`ScraperMemory`**: 
    -   **Propósito**: Gerencia um cache em memória para a lista de eventos e informações de museus extraídos pelos diversos scrapers.
    -   **`__init__(self, refresh_interval_seconds: int = 3600)`**: Inicializa a memória com um intervalo de atualização (padrão de 1 hora). Os eventos são armazenados em `_events` e o último timestamp de atualização em `_last_updated`.
    -   **`get_events() -> List[Dict[str, Any]]`**: Retorna a lista de eventos atualmente em cache.
    -   **`update_events(self, new_events: List[Dict[str, Any]])`**: Substitui os eventos em cache pelos `new_events` e atualiza o `_last_updated`.
    -   **`should_refresh() -> bool`**: Verifica se o cache precisa ser atualizado, comparando o tempo desde a última atualização com o `_refresh_interval`. Retorna `True` se o cache estiver vazio ou se o intervalo de atualização tiver sido excedido.

2.  **`WebSearchMemory`**:
    -   **Propósito**: Gerencia um cache para os resultados de buscas na web (por exemplo, da API Tavily).
    -   **`__init__(self, refresh_interval_seconds: int = 1800)`**: Inicializa a memória de busca com um intervalo de atualização (padrão de 30 minutos). Os resultados são armazenados em `search_cache`, um dicionário onde as chaves são as queries de busca.
    -   **`add_results(self, query_key: str, results: List[Dict[str, Any]])`**: Adiciona ou atualiza os resultados para uma `query_key` específica no cache, armazenando também um `timestamp` da adição.
    -   **`get_results(self, query_key: str) -> Optional[List[Dict[str, Any]]]`**: Tenta recuperar os resultados para uma `query_key`. Se os resultados existirem e o `timestamp` não tiver expirado (comparado com `refresh_interval`), retorna os dados; caso contrário, remove os dados expirados do cache e retorna `None`.
    -   **`clear_all_cache(self)`**: Limpa completamente o `search_cache`.

### Dependências Chave
-   `time`: Para timestamps e controle de tempo de expiração no `ScraperMemory`.
-   `datetime`, `timedelta`: Para timestamps e controle de tempo de expiração no `WebSearchMemory`.
-   `typing`: Para anotações de tipo.

### Configuração e Uso
-   As instâncias dessas classes de memória são geralmente criadas e gerenciadas pelos módulos que dependem delas (por exemplo, `ScraperMemory` é usado em `agents.tools.data_aggregator` e `WebSearchMemory` em `agents.tools.cultural_event_finder`).
-   Os intervalos de atualização (`refresh_interval_seconds`) podem ser ajustados na instanciação para controlar a frequência com que os dados em cache são considerados obsoletos.

### Bloco de Testes (`if __name__ == '__main__':`)
-   O módulo inclui um bloco de testes que demonstra o uso e a lógica de expiração tanto para `ScraperMemory` quanto para `WebSearchMemory`, usando intervalos de tempo curtos para facilitar a verificação.

### Exports (`__all__`)
-   N/A (o módulo não define `__all__` explicitamente, mas as classes `ScraperMemory` e `WebSearchMemory` são destinadas ao uso por outros módulos do pacote `agents`).

---
