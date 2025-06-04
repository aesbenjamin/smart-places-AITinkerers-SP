# Documentação dos Testes Automatizados

Este diretório (`/tests`) contém todos os testes automatizados para o projeto Agente Cultural de São Paulo. Os testes são escritos usando o framework `unittest` do Python e são projetados para garantir a corretude e a robustez dos diversos componentes do sistema.

## Visão Geral

Os testes são organizados em módulos que espelham a estrutura do diretório `agents/`:

*   `test_utils.py`: Testa os módulos utilitários.
*   `test_scrapers.py`: Testa os scrapers de coleta de dados.
*   `test_tools.py`: Testa as ferramentas utilizadas pelo agente.
*   `test_agents.py`: Testa a lógica principal e a inicialização do agente.

Cada módulo de teste normalmente:
1.  Configura um logger específico para registrar os resultados detalhados da execução dos testes em um arquivo de log dedicado (ex: `test_utils.log`).
2.  Adiciona o diretório raiz do projeto ao `sys.path` para permitir imports absolutos dos módulos sendo testados.
3.  Define classes de teste que herdam de `unittest.TestCase`.
4.  Utiliza o `unittest.mock` para isolar componentes e simular dependências externas (como APIs ou chamadas de LLM).
5.  Pode incluir uma função `run_all_<module>_tests()` e uma seção `if __name__ == '__main__':` para permitir a execução individual do conjunto de testes do módulo.

## Módulos de Teste

Abaixo, uma descrição detalhada de cada arquivo de teste:

### 1. `tests/test_utils.py`

*   **Propósito**: Verifica a funcionalidade dos módulos utilitários localizados em `agents/utils/`.
*   **Log**: `tests/test_utils.log`
*   **Principais Classes de Teste**:
    *   `TestConfig`: Testa o carregamento de configurações (`load_config`), a obtenção de chaves de API (`get_api_key`), e a recuperação de configurações do LLM (`get_llm_setting`) do arquivo `config.yaml`.
    *   `TestDateUtils`: Testa as funções de manipulação de datas, como `standardize_date_format` (para padronizar strings de data) e `parse_date` (para converter strings em objetos `datetime`).
    *   `TestEnvSetup`: Testa a configuração do ambiente, incluindo `setup_environment_variables_and_locale` e o carregamento do nome do modelo LLM (`_load_llm_model_name_from_config`).
    *   `TestLogger`: Testa a funcionalidade do `get_logger`, incluindo o cache de instâncias de logger.
    *   `TestMaps`: Testa as utilidades de geocodificação e busca de detalhes de locais (`get_geocode`, `get_place_details`, `geocode_events_list`), que interagem com APIs de mapas (geralmente Google Maps). Os testes são projetados para lidar com a ausência de chaves de API válidas, não falhando, mas registrando avisos.

### 2. `tests/test_scrapers.py`

*   **Propósito**: Verifica a funcionalidade dos scrapers web localizados em `agents/scrapers/`. O foco principal é garantir que os scrapers consigam buscar dados e que o formato dos dados retornados esteja correto.
*   **Log**: `tests/test_scrapers.log`
*   **Principais Classes de Teste**:
    *   `TestWikipediaMuseusScraper`: Testa o `scrape_wikipedia_museus_info` do `wikipedia_museus_scraper.py`. Verifica se a função retorna uma lista de dicionários, e se cada dicionário contém as chaves esperadas (`title`, `district`, `source_site`) com os tipos corretos.
    *   `TestVisiteSaoPauloScraper`: Testa o `scrape_visite_sao_paulo_events` do `visite_sao_paulo_scraper.py`. Valida o formato da saída, esperando uma lista de dicionários de eventos com chaves como `title`, `description`, `date`, `location`, etc.
    *   `TestFablabScraper`: Testa o `scrape_fablab_events` do `fablab_scraper.py`. Similarmente, verifica se a saída é uma lista de dicionários de eventos com as chaves e tipos de dados esperados.
    *   *Nota*: Os testes de scraper geralmente não mockam as requisições HTTP, dependendo da disponibilidade dos sites alvo. Eles são projetados para registrar avisos caso os scrapers não retornem dados, permitindo que o teste de formato do item seja pulado.

