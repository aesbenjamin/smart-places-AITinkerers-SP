import logging
import csv
import os
from datetime import datetime

LOGS_SESSIONS_DIR_NAME = "logs_sessions"
# O diretório base para os logs de sessão será agents/logs_sessions/
# __file__ em agents/utils/logger_session_csv.py refere-se a agents/utils/logger_session_csv.py
# O diretório pai de utils é agents/
AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOGS_SESSIONS_DIR = os.path.join(AGENTS_DIR, LOGS_SESSIONS_DIR_NAME)

class CsvSessionHandler(logging.Handler):
    """
    Um handler de logging que escreve logs de uma sessão específica para um arquivo CSV.
    O nome do arquivo é formatado como [data]_[session_id].csv e armazenado
    no diretório agents/logs_sessions/.
    """
    def __init__(self, session_id: str, logs_dir: str = DEFAULT_LOGS_SESSIONS_DIR):
        super().__init__()
        self.session_id = session_id
        self.logs_dir = logs_dir
        self.log_file_path = None
        self.file_handler = None
        self.csv_writer = None

        if not self.session_id:
            # Não fazer nada se não houver session_id, ou logar um aviso
            logging.getLogger(__name__).warning("CsvSessionHandler inicializado sem session_id. Nenhum log de sessão será gravado.")
            return

        try:
            if not os.path.exists(self.logs_dir):
                os.makedirs(self.logs_dir)
                logging.getLogger(__name__).info(f"Diretório de logs de sessão criado: {self.logs_dir}")
        except OSError as e:
            logging.getLogger(__name__).error(f"Erro ao criar diretório de logs de sessão {self.logs_dir}: {e}", exc_info=True)
            return # Impede a continuação se o diretório não puder ser criado

        current_date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{current_date_str}_{self.session_id}.csv"
        self.log_file_path = os.path.join(self.logs_dir, filename)

        self._open_file_and_writer()

    def _open_file_and_writer(self):
        """Abre o arquivo de log e inicializa o CSV writer."""
        if not self.log_file_path:
            return

        file_exists = os.path.exists(self.log_file_path)
        try:
            # Usar 'a' para append, newline='' para controle correto de novas linhas pelo csv.writer
            self.file_handler = open(self.log_file_path, 'a', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.file_handler, quoting=csv.QUOTE_ALL)

            if not file_exists:
                self.csv_writer.writerow(['timestamp', 'session_id', 'level', 'module', 'function', 'message', 'user_input', 'agent_response'])
                self.flush() # Garante que o header seja escrito imediatamente
        except OSError as e:
            logging.getLogger(__name__).error(f"Erro ao abrir/criar arquivo de log CSV {self.log_file_path}: {e}", exc_info=True)
            self.file_handler = None
            self.csv_writer = None


    def emit(self, record: logging.LogRecord):
        """
        Formata e escreve o registro de log no arquivo CSV.
        """
        if not self.csv_writer or not self.file_handler:
            # Não tentar logar se o arquivo ou writer não puderam ser inicializados
            # Ou se não há session_id
            return

        try:
            timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # Obter os campos personalizados do registro, se existirem
            user_input = getattr(record, 'user_input', '')
            agent_response = getattr(record, 'agent_response', '')
            
            log_entry = [
                timestamp,
                self.session_id,
                record.levelname,
                record.module,
                record.funcName,
                self.format(record), # Mensagem principal do log
                user_input,
                agent_response
            ]
            self.csv_writer.writerow(log_entry)
            self.flush() # Garante que cada log seja escrito imediatamente
        except Exception as e:
            # Usar o logger global para erros dentro do handler para evitar recursão
            logging.getLogger(__name__).error(f"Erro ao emitir log para CSV (sessão {self.session_id}): {e}", exc_info=True)


    def flush(self):
        """Garante que os dados sejam escritos no disco."""
        if self.file_handler and not self.file_handler.closed:
            try:
                self.file_handler.flush()
            except Exception as e:
                logging.getLogger(__name__).error(f"Erro ao fazer flush do arquivo CSV (sessão {self.session_id}): {e}", exc_info=True)

    def close(self):
        """Fecha o arquivo de log."""
        self.flush()
        if self.file_handler:
            try:
                self.file_handler.close()
            except Exception as e:
                logging.getLogger(__name__).error(f"Erro ao fechar arquivo CSV (sessão {self.session_id}): {e}", exc_info=True)
        super().close()

