# utils/logger.py
"""
Utilitário de Logging
-------------------
Este módulo fornece uma instância configurada de logger para uso consistente
em toda a aplicação. Garante que todas as partes da aplicação possam obter
facilmente um logger que exibe mensagens em um formato padronizado no console.

O módulo suporta configuração básica para nível de log e formato das mensagens,
mantendo um cache de loggers já configurados para evitar duplicação de handlers.
"""

# ============================================================================
# Imports
# ============================================================================

import logging
import sys
from typing import Optional
import contextvars

# Importa o CsvSessionHandler
from .logger_session_csv import CsvSessionHandler

# ============================================================================
# ContextVar para o ID da Sessão Atual
# ============================================================================

# Este ContextVar armazenará o session_id da interação atual do agente.
# get_logger o usará se um session_id não for explicitamente fornecido.
current_session_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_session_id_var", default=None)

# ============================================================================
# Configurações e Constantes
# ============================================================================

# Nível padrão de log para todos os loggers obtidos deste módulo
LOG_LEVEL = logging.INFO

# Formato padrão das mensagens de log
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Formato da data para as mensagens de log
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Cache de loggers já configurados para evitar adicionar múltiplos handlers
_configured_loggers = {}

# ============================================================================
# Funções Principais
# ============================================================================

