#!/bin/bash

# Script para iniciar a API do Agente Cultural e a UI Streamlit

echo "----------------------------------------------------"
echo " Iniciando o Agente Cultural e a Interface Web "
echo "----------------------------------------------------"
echo ""

# Define o nome do ambiente virtual
VENV_DIR="venv"

# Verifica se o diretório do ambiente virtual existe
if [ ! -d "$VENV_DIR" ]; then
    echo "INFO: Ambiente virtual '$VENV_DIR' não encontrado. Criando..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao criar o ambiente virtual '$VENV_DIR'. Verifique se python3 e venv estão instalados."
        exit 1
    fi
    echo "INFO: Ambiente virtual '$VENV_DIR' criado com sucesso."
else
    echo "INFO: Ambiente virtual '$VENV_DIR' encontrado."
fi

echo ""
echo "INFO: Ativando ambiente virtual '$VENV_DIR'..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao ativar o ambiente virtual '$VENV_DIR'."
    exit 1
fi

echo ""
echo "INFO: Instalando/atualizando dependências do requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "AVISO: Falha ao instalar algumas dependências do requirements.txt. Tentando forçar a instalação do google-adk."
fi

echo ""
echo "INFO: Tentando instalar/reinstalar google-adk especificamente..."
pip install --force-reinstall --no-cache-dir google-adk
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar/reinstalar google-adk. Verifique a saída acima."
    exit 1
fi

echo ""
echo "INFO: Verificando se o módulo google.adk pode ser importado..."
python -c "from google import adk; print('google.adk disponível')" 
if [ $? -ne 0 ]; then
    echo "ERRO CRÍTICO: O módulo google.adk não pôde ser importado mesmo após a tentativa de instalação."
    echo "            Verifique as mensagens de erro acima e o arquivo requirements.txt."
    echo "            O servidor ADK provavelmente não iniciará."
    # Continuamos para tentar iniciar o servidor, mas é provável que falhe.
else
    echo "INFO: Módulo google.adk importado com sucesso."
fi

echo ""
echo "INFO: Iniciando o servidor do Agente Cultural (ADK) em segundo plano..."
echo "      Logs do servidor ADK serão salvos em 'adk_server.log'"
# Limpa o log antigo antes de iniciar
> adk_server.log 
python -m google.adk.cli api_server --port=8000 --host=127.0.0.1 agents >> adk_server.log 2>&1 &
ADK_PID=$!
echo "INFO: Servidor ADK iniciado com PID: $ADK_PID."
echo "      Acesse a API em: http://localhost:8000 (se padrão)"

# Adiciona uma pequena pausa para dar tempo ao servidor ADK de iniciar
sleep 5

echo ""
echo "INFO: Iniciando a interface Streamlit..."
# A interface Streamlit geralmente roda na porta 8501
streamlit run interface/app.py

# Ao finalizar o Streamlit (Ctrl+C), parar o servidor ADK
echo ""
echo "INFO: Interface Streamlit finalizada."
echo "INFO: Parando o servidor ADK (PID: $ADK_PID)..."
if kill $ADK_PID > /dev/null 2>&1; then
  echo "INFO: Servidor ADK parado com sucesso."
else
  echo "AVISO: Não foi possível parar o servidor ADK automaticamente (PID: $ADK_PID)."
  echo "       Verifique o arquivo 'adk_server.log' para possíveis erros."
  echo "       Pode ser necessário pará-lo manualmente se ainda estiver em execução."
fi

echo ""
echo "----------------------------------------------------"
echo " Serviços finalizados. "
echo "----------------------------------------------------" 