if __name__ == '__main__':
    # Exemplo de uso e teste do CsvSessionHandler
    
    # Configuração básica de logging para ver os logs do próprio handler e do teste
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    print(f"Testando CsvSessionHandler. Logs serão salvos em: {DEFAULT_LOGS_SESSIONS_DIR}")

    # Criar um logger de teste
    test_logger = logging.getLogger('my_test_app')
    test_logger.setLevel(logging.DEBUG) # Capturar todos os níveis para este logger

    # Simular um session_id
    example_session_id = "exemplo_session_12345"
    
    # Criar e adicionar o CsvSessionHandler
    csv_handler = CsvSessionHandler(session_id=example_session_id)
    
    # Um formatador simples para o CSV handler (opcional, o format() padrão pega record.message)
    # Para incluir mais detalhes formatados na coluna 'message' do CSV:
    csv_formatter = logging.Formatter('%(message)s (em %(module)s.%(funcName)s:%(lineno)d)')
    # csv_handler.setFormatter(csv_formatter) # Descomente para usar este formatador na coluna 'message'
                                          # Nota: A mensagem já é formatada pelo handler.format()
                                          # Esta linha só teria efeito se o formatador base não estivesse pegando a msg.
                                          # O handler.format(record) já pega a mensagem formatada pelo logger.
                                          # A coluna 'message' no CSV terá a mensagem completa já formatada
                                          # pelos formatadores do logger principal.

    if csv_handler.csv_writer: # Só adiciona se o handler foi inicializado corretamente
        test_logger.addHandler(csv_handler)
        print(f"CsvSessionHandler adicionado ao logger 'my_test_app' para session_id: {example_session_id}")
        print(f"Arquivo de log esperado: {csv_handler.log_file_path}")
    else:
        print(f"Falha ao inicializar CsvSessionHandler para session_id: {example_session_id}. Verifique os logs de erro.")
        # Não prosseguir com os logs de teste se o handler falhou

    # Logar algumas mensagens de teste
    test_logger.debug("Esta é uma mensagem de debug da sessão.")
    test_logger.info("Informação relevante da sessão.")
    test_logger.warning("Um aviso importante da sessão.")
    test_logger.error("Ocorreu um erro na sessão!")
    
    def alguma_funcao_de_teste():
        test_logger.info("Log de dentro de uma função.")

    alguma_funcao_de_teste()

    # É importante fechar o handler ao final, especialmente se o programa termina aqui.
    # Em um servidor de longa duração, o fechamento pode ser mais complexo (ex: no shutdown do servidor)
    if csv_handler.csv_writer:
        csv_handler.close()
        print(f"CsvSessionHandler fechado para session_id: {example_session_id}")

    print('\nTeste de handler sem session_id (esperado não criar arquivo):')
    no_session_handler = CsvSessionHandler(session_id=None) # type: ignore
    test_logger.addHandler(no_session_handler) # Não deve logar nada no CSV
    test_logger.info("Esta mensagem não deve ir para um CSV de sessão (handler sem session_id).")
    no_session_handler.close()


    print('\nTeste de handler com session_id vazio (esperado não criar arquivo):')
    empty_session_handler = CsvSessionHandler(session_id="")
    test_logger.addHandler(empty_session_handler) # Não deve logar nada no CSV
    test_logger.info("Esta mensagem não deve ir para um CSV de sessão (handler com session_id vazio).")
    empty_session_handler.close()
    
    # Remover handlers para não afetar outros testes ou execuções
    if csv_handler.csv_writer:
      test_logger.removeHandler(csv_handler)
    test_logger.removeHandler(no_session_handler)
    test_logger.removeHandler(empty_session_handler)

    print('\nFim dos testes de CsvSessionHandler.')