### 3. `tests/test_tools.py`

*   **Propósito**: Verifica a funcionalidade das ferramentas localizadas em `agents/tools/`. Essas ferramentas encapsulam a lógica de negócios que o agente utiliza para responder às consultas.
*   **Log**: `tests/test_tools.log`
*   **Principais Classes de Teste**:
    *   `TestCulturalEventFinder`: Testa a função principal `find_cultural_events_unified`. Este é um teste de integração mais complexo que mocka várias dependências, incluindo `get_expanded_location_terms`, `get_all_events_from_scrapers_with_memory`, `search_tavily`, `generate_response_from_llm`, e `web_search_memory`. Verifica o fluxo básico, o formato da saída (incluindo `chat_summary` e `events_found`) e se as descrições completas dos eventos são corretamente anexadas.
    *   `TestSearchWeb`: Testa a função `search_tavily` para busca na web. Utiliza mocks para o `TavilyClient` para simular respostas bem-sucedidas, ausência de chave API e exceções da API.
    *   `TestGetUserResponse`: Testa a função `generate_response_from_llm` que interage com o modelo de linguagem Gemini. Mocka o `genai.GenerativeModel` para simular diferentes respostas do LLM, incluindo JSONs válidos e inválidos, e exceções. Verifica se a função processa corretamente as respostas e estrutura os dados para o agente.
    *   `TestGetBairros`: Testa `get_expanded_location_terms`, que expande termos de localização (bairros, etc.), tanto com o LLM habilitado (mockando a resposta do LLM) quanto desabilitado (usando lógica de fallback).
    *   `TestDataAggregator`: Testa `get_all_events_from_scrapers_with_memory`. Verifica a lógica de cache (acertos e perdas), o acionamento dos scrapers quando o cache está vazio ou expirado, o processamento e padronização dos dados dos scrapers, e a resiliência a falhas em scrapers individuais.

### 4. `tests/test_agents.py`

*   **Propósito**: Verifica a configuração e inicialização do agente principal (`CulturalAgentSPImpl`) e outros componentes definidos em `agents/cultural_agent.py`.
*   **Log**: `tests/test_agents.log`
*   **Principais Classes de Teste**:
    *   `TestAgentInitialization`: Testa se o `root_agent` (uma instância de `CulturalAgentSPImpl`, que por sua vez é uma subclasse de `google.adk.agents.Agent`) é instanciado corretamente. Isso envolve mockar:
        *   `_load_llm_model_name_from_config` (de `agents.utils.env_setup`) para fornecer um nome de modelo.
        *   `get_agent_instruction` (de `agents.prompts`) para fornecer as instruções do agente.
        *   `google.adk.agents.Agent` para verificar os parâmetros de sua instanciação.
        *   `google.adk.tools.FunctionTool` para garantir que a ferramenta `find_cultural_events_unified` seja corretamente encapsulada e passada para o agente.
        *   Utiliza `importlib.reload` no módulo `agents.cultural_agent` para garantir que a lógica de inicialização do agente seja executada com os mocks ativos.
    *   `TestWelcomeHelper`: Testa a classe `WelcomeHelper` e seu método `get_welcome_message`, garantindo que a mensagem de boas-vindas padrão seja retornada corretamente.
    *   *(Removido)* `TestFindEventsFunction`: Anteriormente testava a função `find_events_with_metadata`, que foi refatorada. A funcionalidade agora é coberta pelos testes de `find_cultural_events_unified` em `TestCulturalEventFinder` e a integração da ferramenta com o agente em `TestAgentInitialization`.

## Executando os Testes

Para executar todos os testes, você pode usar o `pytest` na raiz do projeto ou executar os scripts individualmente:

```bash
# Executar todos os testes com pytest (recomendado)
pytest tests/

# Ou para executar um módulo de teste específico:
python tests/test_utils.py
python tests/test_scrapers.py
python tests/test_tools.py
python tests/test_agents.py
```

Verifique os arquivos `.log` no diretório `tests/` para uma saída detalhada de cada execução.
