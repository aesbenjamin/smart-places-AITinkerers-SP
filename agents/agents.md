# Visão Geral da Estrutura do Pacote `agents`

Este pacote (`agents/`) contém todos os componentes necessários para o funcionamento do Agente Cultural de São Paulo (`CulturalAgentSP`). A seguir, uma descrição de seus principais diretórios e arquivos, com referências para suas documentações técnicas detalhadas.

## Estrutura de Subdiretórios

1.  **`agents/utils/`**
    *   **Descrição**: Contém módulos utilitários que fornecem funcionalidades de suporte reusáveis em todo o projeto do agente. Isso inclui configuração, manipulação de datas, configuração de ambiente (chaves de API, locale), e o sistema de logging (incluindo o logger de sessão CSV).
    *   **Documentação Detalhada**: [`utils/utils.md`](./utils/utils.md)

2.  **`agents/tools/`**
    *   **Descrição**: Abriga os módulos que definem as ferramentas específicas que o agente pode utilizar para realizar tarefas. Cada ferramenta geralmente encapsula uma lógica de negócios ou capacidade de interação com dados/APIs, como busca de eventos culturais, agregação de dados, busca na web, etc.
    *   **Documentação Detalhada**: [`tools/tools.md`](./tools/tools.md)

3.  **`agents/state/`**
    *   **Descrição**: Módulos responsáveis pelo gerenciamento de estado ou memória de curto/médio prazo do agente. Implementa mecanismos de cache para dados coletados (como resultados de scrapers ou buscas na web) para otimizar o desempenho e evitar requisições repetidas.
    *   **Documentação Detalhada**: [`state/state.md`](./state/state.md)

4.  **`agents/scrapers/`**
    *   **Descrição**: Contém os scrapers web, cada um projetado para extrair informações de fontes de dados online específicas (por exemplo, sites de eventos, portais de cultura, Wikipédia). Os dados coletados alimentam as ferramentas e o conhecimento do agente.
    *   **Documentação Detalhada**: [`scrapers/scrapers.md`](./scrapers/scrapers.md)

5.  **`agents/logs_sessions/`**
    *   **Descrição**: Este diretório é o local designado para armazenar os arquivos CSV gerados pelo logger de sessão (`CsvSessionHandler`). Cada arquivo CSV contém um registro detalhado das interações de uma sessão específica do agente, incluindo entradas do usuário, respostas do agente e outras mensagens de log relevantes.
    *   **Documentação Detalhada**: A configuração do logger que cria esses arquivos está detalhada em `utils/logger_session_csv.py` (dentro de [`utils/utils.md`](./utils/utils.md)) e seu uso em `cultural_agent.py` (descrito abaixo).

## Componentes Principais do Agente (Nível Raiz de `agents/`)

Os seguintes arquivos e o arquivo de configuração YAML, localizados diretamente dentro de `agents/`, são cruciais para a definição, inicialização e operação do agente principal:

*   **`__init__.py`**: Inicializador do pacote `agents`, crucial para a descoberta do agente pelo ADK.
*   **`cultural_agent.py`**: Define a classe principal do agente (`CulturalAgentSPImpl`), sua lógica de processamento, e integra as ferramentas e prompts.
*   **`prompts.py`**: Centraliza as instruções textuais que guiam o comportamento do LLM do agente.
*   **`config.yaml`**: Arquivo de configuração para chaves de API e configurações do modelo de linguagem.

**Documentação Detalhada destes componentes**: Veja as seções subsequentes neste mesmo arquivo (`agents.md`).

---

# Documentação Técnica: Componentes Principais do Agente (`agents/`)

Este documento descreve os arquivos Python centrais que constituem o `CulturalAgentSP`, localizados diretamente no diretório `agents/`. Ele cobre o inicializador do pacote, a definição principal do agente e os prompts que guiam seu comportamento.

---

## `__init__.py` (no diretório `agents/`)

### Propósito
Este arquivo é crucial para o framework ADK (Agent Development Kit) descobrir e carregar o agente. Ele importa a instância principal do agente (`root_agent`) do módulo `cultural_agent.py` e a expõe como `agent`. Isso permite que o ADK encontre o agente ao inspecionar o pacote `agents`.

### Conteúdo Principal
-   Importa `root_agent` de `.cultural_agent`.
-   Atribui `root_agent` a uma variável chamada `agent`.
-   Define `__all__ = ['agent']` para explicitamente declarar qual objeto é exportado quando o pacote `agents` é importado (por exemplo, pelo ADK).
-   Inclui instruções de `print` para fins de depuração durante o carregamento do módulo, mostrando o sucesso ou falha da importação e o nome do agente carregado.

### Funcionamento com ADK
-   Quando o ADK é iniciado (por exemplo, com `adk web`), ele procura por pacotes de agentes. O `__init__.py` no diretório `agents` é executado.
-   A variável `agent` (que referencia a instância `CulturalAgentSPImpl`) é disponibilizada para o ADK, permitindo que o agente seja listado e utilizado na interface do ADK.

