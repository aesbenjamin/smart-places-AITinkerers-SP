"""
Interface do Agente Cultural de São Paulo
----------------------------------------
Este módulo implementa a interface web do Agente Cultural usando Streamlit.
Permite interação com o agente ADK para busca de eventos culturais e exibição
dos resultados em um mapa interativo.
"""

# ============================================================================
# Configuração do Ambiente e Imports
# ============================================================================

import streamlit as st
import datetime
import sys
import os
import requests
import json
import pandas as pd

# Ajusta o Python path para incluir o diretório raiz do projeto
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports locais
from agents.utils.maps import geocode_events_list
from agents.utils.logger import get_logger

# Configuração do logger
logger = get_logger(__name__)

# ============================================================================
# Configuração do Estado da Sessão
# ============================================================================

# Inicialização das variáveis de estado
if "messages" not in st.session_state:
    logger.debug("Initializing chat history in session_state.")
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Olá! Sou seu Agente Cultural. Como posso te ajudar a encontrar eventos em São Paulo?"
    }]

if "adk_session_id" not in st.session_state:
    logger.debug("Initializing adk_session_id in session_state.")
    st.session_state.adk_session_id = None

if "current_events_found" not in st.session_state:
    logger.debug("Initializing current_events_found in session_state.")
    st.session_state.current_events_found = []

# ============================================================================
# Configuração da Interface
# ============================================================================

# Configuração da página
st.set_page_config(
    page_title="Agente Cultural de São Paulo",
    page_icon="🎭",
    layout="wide"
)

# Cabeçalho com logo e informações da comunidade
col1, col2 = st.columns([1, 4])

with col1:
    # Logo da comunidade AI Tinkerers
    try:
        st.image("interface/img/aitink.png", width=120)
    except:
        st.markdown("🤖")  # Fallback se a imagem não carregar

with col2:
    st.title("🎭 Agente Cultural de São Paulo")
    st.markdown("**🌎 AI Tinkerers São Paulo (SP)**")


st.markdown("---")
st.markdown("Use o chat abaixo para interagir com o agente e descobrir eventos culturais, oficinas e exposições na cidade!")

# Mensagem de boas-vindas
st.markdown("""
    **Bem-vindo!**

    Esta interface permite que você converse com o Agente Cultural de São Paulo. 
    Utilize a caixa de chat abaixo para fazer suas perguntas sobre:
    - Tipos de eventos (shows, museus, exposições, etc.)
    - Datas específicas ou períodos (hoje, amanhã, próximo fim de semana, DD/MM/YYYY)
    - Localizações (bairros, pontos de referência, etc.)

    O agente tentará encontrar as melhores opções para você!
""")

# ============================================================================
# Configuração do Layout
# ============================================================================

# Divisão da tela em colunas (chat e mapa)
chat_col, map_col = st.columns([2, 1])  # Chat ocupa 2/3, Mapa 1/3

# ============================================================================
# Configuração do ADK
# ============================================================================

# Endpoints do servidor ADK
ADK_SESSION_URL = "http://localhost:8000/apps/agents/users/user/sessions"
ADK_RUN_SSE_URL = "http://localhost:8000/run_sse"

def create_adk_session():
    """
    Cria ou recupera uma sessão ADK.
    
    Returns:
        str: ID da sessão ADK ou None em caso de erro
    """
    if "adk_session_id" not in st.session_state or st.session_state.adk_session_id is None:
        try:
            logger.info(f"Criando nova sessão ADK em {ADK_SESSION_URL}")
            session_payload = {"appName": "agents", "userId": "user"}
            response = requests.post(ADK_SESSION_URL, json=session_payload, timeout=10)
            response.raise_for_status()
            session_data = response.json()
            
            if "id" in session_data:
                st.session_state.adk_session_id = session_data["id"]
                logger.info(f"ID da Sessão ADK: {st.session_state.adk_session_id}")
                return st.session_state.adk_session_id
            elif isinstance(session_data, list) and len(session_data) > 0 and "id" in session_data[0]:
                st.session_state.adk_session_id = session_data[0]["id"]
                logger.warning(f"Sessão ADK obtida de uma lista: {st.session_state.adk_session_id}")
                return st.session_state.adk_session_id
            else:
                logger.error(f"Formato de resposta da sessão ADK inesperado: {session_data}")
                st.session_state.adk_session_id = None
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao criar/obter sessão ADK: {e}")
            st.session_state.adk_session_id = None
            return None
    return st.session_state.adk_session_id

