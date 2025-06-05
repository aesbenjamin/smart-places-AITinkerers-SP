#!/bin/bash

echo "============================================"
echo " Teste do Servidor ADK "
echo "============================================"

echo ""
echo "INFO: Verificando o módulo google.adk..."
python -c "from google import adk; print('✓ google.adk disponível')" 
if [ $? -ne 0 ]; then
    echo "✗ ERRO: google.adk não pode ser importado"
    exit 1
fi

echo ""
echo "INFO: Verificando dependências dos agentes..."
python -c "
import sys
sys.path.append('.')
try:
    import agents
    print('✓ Módulo agents disponível')
    agent = agents.agent
    print(f'✓ Agent carregado: {type(agent).__name__}')
except Exception as e:
    print(f'✗ Erro ao carregar agents: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "✗ ERRO: Falha ao carregar o módulo agents"
    exit 1
fi

echo ""
echo "INFO: Iniciando servidor ADK na porta 8000..."
echo "      Logs serão salvos em 'adk_test.log'"

> adk_test.log 
python -m google.adk.cli api_server --port=8000 --host=127.0.0.1 --log_level=info agents >> adk_test.log 2>&1 &
ADK_PID=$!

echo "INFO: Servidor iniciado com PID: $ADK_PID"
echo "      Aguardando 10 segundos para o servidor inicializar..."

sleep 10

echo ""
echo "INFO: Testando se o servidor está respondendo..."
curl -s -f http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Servidor ADK está respondendo em http://localhost:8000"
    echo ""
    echo "INFO: Teste de conexão com uma requisição de health check:"
    curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
else
    echo "✗ Servidor ADK não está respondendo"
    echo ""
    echo "INFO: Últimas linhas do log:"
    tail -20 adk_test.log
fi

echo ""
echo "INFO: Para parar o servidor, execute: kill $ADK_PID"
echo "INFO: Para ver os logs em tempo real: tail -f adk_test.log"
echo ""
echo "============================================" 