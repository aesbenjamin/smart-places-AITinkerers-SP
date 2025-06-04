# Documentação Técnica do Pacote `agents.utils`

Este documento fornece uma visão geral técnica dos módulos utilitários encontrados no pacote `agents.utils`. Cada seção abaixo descreve um arquivo `.py` específico dentro deste diretório.

---

## `__init__.py`

### Propósito
Este arquivo marca o diretório `utils/` como um pacote Python, permitindo que seus módulos sejam importados usando a sintaxe de pacote (por exemplo, `from agents.utils import config`).

### Conteúdo Principal
- O arquivo está atualmente vazio ou contém apenas comentários, o que é suficiente para sua função como inicializador de pacote.

### Exports
- N/A (não define `__all__` e não tem código funcional para exportar)

---

## `config.py`

### Propósito
Este módulo é responsável por carregar e gerenciar as configurações da aplicação a partir de um arquivo YAML (`config.yaml` localizado no diretório `agents/`). Ele fornece funções para acessar chaves de API e outras configurações de forma centralizada, incluindo um mecanismo de cache para evitar leituras repetidas do arquivo.

### Principais Componentes
-   **`load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]`**: Carrega o arquivo de configuração YAML. Utiliza um cache (`_config_cache`) para armazenar a configuração após a primeira leitura. Retorna um dicionário vazio em caso de erro ou se o arquivo não for encontrado.
-   **`get_api_key(service_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[str]`**: Obtém uma chave de API específica da seção `api_keys` da configuração carregada. Inclui um mapeamento para nomes de serviço curtos (ex: "gemini" para "gemini_api_key") e verifica por placeholders.
-   **`get_llm_setting(setting_name: str, default_value: Any = None, config: Optional[Dict[str, Any]] = None) -> Any`**: Obtém uma configuração da seção `llm_settings` da configuração.

### Dependências Chave
-   `yaml` (PyYAML): Para ler e parsear o arquivo de configuração YAML.
-   `os`, `sys`: Para manipulação de caminhos e modificação do `sys.path`.
-   `agents.utils.logger`: Para logging interno do módulo.

### Configuração e Uso
-   O caminho padrão para o arquivo de configuração é `agents/config.yaml`.
-   As chaves de API devem estar sob a chave `api_keys` no YAML.
-   As configurações de LLM devem estar sob a chave `llm_settings`.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Contém testes locais para verificar o carregamento da configuração, a obtenção de chaves de API, a recuperação de configurações do LLM e o funcionamento do cache.

### Exports (`__all__`)
-   `load_config`
-   `get_api_key`
-   `get_llm_setting`

---

## `date_utils.py`

### Propósito
Este módulo fornece funções utilitárias para manipulação, parsing e padronização de strings de data, com foco em formatos comuns em português brasileiro. O objetivo principal é converter diversas representações de datas para o formato `YYYY-MM-DD` ou para objetos `datetime`.

### Principais Componentes
-   **`parse_date(date_str: str) -> Optional[Tuple[datetime, datetime]]`**: Tenta converter uma string de data em uma tupla de objetos `datetime` (início, fim). Suporta vários formatos de data (ex: "20 de Janeiro de 2023", "20/01/2023") e intervalos (ex: "20 de Janeiro a 25 de Janeiro de 2023"). Retorna `None` se a conversão falhar.
-   **`standardize_date_format(date_str: str) -> Optional[str]`**: Tenta padronizar uma string de data para o formato `YYYY-MM-DD`. Retorna `None` se a string for vazia, "n/a" ou representar um intervalo. Se nenhum formato conhecido for compatível, retorna a string original.

### Dependências Chave
-   `datetime`, `timedelta` (do módulo `datetime`): Para manipulação de datas e horas.
-   `os`, `sys`: Para manipulação de caminhos.
-   `agents.utils.logger`: Para logging.

### Configuração e Uso
-   Para o correto parsing de nomes de meses por extenso em português (ex: "Janeiro"), o locale `pt_BR.UTF-8` deve ser configurado globalmente na aplicação (geralmente feito pelo módulo `env_setup.py`).

### Bloco de Testes (`if __name__ == '__main__':`)
-   Inclui um conjunto de casos de teste para a função `standardize_date_format`, cobrindo datas por extenso, formatos numéricos, formato ISO, intervalos e datas inválidas.

### Exports (`__all__`)
-   `standardize_date_format`
-   `parse_date`

---

## `env_setup.py`