# ============================================================================
# Interface do Chat
# ============================================================================

with chat_col:
    st.header("Chat com Agente Cultural")

    # Exibe mensagens anteriores
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Processamento do input do chat
    if prompt := st.chat_input("Como posso te ajudar?"):
        agent_response_text = "Processando sua solicitação... ⏳"
        
        logger.info(f"User entered chat prompt: '{prompt}'")
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.current_events_found = []
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown(agent_response_text)
            
            session_id = create_adk_session()

            if not session_id:
                agent_response_text = "Falha ao iniciar uma sessão com o agente. Tente recarregar a página."
                st.session_state.current_events_found = []
            else:
                try:
                    # Prepara o payload para o ADK
                    payload = {
                        "appName": "agents",
                        "userId": "user",
                        "sessionId": session_id,
                        "newMessage": {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        },
                        "streaming": False
                    }
                    
                    logger.info(f"Enviando para o Agente ADK em {ADK_RUN_SSE_URL}")
                    st.session_state.current_events_found = []
                    st.session_state.error_message = None

                    parsed_agent_chat_text_from_sse = None
                    structured_response_data_from_tool = None

                    # Processa a resposta do ADK
                    try:
                        with requests.post(ADK_RUN_SSE_URL, json=payload, stream=True, headers={'Accept': 'text/event-stream'}) as response:
                            response.raise_for_status()
                            logger.info(f"Resposta SSE recebida do Agente ADK. Content-Type: {response.headers.get('Content-Type')}")
                            
                            for line in response.iter_lines():
                                if line:
                                    decoded_line = line.decode('utf-8')
                                    if decoded_line.startswith('data:'):
                                        json_data_str = decoded_line[len('data:'):].strip()
                                        try:
                                            sse_event_data = json.loads(json_data_str)
                                            content = sse_event_data.get("content")
                                            if content and isinstance(content.get("parts"), list):
                                                for part in content["parts"]:
                                                    if "functionResponse" in part:
                                                        function_response = part["functionResponse"]
                                                        if function_response.get("name") == "find_cultural_events_unified":
                                                            response_content = function_response.get("response")
                                                            if isinstance(response_content, dict):
                                                                structured_response_data_from_tool = response_content
                                                    elif "text" in part:
                                                        parsed_agent_chat_text_from_sse = part["text"]
                                        except json.JSONDecodeError:
                                            logger.warning(f"Falha ao decodificar JSON do evento SSE: {json_data_str}")
                                        except Exception as e_inner_sse:
                                            logger.error(f"Erro ao processar evento SSE: {e_inner_sse}")

                    except requests.exceptions.RequestException as e_http:
                        logger.error(f"Erro na requisição para o Agente ADK: {e_http}")
                        st.session_state.error_message = f"Erro de comunicação com o Agente: {e_http}"
                        agent_response_text = f"Erro de comunicação com o Agente. Verifique os logs e tente novamente."

                except Exception as e_outer:
                    logger.error(f"Erro geral no processamento do chat: {e_outer}", exc_info=True)
                    st.session_state.error_message = f"Ocorreu um erro inesperado no sistema: {e_outer}"
                    agent_response_text = "Ocorreu um erro inesperado ao processar sua solicitação."

                # Processa a resposta final
                if structured_response_data_from_tool:
                    chat_summary = structured_response_data_from_tool.get("chat_summary")
                    events_found = structured_response_data_from_tool.get("events_found", [])
                    
                    if chat_summary:
                        agent_response_text = chat_summary
                    elif parsed_agent_chat_text_from_sse:
                        agent_response_text = parsed_agent_chat_text_from_sse
                    elif not st.session_state.error_message:
                        agent_response_text = "Recebi uma resposta da ferramenta, mas sem um resumo claro. Veja os eventos no mapa, se houver."
                    
                    if events_found:
                        st.session_state.current_events_found = events_found
                        logger.info(f"{len(events_found)} eventos estruturados armazenados.")
                
                elif parsed_agent_chat_text_from_sse:
                    agent_response_text = parsed_agent_chat_text_from_sse
                
                elif st.session_state.error_message:
                    agent_response_text = st.session_state.error_message
                
                elif agent_response_text == "Processando sua solicitação... ⏳":
                    agent_response_text = "Não consegui obter uma resposta conclusiva do agente desta vez."

                # Atualiza a interface com a resposta
                placeholder.markdown(agent_response_text)
                if agent_response_text.strip():
                    if not st.session_state.messages or st.session_state.messages[-1]["content"] != agent_response_text:
                        st.session_state.messages.append({"role": "assistant", "content": agent_response_text})

                # Processa eventos para o mapa
                if st.session_state.current_events_found:
                    logger.info(f"Iniciando geocodificação de {len(st.session_state.current_events_found)} eventos.")
                    st.session_state.current_events_found = geocode_events_list(st.session_state.current_events_found)
                    logger.info(f"Geocodificação concluída. {sum(1 for ev in st.session_state.current_events_found if ev.get('latitude') is not None)} eventos com coordenadas.")

    # Informação sobre o projeto
    st.markdown("---")
    st.markdown("*Desenvolvido pela comunidade **🌎 AI Tinkerers São Paulo (SP)***")

