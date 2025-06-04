# Documentação Técnica do Pacote `agents.tools`

Este documento fornece uma visão geral técnica das ferramentas encontradas no pacote `agents.tools`. Cada seção abaixo descreve um arquivo `.py` específico dentro deste diretório, que geralmente corresponde a uma capacidade ou ferramenta específica do agente.

---

## `__init__.py`

### Propósito
Este arquivo marca o diretório `tools/` como um pacote Python. Isso permite que os módulos de ferramentas sejam importados usando a sintaxe de pacote (por exemplo, `from agents.tools import cultural_event_finder`).

### Conteúdo Principal
- O arquivo está atualmente vazio ou contém apenas comentários, o que é suficiente para sua função como inicializador de pacote.

### Exports
- N/A (não define `__all__` e não tem código funcional para exportar)

---

## `cultural_event_finder.py`

### Propósito
Este módulo implementa a principal ferramenta de busca do agente: `find_cultural_events_unified`. Ele orquestra a busca por eventos culturais, museus e atividades de lazer em São Paulo, combinando dados de diversas fontes.

### Principais Componentes
-   **`find_cultural_events_unified(event_type: Optional[str], date: Optional[str], location_query: Optional[str]) -> Dict[str, Any]`**:
    -   Esta é a função central exposta como uma ferramenta para o agente.
    -   **Expansão de Localização**: Utiliza `get_expanded_location_terms` para ampliar a consulta de localização do usuário.
    -   **Coleta de Dados de Scrapers**: Chama `get_all_events_from_scrapers_with_memory` para obter dados de eventos e museus coletados localmente.
    -   **Busca na Web**: Utiliza `search_tavily` para buscar informações adicionais ou mais atuais na web, caso uma chave da API Tavily esteja configurada. Os resultados são armazenados em `web_search_memory`.
    -   **Geração de Resposta com LLM**: Passa todos os dados coletados (localização expandida, dados de scrapers, resultados da web) para `generate_response_from_llm` para analisar e compilar uma lista de sugestões de eventos.
    -   **Anexação de Detalhes**: Após o LLM selecionar os eventos, a função anexa as descrições completas (obtidas dos dados originais dos scrapers ou da web) aos eventos retornados.
-   **`web_search_memory: WebSearchMemory`**: Uma instância para armazenar em cache os resultados de buscas na web realizadas por este módulo, evitando buscas repetidas.

### Dependências Chave
-   `agents.tools.search_web.search_tavily`
-   `agents.tools.get_bairros.get_expanded_location_terms`
-   `agents.tools.get_user_response.generate_response_from_llm`
-   `agents.tools.data_aggregator.get_all_events_from_scrapers_with_memory`
-   `agents.state.macro_state.WebSearchMemory`
-   `logging` (para logs internos do módulo)

### Configuração e Uso
-   A função `find_cultural_events_unified` é projetada para ser usada como uma `FunctionTool` pelo agente.
-   Requer que a chave da API Tavily (`TAVILY_API_KEY`) esteja disponível como variável de ambiente para que a busca na web funcione.
-   As outras dependências (como chaves para LLMs) são gerenciadas pelos módulos que elas invocam.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Contém um conjunto de casos de teste que simulam diferentes consultas do usuário para a função `find_cultural_events_unified`.

### Exports (`__all__`)
-   `find_cultural_events_unified`

---

## `data_aggregator.py`

### Propósito
Este módulo é responsável por agregar dados de eventos culturais e museus de diferentes fontes de scraping. Ele coleta, processa e padroniza essas informações, disponibilizando-as através de um cache em memória (`ScraperMemory`) para uso por outras ferramentas, como o `cultural_event_finder`.

### Principais Componentes
-   **`get_all_events_from_scrapers_with_memory() -> List[Dict[str, Any]]`**:
    -   Função principal que verifica se a memória de scrapers (`scraper_memory`) precisa ser atualizada.
    -   Se necessário, executa os scrapers configurados (`scrape_fablab_events`, `scrape_visite_sao_paulo_events`, `scrape_wikipedia_museus_info`).
    -   Para cada item coletado:
        -   Padroniza o campo de data usando `standardize_date_format`.
        -   Gera um ID único para o item.
        -   Chama funções auxiliares (`_process_museum_info`, `_process_fablab_location`, `_process_visite_sao_paulo_location`) para processar e adicionar campos específicos (como `bairro`).
    -   Atualiza a `scraper_memory` com os novos dados.
    -   Retorna a lista de todos os eventos/itens da memória.