def get_logger(name: str, session_id: Optional[str] = None) -> logging.Logger:
    """
    Obtém uma instância configurada de logger.

    Se um logger com o nome fornecido já foi configurado por esta função,
    retorna a instância existente. Caso contrário, cria e configura um novo
    logger. A configuração inclui definir o nível de log, criar um
    StreamHandler para saída no stdout e aplicar um formatador padrão.

    Args:
        name (str): Nome do logger. Tipicamente é o atributo `__name__`
                   do módulo chamador, o que ajuda a identificar a origem
                   das mensagens de log.
        session_id (Optional[str]): ID da sessão opcional. Se fornecido, ou se um ID de sessão
                                     estiver definido no ContextVar 'current_session_id_var',
                                     um CsvSessionHandler será adicionado.

    Returns:
        logging.Logger: A instância configurada do logger.

    Note:
        O logger é configurado para:
        - Usar o nível de log definido em LOG_LEVEL
        - Enviar todas as mensagens para stdout
        - Usar o formato padrão definido em LOG_FORMAT
        - Manter um cache de loggers já configurados
    """
    if name in _configured_loggers:
        # Mesmo que o logger base (com StreamHandler) já exista e esteja no cache,
        # ainda podemos precisar adicionar um CsvSessionHandler para uma nova sessão.
        logger = _configured_loggers[name]
    else:
        logger = logging.getLogger(name)
        logger.setLevel(LOG_LEVEL)
        _configured_loggers[name] = logger

    # Configura o handler de console (StreamHandler) apenas uma vez por nome de logger
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVEL)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Determina o ID da sessão a ser usado
    effective_session_id = session_id
    if effective_session_id is None:
        effective_session_id = current_session_id_var.get()

    # Adiciona CsvSessionHandler se um ID de sessão efetivo for encontrado
    if effective_session_id and effective_session_id.strip():
        session_handler_exists = False
        for h in logger.handlers:
            if isinstance(h, CsvSessionHandler) and h.session_id == effective_session_id:
                session_handler_exists = True
                break
        
        if not session_handler_exists:
            csv_handler = CsvSessionHandler(session_id=effective_session_id)
            if csv_handler.csv_writer:
                logger.addHandler(csv_handler)
            else:
                # Log de aviso usando o logger raiz para evitar problemas se o logger atual estiver sendo configurado
                logging.getLogger().warning(f"Falha ao inicializar CsvSessionHandler para logger '{name}' com session_id: {effective_session_id}. Logs CSV para esta sessão podem não ser gravados.")
    return logger

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    print("\n=== Testes do Utilitário de Logging ===\n")
    
    # Lista de casos de teste
    test_cases = [
        {
            "nome": "Teste de mensagens básicas",
            "descricao": "Testa diferentes níveis de mensagens de log"
        },
        {
            "nome": "Teste de múltiplos loggers",
            "descricao": "Testa a criação de loggers para diferentes módulos"
        },
        {
            "nome": "Teste de cache de loggers",
            "descricao": "Testa se o cache de loggers está funcionando corretamente"
        }
    ]
    
    # Executa os testes
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Teste {i}: {test_case['nome']} ---")
        print(f"Descrição: {test_case['descricao']}")
        
        try:
            if "básicas" in test_case['nome'].lower():
                logger_test = get_logger(__name__)
                logger_test.info("Esta é uma mensagem de informação (console).")
                logger_test.warning("Esta é uma mensagem de aviso (console).")
                logger_test.error("Esta é uma mensagem de erro (console).")

                # Teste com session_id
                session_logger_test = get_logger(__name__ + ".session_test", session_id="test_session_001")
                session_logger_test.info("Esta mensagem deve ir para o console E para o CSV da test_session_001.")
                session_logger_test.error("Este erro também deve ir para o console E para o CSV da test_session_001.")
                # Para evitar que os arquivos de log de teste fiquem abertos, fechamos explicitamente
                # Em uma aplicação real, o ciclo de vida dos handlers é mais complexo.
                for handler in session_logger_test.handlers:
                    if isinstance(handler, CsvSessionHandler):
                        handler.close()

            elif "múltiplos" in test_case['nome'].lower():
                logger_modulo1 = get_logger("ModuloTeste1")
                logger_modulo2 = get_logger("ModuloTeste2")
                logger_modulo1.info("Mensagem do Módulo 1")
                logger_modulo2.info("Mensagem do Módulo 2")
                
            elif "cache" in test_case['nome'].lower():
                logger1 = get_logger("TesteCache")
                logger2 = get_logger("TesteCache")
                if id(logger1) == id(logger2):
                    print("✓ Cache de loggers funcionando corretamente")
                else:
                    print("✗ Cache de loggers não está funcionando como esperado")
                
        except Exception as e:
            print(f"Erro durante o teste: {str(e)}")
        
        print("\n" + "="*50)
    
    print("\n--- Teste de ContextVar para session_id ---")
    TEST_SESSION_ID_CTX = "session_from_contextvar_67890"
    
    # Simula a configuração do ContextVar como um agente faria
    token = current_session_id_var.set(TEST_SESSION_ID_CTX)
    
    logger_ctx_test = get_logger("ContextVarTestLogger") # Não passa session_id explicitamente
    logger_ctx_test.info("Esta mensagem DEVE ir para o CSV da sessão pega do ContextVar e para o console.")
    logger_ctx_test.error("Este erro TAMBÉM DEVE ir para o CSV da sessão pega do ContextVar e para o console.")

    # Limpa o ContextVar
    current_session_id_var.reset(token)

    # Fecha o handler CSV para este logger de teste específico
    for handler in logger_ctx_test.handlers:
        if isinstance(handler, CsvSessionHandler) and handler.session_id == TEST_SESSION_ID_CTX:
            handler.close()
            print(f"Handler CSV para {TEST_SESSION_ID_CTX} fechado.")
            break

    # Teste com session_id explícito (como nos testes anteriores)
    logger_explicit_session = get_logger("ExplicitSessionLogger", session_id="explicit_test_session_123")
    logger_explicit_session.info("Mensagem para sessão explícita (console e CSV explícito).")
    for handler in logger_explicit_session.handlers:
        if isinstance(handler, CsvSessionHandler) and handler.session_id == "explicit_test_session_123":
            handler.close()
            print(f"Handler CSV para explicit_test_session_123 fechado.")
            break

    print("\nTestes de logging concluídos. Verifique a saída do console e os arquivos CSV em agents/logs_sessions/")
    print(f"Loggers configurados no cache: {list(_configured_loggers.keys())}")

# ============================================================================
# Exports
# ============================================================================

__all__ = ['get_logger']