# ============================================================================
# Interface do Mapa
# ============================================================================

with map_col:
    st.header("Mapa de Eventos")
    
    if st.session_state.current_events_found:
        events_with_coords = [
            event for event in st.session_state.current_events_found 
            if event.get('latitude') is not None and event.get('longitude') is not None
        ]
        
        if events_with_coords:
            logger.info(f"Exibindo mapa com {len(events_with_coords)} eventos geocodificados.")
            map_df = pd.DataFrame(events_with_coords)
            map_display_df = map_df[['latitude', 'longitude']].copy()
            
            # Coordenadas de São Paulo para centralização do mapa
            sp_lat, sp_lon = -23.550520, -46.633308
            avg_lat = map_df['latitude'].mean()
            avg_lon = map_df['longitude'].mean()

            st.map(map_display_df, latitude=avg_lat, longitude=avg_lon, zoom=11)
            
            # Lista detalhada dos eventos
            st.subheader("Detalhes dos Eventos Encontrados:")
            for event in events_with_coords:
                name = event.get('name', 'Nome não disponível')
                details_link = event.get('details_link')
                date_info = event.get('date_info', 'Data não informada')
                loc_details = event.get('location_details', 'Local não informado')
                event_type = event.get('type', 'Tipo não informado')
                full_description = event.get('full_description', 'Descrição não fornecida.')

                st.markdown(f"**{name}**")
                st.markdown(f"*Tipo:* {event_type} | *Data:* {date_info} | *Local:* {loc_details}")
                if details_link and isinstance(details_link, str) and details_link.startswith("http"):
                    st.markdown(f"[Mais Detalhes]({details_link})")
                
                with st.expander("Ver Descrição Completa"):
                    st.markdown(full_description if full_description else "Descrição não disponível.")
                st.divider()
        else:
            logger.info("Nenhum evento com coordenadas para exibir no mapa.")
            st.info("Não foram encontrados eventos com localização precisa para exibir no mapa.")
    else:
        st.info("Busque por eventos para vê-los aqui no mapa!")

# ============================================================================
# Tratamento de Erros
# ============================================================================

if "error_message" in st.session_state and st.session_state.error_message:
    st.error(st.session_state.error_message)

# ============================================================================
# Rodapé da Comunidade
# ============================================================================

# Sobre a comunidade
with st.expander("ℹ️ Sobre o AI Tinkerers São Paulo"):
    st.markdown("""
    **Missão:** Conectar e fortalecer a comunidade de desenvolvedores, engenheiros, pesquisadores e empreendedores de IA em São Paulo, promovendo a experimentação prática e o compartilhamento de conhecimento em aplicações inovadoras de IA generativa.
    
    **Público-alvo:** Profissionais técnicos ativos na construção de soluções com modelos fundacionais, LLMs, agentes autônomos, ferramentas de IA generativa e aplicações práticas de IA.
    """)


st.markdown("---")

col_footer1, col_footer2 = st.columns([1, 1])


with col_footer1:
    st.markdown("### 🌎 AI Tinkerers São Paulo")
    st.markdown("**📧 community@aitinkererssp.com**")
    st.markdown("*Conectando desenvolvedores e pesquisadores de IA em São Paulo*")

with col_footer2:
    st.markdown("### 🤖 Sobre este Projeto")
    st.markdown("Agente Cultural desenvolvido com:")
    st.markdown("• Google AI ADK & Gemini 2.0")
    st.markdown("• Streamlit & Python")
    st.markdown("• APIs de São Paulo")

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    main_app_logger = get_logger(__name__)
    main_app_logger.info("Interface Streamlit (app.py) executada diretamente. Para rodar com o servidor Streamlit: streamlit run interface/app.py")