-   **`scraper_memory: ScraperMemory`**: Instância que gerencia o cache dos dados dos scrapers, com um intervalo de atualização configurável (padrão: 3600 segundos).
-   **Funções Auxiliares de Processamento**:
    -   `_process_fablab_location(item: Dict[str, Any])`: Extrai o bairro da localização de eventos do FabLab.
    -   `_process_museum_info(item: Dict[str, Any])`: Padroniza campos para informações de museus da Wikipédia.
    -   `_process_visite_sao_paulo_location(item: Dict[str, Any])`: Processa a localização de eventos do Visite São Paulo.

### Dependências Chave
-   `agents.utils.logger.get_logger`
-   `agents.utils.date_utils.standardize_date_format`
-   `agents.state.macro_state.ScraperMemory`
-   Módulos de Scrapers:
    -   `agents.scrapers.fablab_scraper.scrape_fablab_events`
    -   `agents.scrapers.visite_sao_paulo_scraper.scrape_visite_sao_paulo_events`
    -   `agents.scrapers.wikipedia_museus_scraper.scrape_wikipedia_museus_info`

### Configuração e Uso
-   A lista de scrapers a serem executados está definida dentro de `get_all_events_from_scrapers_with_memory`.
-   O intervalo de atualização da memória é definido na instanciação de `ScraperMemory`.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Contém testes para a coleta completa de dados e para as funções de processamento específicas de cada fonte.

### Exports (`__all__`)
-   `get_all_events_from_scrapers_with_memory`

---

## `get_bairros.py`

### Propósito
Este módulo fornece a funcionalidade `get_expanded_location_terms`, que visa expandir um termo de localização fornecido pelo usuário (por exemplo, "Paulista") em uma lista de termos relacionados, como bairros adjacentes, nomes alternativos ou sinônimos. Isso ajuda a aumentar a abrangência das buscas por eventos.

### Principais Componentes
-   **`get_expanded_location_terms(location_query: str) -> Dict[str, List[str]]`**:
    -   Recebe uma consulta de localização.
    -   Se `SHOULD_USE_LLM` for `True` (o que depende do carregamento bem-sucedido da API Key do Gemini), utiliza um modelo LLM (Gemini) para gerar termos expandidos.
    -   O prompt para o LLM pede uma lista JSON de strings.
    -   Inclui funções auxiliares `_clean_llm_response` e `_parse_llm_response` para tratar a saída do LLM.
    -   Garante que o termo original sempre faça parte da lista final.
    -   Retorna um dicionário com a chave `"expanded_terms"` contendo a lista de termos.
-   **`_configure_api()`**: Tenta configurar a API do Gemini carregando a chave do `config.yaml` (chave `gemini_api_key`) ou da variável de ambiente `GOOGLE_API_KEY`. Define `API_KEY_LOADED` e `SHOULD_USE_LLM`.
-   **`_clean_llm_response(response_text: str) -> str`**: Remove marcadores de bloco de código e espaços extras da resposta do LLM.
-   **`_parse_llm_response(cleaned_text: str, location_query: str) -> List[str]`**: Tenta fazer o parse da resposta limpa do LLM como JSON ou, como fallback, como um literal Python (`ast.literal_eval`).

### Dependências Chave
-   `google.generativeai` (SDK do Gemini)
-   `yaml` (para carregar a configuração da API do `config.yaml`)
-   `ast`, `json` (para parsear a resposta do LLM)
-   `agents.utils.logger.get_logger`

### Configuração e Uso
-   A utilização do LLM para expansão de termos depende da disponibilidade e configuração correta da chave API do Gemini.
-   O prompt para o LLM é específico para a cidade de São Paulo.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Testa a função `get_expanded_location_terms` com uma lista de locais de exemplo em São Paulo.

### Exports (`__all__`)
-   N/A (não define `__all__` explicitamente, mas `get_expanded_location_terms` é a função principal destinada ao uso externo).

---

## `get_user_response.py`

### Propósito
Este módulo é central para a inteligência do agente na formulação de sugestões. A função `generate_response_from_llm` utiliza um modelo de linguagem generativa (LLM), como o Gemini, para analisar uma consulta do usuário, dados de eventos coletados (de scrapers e busca web) e gerar uma resposta estruturada em JSON. Essa resposta inclui uma lista de candidatos a eventos e, posteriormente, um resumo para o chat.