### Propósito
Este módulo centraliza a configuração do ambiente da aplicação. Suas responsabilidades incluem o carregamento de chaves de API do `config.yaml` para variáveis de ambiente (`os.environ`) e a configuração do locale do sistema para `pt_BR.UTF-8`, essencial para a correta manipulação de datas em português.

### Principais Componentes
-   **`setup_environment_variables_and_locale()`**: Função principal que orquestra o carregamento da configuração (via `agents.utils.config`), define variáveis de ambiente para chaves de API (GOOGLE_API_KEY, TAVILY_API_KEY, GOOGLE_MAPS_API_KEY) e configurações de LLM, e tenta definir o `locale.LC_TIME` para `pt_BR.UTF-8`.
-   **`_set_env_var_from_config(key_name: str, config_service_name: str, config: Dict[str, Any])`**: Função auxiliar para obter uma chave de API do `config` e defini-la como uma variável de ambiente.
-   **`_set_llm_env_vars_from_config(config: Dict[str, Any])`**: Função auxiliar para definir variáveis de ambiente a partir da seção `llm_settings` do `config`.
-   **`_load_llm_model_name_from_config(default_model_name: str) -> str`**: Carrega o nome do modelo LLM do `config.yaml`, retornando um valor padrão se não encontrado.

### Dependências Chave
-   `os`, `sys`, `locale`: Módulos padrão do Python.
-   `agents.utils.config`: Para carregar a configuração e obter chaves/settings.
-   `agents.utils.logger`: Para logging.

### Configuração e Uso
-   Esta função `setup_environment_variables_and_locale()` é tipicamente chamada no início do ciclo de vida da aplicação (por exemplo, no `agents/cultural_agent.py`) para garantir que o ambiente esteja corretamente configurado antes que outras partes do sistema tentem acessar variáveis de ambiente ou necessitem do locale correto.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Contém testes para verificar se as variáveis de ambiente são definidas corretamente e se o locale é configurado. Também testa a função `_load_llm_model_name_from_config`.

### Exports (`__all__`)
-   `setup_environment_variables_and_locale`
-   `_load_llm_model_name_from_config`

---

## `logger.py`

### Propósito
Este módulo fornece um sistema de logging centralizado e configurável para a aplicação. Ele garante que todas as partes do código possam obter uma instância de logger padronizada, facilitando o rastreamento e a depuração. O logger é configurado para exibir mensagens no console (stdout) e, opcionalmente, em arquivos CSV por sessão.

### Principais Componentes
-   **`current_session_id_var: contextvars.ContextVar[Optional[str]]`**: Uma `ContextVar` que armazena o ID da sessão da interação atual do agente. É usada por `get_logger` para associar logs a uma sessão específica quando um ID não é fornecido explicitamente.
-   **`get_logger(name: str, session_id: Optional[str] = None) -> logging.Logger`**: Função principal para obter uma instância de `logging.Logger`.
    -   Utiliza um cache (`_configured_loggers`) para evitar a reconfiguração de loggers e a duplicação de handlers.
    -   Configura um `StreamHandler` para saída no console (apenas uma vez por nome de logger).
    -   Se `session_id` for fornecido ou estiver presente em `current_session_id_var`, adiciona um `CsvSessionHandler` (do módulo `logger_session_csv.py`) para gravar logs em um arquivo CSV específico da sessão.

### Dependências Chave
-   `logging`, `sys`, `contextvars`: Módulos padrão do Python.
-   `agents.utils.logger_session_csv.CsvSessionHandler`: Para o logging de sessão em CSV.

### Configuração e Uso
-   **Nível de Log Padrão**: `LOG_LEVEL = logging.INFO`
-   **Formato de Log Padrão**: `LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'`
-   Para usar o logger, importe `get_logger` e chame-o com `__name__` do módulo atual: `logger = get_logger(__name__)`.
-   Para logging de sessão, o `session_id` pode ser passado explicitamente para `get_logger`, ou `current_session_id_var` pode ser definido (geralmente feito no `cultural_agent.py`).

### Bloco de Testes (`if __name__ == '__main__':`)
-   Inclui testes para verificar mensagens básicas de log, múltiplos loggers, o cache de loggers e o uso de `contextvars` para logging de sessão.

### Exports (`__all__`)
-   `get_logger`

---

## `logger_session_csv.py`

### Propósito
Este módulo implementa um handler de logging personalizado, `CsvSessionHandler`, que escreve registros de log em arquivos CSV. Cada arquivo CSV é específico para uma sessão de interação com o agente, permitindo um rastreamento detalhado e isolado das atividades de cada sessão. Os arquivos são nomeados com a data e o ID da sessão (ex: `AAAA-MM-DD_session_id.csv`) e armazenados no diretório `agents/logs_sessions/`.

