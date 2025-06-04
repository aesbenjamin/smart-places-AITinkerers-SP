# Documentação Técnica da Interface (`interface/`)

Este documento descreve o componente de interface do usuário para o Agente Cultural de São Paulo, implementado com Streamlit.

---

## `app.py`

### Propósito
O arquivo `app.py` implementa uma interface web interativa para o Agente Cultural de São Paulo. Utilizando a biblioteca Streamlit, ele permite que os usuários conversem com o agente, solicitem informações sobre eventos culturais, e visualizem os resultados, incluindo a localização dos eventos em um mapa.

### Principais Funcionalidades e Componentes

1.  **Configuração da Aplicação Streamlit**:
    *   Define o título da página (`Agente Cultural de São Paulo`), ícone e layout (`wide`).
    *   Apresenta um título principal e uma introdução sobre como usar o agente.

2.  **Gerenciamento de Estado da Sessão (`st.session_state`)**:
    *   `messages`: Lista que armazena o histórico da conversa (mensagens do usuário e do agente).
    *   `adk_session_id`: Armazena o ID da sessão ativa com o servidor ADK. É inicializado como `None` e obtido na primeira interação.
    *   `current_events_found`: Lista para guardar os dados estruturados dos eventos retornados pela ferramenta `find_cultural_events_unified` do agente.
    *   `error_message`: Armazena mensagens de erro para exibição na interface.

3.  **Layout da Interface**:
    *   A tela é dividida em duas colunas principais:
        *   `chat_col`: Ocupa dois terços da largura e contém a interface de chat.
        *   `map_col`: Ocupa um terço da largura e é usada para exibir o mapa e a tabela de eventos.

4.  **Comunicação com o Agente ADK (Backend)**:
    *   **`ADK_SESSION_URL`**: `http://localhost:8000/apps/agents/users/user/sessions` (para criar/obter sessões).
    *   **`ADK_RUN_SSE_URL`**: `http://localhost:8000/run_sse` (para enviar prompts e receber respostas via Server-Sent Events).
    *   **`create_adk_session()`**: Função para iniciar uma nova sessão com o ADK ou reutilizar uma existente. Envia um POST para `ADK_SESSION_URL` e armazena o ID da sessão em `st.session_state.adk_session_id`.
    *   **Interação com o Agente**: Quando o usuário envia uma mensagem:
        *   A mensagem é adicionada ao histórico local (`st.session_state.messages`).
        *   Um payload é construído contendo o `appName` ("agents"), `userId`, `sessionId` e a nova mensagem do usuário.
        *   Uma requisição POST é feita para `ADK_RUN_SSE_URL` com `stream=True` para receber eventos SSE.
        *   A resposta SSE é iterada linha por linha. As linhas `data:` são parseadas como JSON.
        *   O código procura por partes de texto (`"text"`) e respostas de função (`"functionResponse"`), especificamente da função `find_cultural_events_unified`.
        *   O texto do chat do agente é extraído para exibição. Os dados estruturados da resposta da função (contendo `chat_summary` e `events_found`) são armazenados.

5.  **Interface do Chat (`chat_col`)**:
    *   Exibe as mensagens do histórico (`st.session_state.messages`) usando `st.chat_message`.
    *   Utiliza `st.chat_input` para obter a nova mensagem do usuário.
    *   Exibe a resposta do agente, que pode ser um texto direto ou um resumo gerado a partir dos dados da ferramenta.

6.  **Visualização de Eventos (`map_col`)**:
    *   **`update_map_and_table()`**: Função chamada para processar e exibir os eventos.
    *   Se `st.session_state.current_events_found` contém eventos:
        *   Os eventos são geocodificados usando a função `geocode_events_list` do módulo `agents.utils.maps`. A geocodificação tenta obter coordenadas de latitude e longitude para cada evento.
        *   Eventos que puderam ser geocodificados são preparados para exibição no mapa.
        *   Um DataFrame do Pandas é criado com os campos `lat`, `lon`, `name`, `type`, `date_info` e `details_link`.
        *   `st.map(df_events_geocoded)` é usado para renderizar o mapa interativo.
        *   `st.dataframe(df_events_table)` exibe uma tabela com os detalhes dos eventos abaixo do mapa.
    *   Se nenhum evento for encontrado ou se houver erros, mensagens apropriadas são exibidas.

### Dependências Chave
-   `streamlit`: Para construir a interface web interativa.
-   `requests`: Para fazer requisições HTTP para o backend do ADK.
-   `pandas`: Para manipulação de dados tabulares e criação do DataFrame para o mapa e tabela.
-   `json`: Para parsear as respostas JSON do ADK.
-   Módulos locais:
    *   `agents.utils.maps.geocode_events_list`: Para geocodificar os endereços dos eventos.
    *   `agents.utils.logger.get_logger`: Para logging no backend da interface.

### Execução
-   Para executar esta interface, o servidor ADK (`adk web`) deve estar rodando (normalmente em `http://localhost:8000`).
-   A aplicação Streamlit é iniciada com o comando: `streamlit run interface/app.py` (executado a partir do diretório raiz do projeto).

### Fluxo de Interação Típico
1.  O usuário acessa a interface no navegador.
2.  A mensagem de boas-vindas é exibida.
3.  O usuário digita uma pergunta no chat (ex: "eventos para crianças no centro amanhã").
4.  Ao enviar, `create_adk_session()` garante que uma sessão ADK exista.
5.  A pergunta é enviada para o endpoint `ADK_RUN_SSE_URL`.
6.  A interface recebe e processa os eventos SSE:
    *   A resposta de texto do agente é exibida no chat.
    *   Se a ferramenta `find_cultural_events_unified` for chamada, os dados estruturados dos eventos são armazenados em `st.session_state.current_events_found`.
7.  A função `update_map_and_table()` é chamada (implicitamente pela re-execução do script Streamlit após o estado mudar).
8.  Os eventos em `current_events_found` são geocodificados.
9.  O mapa em `map_col` é atualizado com os eventos geocodificados, e a tabela de detalhes é exibida.

---