### Dependências
-   `.cultural_agent`: Módulo de onde o `root_agent` é importado.
-   `traceback`: Usado para imprimir detalhes de erros de importação durante a depuração.

### Exports
-   `agent`: A instância principal do `CulturalAgentSPImpl`.

---

## `cultural_agent.py`

### Propósito
Este é o coração do `CulturalAgentSP`. Ele define a classe principal do agente, sua lógica de processamento de interações, as ferramentas que utiliza e como ele é inicializado e configurado para uso com o Google ADK.

### Principais Componentes

1.  **`CulturalAgentSPImpl(Agent)`**:
    *   **Herança**: Herda da classe `Agent` do `google.adk.agents`.
    *   **Propósito**: Implementação personalizada do agente que inclui lógica para gerenciamento de logs de sessão usando `contextvars`.
    *   **`_run_async_impl(self, ctx: Any) -> AsyncIterator[Any]`**: Método sobrescrito crucial.
        *   **Gerenciamento de ID de Sessão**: Antes de executar a lógica principal do agente (chamando `super()._run_async_impl(ctx)`), este método extrai o ID da sessão do `InvocationContext` (`ctx`). Ele tenta `ctx.session.id` primeiro, depois `ctx.user_id` como fallback, e por fim um ID genérico se nenhum for encontrado. O ID da sessão é então armazenado em um `ContextVar` (`current_session_id_var`) do módulo `utils.logger`.
        *   **Logging de Entrada/Saída**: Registra a entrada do usuário (de `ctx.user_content`) e a resposta do agente (de `event.content`) usando o logger da sessão, que agora inclui as colunas `user_input` e `agent_response` no CSV.
        *   **Limpeza**: Após a conclusão do processamento, o `ContextVar` do ID da sessão é resetado.

2.  **Inicialização do Agente (`root_agent`)**:
    *   Uma instância de `FunctionTool` é criada, encapsulando a função `find_cultural_events_unified` (do módulo `tools.cultural_event_finder`).
    *   O nome do modelo LLM para o ADK é carregado da configuração (`_load_llm_model_name_from_config`) ou um padrão (`DEFAULT_ADK_LLM_MODEL_NAME`) é usado.
    *   A instância `root_agent` é criada a partir de `CulturalAgentSPImpl` com:
        *   `name`: "CulturalAgentSP".
        *   `description`: Descrição do agente.
        *   `instruction`: Instruções específicas para o agente (de `prompts.get_agent_instruction()`).
        *   `global_instructions`: Instruções globais (de `prompts.get_global_instructions()`).
        *   `tools`: Lista contendo a `tool_instance` criada.
        *   `model`: Nome do modelo LLM a ser usado.

3.  **`WelcomeHelper` Class**:
    *   Uma classe simples para gerar mensagens de boas-vindas. Atualmente não integrada ao fluxo principal do ADK, mas usada no bloco de testes `if __name__ == "__main__":`.

4.  **Configuração de Ambiente e Logging**:
    *   `setup_environment_variables_and_locale()`: Chamado para carregar chaves de API e configurar o locale.
    *   `module_init_logger`: Um logger no nível do módulo, usado para logs antes que um ID de sessão específico esteja disponível.

### Dependências Chave
-   `google.adk.agents.Agent`: Classe base para o agente.
-   `google.adk.tools.FunctionTool`: Para registrar funções Python como ferramentas para o LLM.
-   `google.generativeai` (genai): SDK da Gemini, usado no bloco de testes.
-   Módulos locais:
    *   `.utils.logger`: Para logging, incluindo o `current_session_id_var` e `get_logger`.
    *   `.utils.env_setup`: Para carregar configurações.
    *   `.prompts`: Para obter as instruções do agente.
    *   `.tools.cultural_event_finder`: Para a ferramenta principal de busca de eventos.
-   `typing`: Para anotações de tipo.
-   `sys`, `os`, `datetime`, `timedelta`: Utilitários Python padrão.

### Bloco de Testes (`if __name__ == "__main__":`)
-   Permite executar o agente ou suas ferramentas de forma isolada para testes.
-   Configura a API Gemini (se a chave estiver disponível).
-   Imprime uma mensagem de boas-vindas.
-   Executa testes para a função `find_cultural_events_unified` com exemplos de queries.
-   Fornece instruções sobre como interagir com o agente via ADK.

### Exports (`__all__`)
-   `root_agent`: A instância configurada do `CulturalAgentSPImpl`.

---

## `prompts.py`

### Propósito
Este módulo centraliza todos os prompts de texto (instruções) usados para configurar o comportamento do LLM (Large Language Model) dentro do `CulturalAgentSP`.

### Principais Componentes