### Principais Componentes
-   **`CsvSessionHandler(logging.Handler)`**:
    -   **`__init__(self, session_id: str, logs_dir: str = DEFAULT_LOGS_SESSIONS_DIR)`**: Inicializa o handler, cria o diretório de logs se não existir, e configura o caminho do arquivo de log CSV específico da sessão.
    -   **`_open_file_and_writer(self)`**: Abre o arquivo CSV em modo de apêndice (`'a'`) e inicializa um `csv.writer`. Escreve o cabeçalho se o arquivo for novo. O cabeçalho inclui: `timestamp`, `session_id`, `level`, `module`, `function`, `message`, `user_input`, `agent_response`.
    -   **`emit(self, record: logging.LogRecord)`**: Formata e escreve um registro de log no arquivo CSV. Extrai `user_input` e `agent_response` do `LogRecord` se estiverem presentes (passados via argumento `extra` no logging).
    -   **`flush(self)`**: Garante que os dados sejam escritos no disco.
    -   **`close(self)`**: Fecha o arquivo de log.

### Dependências Chave
-   `logging`, `csv`, `os`, `datetime`: Módulos padrão do Python.

### Configuração e Uso
-   O diretório padrão para os logs CSV é `agents/logs_sessions/`.
-   Este handler é tipicamente adicionado a um logger pela função `get_logger` no módulo `logger.py` quando um `session_id` é fornecido ou está disponível via `contextvars`.
-   Para registrar informações nas colunas `user_input` e `agent_response`, utilize o argumento `extra` ao chamar os métodos do logger: `logger.info("Mensagem", extra={"user_input": "input", "agent_response": "response"})`.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Contém um exemplo de uso que cria um logger de teste, adiciona o `CsvSessionHandler`, registra várias mensagens e testa o comportamento com e sem `session_id`.

### Exports (`__all__`)
-   N/A (o módulo é projetado para que a classe `CsvSessionHandler` seja importada e usada por outros módulos, como `logger.py`, mas não define `__all__` explicitamente).

---

## `maps.py`

### Propósito
Este módulo fornece utilitários para interagir com a API do Google Maps. Ele encapsula funcionalidades como geocodificação de endereços (converter endereço em coordenadas lat/lng) e obtenção de detalhes de lugares (informações sobre estabelecimentos). A chave da API do Google Maps é carregada automaticamente a partir do arquivo `config.yaml`.

### Principais Componentes
-   **`_get_maps_api_key() -> str | None`**: Função auxiliar interna para carregar a chave da API do Google Maps do `config.yaml` (via `agents.utils.config`). Verifica se a chave existe e não é um placeholder.
-   **`get_geocode(address: str) -> dict | None`**: Geocodifica uma string de endereço para coordenadas de latitude e longitude. Retorna um dicionário `{'latitude': ..., 'longitude': ...}` ou `None` em caso de falha.
-   **`get_place_details(place_id: str) -> dict | None`**: Recupera informações detalhadas para um lugar usando seu ID do Google Maps. Retorna um dicionário com os detalhes do lugar ou `None`. Os campos solicitados incluem nome, endereço, avaliação, fotos, horários, site, telefone e geometria.
-   **`geocode_events_list(events_data: list[dict[str, any]]) -> list[dict[str, any]]`**: Itera sobre uma lista de dicionários de eventos, tenta geocodificar cada um usando o campo `location_details` de cada evento, e adiciona as chaves `latitude` e `longitude` aos dicionários dos eventos.

### Dependências Chave
-   `googlemaps`: Biblioteca cliente oficial do Google Maps para Python.
-   `os`, `sys`: Para manipulação de caminhos.
-   `agents.utils.config`: Para carregar a chave da API.
-   `agents.utils.logger`: Para logging.

### Configuração e Uso
-   Uma chave válida da API do Google Maps deve ser configurada no arquivo `agents/config.yaml` sob `api_keys.google_maps`.
-   As funções lidam com exceções comuns da API (ApiError, HTTPError, Timeout, TransportError) e registram logs apropriados.

### Bloco de Testes (`if __name__ == '__main__':`)
-   Inclui um bloco para testes locais que permite testar as funcionalidades de geocodificação e busca de detalhes, assumindo que uma chave de API válida está configurada.

### Exports (`__all__`)
-   N/A (o módulo não define `__all__` explicitamente, mas suas funções públicas como `get_geocode`, `get_place_details`, e `geocode_events_list` são destinadas ao uso externo).

---
