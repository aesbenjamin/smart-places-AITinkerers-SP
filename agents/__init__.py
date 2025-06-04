"""
Pacote de Agentes
----------------
Este pacote contém os agentes especializados do sistema, incluindo o agente cultural
responsável por processar e analisar eventos culturais.
"""
import os
import traceback

print("="*50)
print("DEBUG: Executando agents/__init__.py")
print(f"DEBUG: Tentando importar 'root_agent' de .cultural_agent e atribuí-lo a 'agent'")
try:
    from .cultural_agent import root_agent
    agent = root_agent
    print(f"DEBUG: Importação de 'root_agent' e atribuição a 'agent' bem-sucedida.")
    print(f"DEBUG: Tipo do 'agent': {type(agent)}")
    agent_name = getattr(agent, 'name', 'Nome não encontrado')
    print(f"DEBUG: Nome do 'agent': {agent_name}")
    __all__ = ['agent']
except ImportError as e_imp:
    print(f"DEBUG: ERRO DE IMPORTAÇÃO em agents/__init__.py: {e_imp}")
    print(f"DEBUG: Detalhes do erro de importação:")
    traceback.print_exc()

except Exception as e_gen:
    print(f"DEBUG: ERRO GERAL em agents/__init__.py ao importar/configurar 'agent': {e_gen}")
    print(f"DEBUG: Detalhes do erro geral:")
    traceback.print_exc()

else:
    print(f"DEBUG: 'agent' ({agent_name}) pronto para ser exportado em __all__.")
print("="*50) 