### Principais Componentes
-   **`generate_response_from_llm(user_query_details: Dict, scraped_events: List, web_search_results: List, max_suggestions: int) -> Dict[str, Any]`**:
    -   Constrói um prompt detalhado para o LLM, incluindo:
        -   Contextualização da tarefa e detalhes da consulta do usuário (tipo de interesse, data, localização original e expandida).
        -   Dados de eventos locais (scrapers) e resultados de busca na web.
        -   Instruções CRÍTICAS para o formato da saída JSON, que deve conter uma chave `"event_candidates"` com uma lista de objetos de evento. Cada objeto deve ter campos específicos: `id`, `name`, `location_details`, `type`, `date_info`, `source`, `details_link`.
    -   Chama o LLM (configurado para retornar `application/json`).
    -   Processa a resposta JSON do LLM.
    -   Se a resposta do LLM for válida, gera um "chat_summary" adicional, pedindo ao LLM para criar uma mensagem amigável para o usuário resumindo os achados.
    -   Retorna um dicionário com `"chat_summary"` e `"events_found"`.
-   **`_load_llm_config() -> Dict[str, str]`**: Carrega configurações do LLM (nome do modelo e chave API) do `config.yaml`.
-   **`_sanitize_string_for_prompt(text: Optional[Any]) -> str`**: Limpa e escapa strings para inclusão segura em prompts.

### Dependências Chave
-   `google.generativeai` (SDK do Gemini)
-   `yaml` (para carregar configurações)
-   `json` (para processar a resposta do LLM)
-   `agents.utils.logger.get_logger`

### Configuração e Uso
-   Requer a configuração da API do Gemini e o nome do modelo, preferencialmente via `config.yaml`.
-   O prompt é cuidadosamente construído para guiar o LLM a retornar um JSON estruturado e relevante.
-   A qualidade da resposta depende da qualidade dos dados de entrada e da capacidade do LLM de seguir as instruções.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Contém um exemplo de chamada para `generate_response_from_llm` com dados de teste mocados, demonstrando como a função pode ser usada e qual tipo de saída esperar.

### Exports (`__all__`)
-   N/A (não define `__all__` explicitamente, mas `generate_response_from_llm` é a função principal).

---

## `search_web.py`

### Propósito
Este módulo fornece uma interface para realizar buscas na web utilizando a API Tavily. Ele permite buscas gerais e avançadas, com opções para incluir ou excluir domínios específicos.

### Principais Componentes
-   **`search_tavily(query: str, api_key: Optional[str], max_results: int = 5, include_domains: List[str] = None, exclude_domains: List[str] = None) -> List[Dict[str, Any]]`**:
    -   Função principal que interage com o `TavilyClient`.
    -   Permite especificar a query, chave da API, número máximo de resultados e filtros de domínio.
    -   Utiliza o modo de busca "advanced" da Tavily.
    -   Retorna uma lista de dicionários, onde cada dicionário representa um resultado da busca, ou uma lista vazia em caso de erro.
-   **`load_tavily_api_key() -> str | None`**:
    -   Carrega a chave da API Tavily. Prioriza o arquivo `config.yaml` (chave `tavily_api_key` dentro de `api_keys`).
    -   Como fallback, tenta carregar da variável de ambiente `TAVILY_API_KEY`.
    -   Armazena a chave carregada na variável global `TAVILY_API_KEY` do módulo para possível reutilização (embora `search_tavily` requeira a chave como argumento).

### Dependências Chave
-   `tavily.TavilyClient` (da biblioteca `tavily-python`)
-   `yaml` (para carregar a chave do `config.yaml`)
-   `agents.utils.logger.get_logger`

### Configuração e Uso
-   Requer uma chave da API Tavily válida, que pode ser fornecida via `config.yaml` ou variável de ambiente.
-   A função `search_tavily` é usada por outras ferramentas (como `cultural_event_finder`) para enriquecer os dados com informações da web.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Inclui testes para a função `search_tavily`, demonstrando uma busca geral e uma busca com filtro de domínio, desde que a chave da API seja carregada com sucesso.

### Exports (`__all__`)
-   `search_tavily`
-   `load_tavily_api_key`

---