1.  **`GLOBAL_INSTRUCTIONS` (constante string)**:
    *   Define instruções de alto nível que se aplicam a todas as interações do agente.
    *   Atualmente, instrui o agente a atuar como um "agente de pesquisa cultural" focado em encontrar eventos em São Paulo.

2.  **`AGENT_INSTRUCTION` (constante string)**:
    *   Define instruções mais específicas para o `CulturalAgentSP`.
    *   Identifica o agente pelo nome.
    *   Descreve seu objetivo (ajudar usuários a encontrar eventos culturais, museus, etc.).
    *   Instrui explicitamente a usar a ferramenta `find_cultural_events_unified` para todas as buscas relacionadas a eventos.
    *   Especifica que a resposta da ferramenta deve ser retornada diretamente, sem formatação adicional pelo agente.
    *   Enfatiza a priorização de respostas em português brasileiro.

3.  **Funções de Acesso (`get_global_instructions`, `get_agent_instruction`)**:
    *   `get_global_instructions() -> str`: Retorna a string `GLOBAL_INSTRUCTIONS`.
    *   `get_agent_instruction() -> str`: Retorna a string `AGENT_INSTRUCTION`.
    *   Estas funções são usadas pelo `cultural_agent.py` para obter os prompts ao inicializar a instância do agente.

### Dependências
-   Nenhuma dependência externa ou de outros módulos do projeto.

### Configuração e Uso
-   As strings de instrução (`GLOBAL_INSTRUCTIONS`, `AGENT_INSTRUCTION`) são editadas diretamente neste arquivo para modificar o comportamento do agente.
-   O `cultural_agent.py` importa e chama as funções `get_global_instructions()` e `get_agent_instruction()`.

### Exports
-   As funções `get_global_instructions` e `get_agent_instruction` são exportadas implicitamente para uso por outros módulos.

---

## `config.yaml`

### Propósito
O arquivo `config.yaml` é o local centralizado para armazenar configurações críticas para a execução do agente e suas ferramentas, principalmente chaves de API e configurações do modelo de linguagem (LLM).

### Estrutura do Arquivo
O arquivo é dividido em seções principais:

1.  **`api_keys`**: 
    *   Esta seção agrupa todas as chaves de API necessárias para que o agente e suas ferramentas acessem serviços externos.
    *   **`google_maps`**: Chave da API do Google Maps, utilizada para funcionalidades de geocodificação e obtenção de detalhes de lugares (atualmente não implementado ativamente nas ferramentas, mas reservado).
    *   **`gemini_api_key`**: Chave da API do Google Gemini, essencial para o funcionamento do LLM que potencializa o agente e algumas de suas ferramentas (como `get_user_response` e a capacidade de compilação de resultados no `cultural_event_finder`).
    *   **`tavily_api_key`**: Chave da API do Tavily, usada pela ferramenta `search_web.py` (e indiretamente pelo `cultural_event_finder`) para realizar buscas na web.

2.  **`llm_settings`**:
    *   Esta seção define os parâmetros para o modelo de linguagem grande (LLM).
    *   **`model_name`**: Especifica qual modelo Gemini deve ser utilizado. O arquivo de exemplo sugere opções como `gemini-1.5-flash-latest`, `gemini-1.0-pro-latest`, ou `gemini-2.0-flash`. Esta configuração é lida por `agents.utils.config.get_llm_model_name()` e `agents.utils.env_setup._load_llm_model_name_from_config()` para configurar o agente ADK e outras ferramentas que possam usar um LLM diretamente.

### Utilização
-   O módulo `agents.utils.config.py` contém funções como `get_api_key(service_name: str)` e `get_llm_model_name()` que são responsáveis por carregar este arquivo YAML, parsear seu conteúdo e fornecer os valores de configuração para outras partes do sistema.
-   O módulo `agents.utils.env_setup.py` também utiliza `get_api_key` para popular variáveis de ambiente (`os.environ`) com as chaves de API no início da execução, tornando-as disponíveis para bibliotecas que esperam essas chaves como variáveis de ambiente (por exemplo, a SDK do Gemini).

### Segurança e Boas Práticas
-   **Não versionar chaves reais**: É crucial que o `config.yaml` contendo chaves de API reais **não seja versionado** em repositórios públicos (como o GitHub). Em vez disso, um arquivo de exemplo (`config.example.yaml` ou similar) com a estrutura e placeholders para as chaves deve ser versionado.
-   **Variáveis de Ambiente**: Para produção ou ambientes seguros, é preferível carregar chaves de API diretamente de variáveis de ambiente do sistema operacional em vez de arquivos de configuração, ou usar sistemas de gerenciamento de segredos.

### Dependências de Leitura
-   `PyYAML` (ou uma biblioteca similar de parsing de YAML) é necessária para que o Python possa ler e interpretar este arquivo. Essa dependência deve estar listada no `requirements.txt`.

---
