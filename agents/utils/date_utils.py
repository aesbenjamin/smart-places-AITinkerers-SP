"""
Utilitários de Data
------------------
Este módulo implementa funções utilitárias para manipulação e padronização
de datas no sistema, com foco especial no formato brasileiro de datas.

O módulo fornece funções para converter diferentes formatos de data para
um formato padronizado (YYYY-MM-DD), lidando com formatos comuns em
português como "20 de Janeiro de 2023".
"""

# ============================================================================
# Imports
# ============================================================================

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

# Adiciona o diretório raiz do projeto ao sys.path para imports absolutos
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports absolutos
from agents.utils.logger import get_logger

# ============================================================================
# Configuração do Logger
# ============================================================================

logger = get_logger(__name__)

# ============================================================================
# Funções Principais
# ============================================================================

def parse_date(date_str: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Tenta converter uma string de data em um objeto datetime.
    Suporta vários formatos de data em português.

    Args:
        date_str (str): String contendo a data a ser convertida

    Returns:
        Optional[Tuple[datetime, datetime]]: Tupla com data inicial e final se for um intervalo,
                                           ou tupla com a mesma data duas vezes se for uma data única,
                                           ou None se não for possível converter
    """
    if not date_str or date_str.lower() == 'n/a':
        return None

    # Lista de formatos de data suportados
    formats_to_try = [
        "%d de %B de %Y",  # ex: 20 de Janeiro de 2023
        "%d/%m/%Y",        # ex: 20/01/2023
        "%Y-%m-%d",        # ex: 2023-01-20
        "%d de %b de %Y",  # ex: 20 de Jan de 2023
    ]

    # Verifica se é um intervalo de datas
    if ' a ' in date_str.lower() or ' até ' in date_str.lower():
        try:
            # Tenta separar o intervalo
            if ' a ' in date_str.lower():
                start_str, end_str = date_str.lower().split(' a ', 1)
            else:
                start_str, end_str = date_str.lower().split(' até ', 1)

            # Tenta converter cada parte do intervalo
            start_date = None
            end_date = None

            for fmt in formats_to_try:
                try:
                    start_date = datetime.strptime(start_str.strip(), fmt)
                    break
                except ValueError:
                    continue

            for fmt in formats_to_try:
                try:
                    end_date = datetime.strptime(end_str.strip(), fmt)
                    break
                except ValueError:
                    continue

            if start_date and end_date:
                return (start_date, end_date)
            else:
                logger.warning(f"Não foi possível converter o intervalo de datas: {date_str}")
                return None

        except Exception as e:
            logger.error(f"Erro ao processar intervalo de datas '{date_str}': {e}")
            return None

    # Se não for um intervalo, tenta converter como uma data única
    for fmt in formats_to_try:
        try:
            date = datetime.strptime(date_str, fmt)
            return (date, date)
        except ValueError:
            continue

    logger.warning(f"Não foi possível converter a data: {date_str}")
    return None

def standardize_date_format(date_str: str) -> Optional[str]:
    """
    Tenta padronizar uma string de data para o formato YYYY-MM-DD.

    Esta função tenta converter diferentes formatos de data para um formato
    padronizado (YYYY-MM-DD). Ela suporta vários formatos comuns em português,
    incluindo datas por extenso e formatos numéricos.

    Args:
        date_str (str): String contendo a data a ser padronizada

    Returns:
        Optional[str]: Data no formato YYYY-MM-DD se bem-sucedido,
                      None se a string for vazia, nula ou representar um intervalo,
                      ou a string original se nenhum formato conhecido for compatível

    Note:
        O locale pt_BR.UTF-8 deve ser configurado globalmente no início da aplicação
        (ex: em env_setup.py) para que o parse de nomes de meses como 'Janeiro',
        'Fevereiro' funcione corretamente.
    """
    if not date_str or date_str.lower() == 'n/a':
        return None
    
    # Verifica se é um intervalo de datas
    if ' a ' in date_str.lower() or ' até ' in date_str.lower():
        logger.debug(f"Intervalo de datas detectado '{date_str}', não padronizando para data única.")
        return None  # Retorna None para intervalos explicitamente

    # Lista de formatos de data suportados
    formats_to_try = [
        "%d de %B de %Y",  # ex: 20 de Janeiro de 2023
        "%d/%m/%Y",        # ex: 20/01/2023
        "%Y-%m-%d",        # ex: 2023-01-20
        "%d de %b de %Y",  # ex: 20 de Jan de 2023 (requer locale)
    ]
    
    # Tenta cada formato até encontrar um que funcione
    parsed_date = None
    for fmt in formats_to_try:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    if not parsed_date:
        # Se chegou aqui, nenhum formato foi reconhecido
        logger.debug(f"Formato de data não reconhecido para padronização estrita: '{date_str}'. Mantendo original para possível tratamento posterior.")
        return date_str  # Mantém a string original se não puder padronizar
    
    # Este caso não deve ser alcançado devido à lógica acima, mas por segurança:
    return None

# ============================================================================
# Execução Local
# ============================================================================

if __name__ == '__main__':
    print("\n=== Testes de Utilitários de Data ===\n")
    
    # Configuração básica de logging para testes
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Lista de casos de teste
    test_cases = [
        {
            "nome": "Teste de data por extenso",
            "descricao": "Testa o formato de data por extenso em português",
            "data": "20 de Janeiro de 2023",
            "esperado": "2023-01-20"
        },
        {
            "nome": "Teste de data numérica",
            "descricao": "Testa o formato de data numérica (DD/MM/YYYY)",
            "data": "20/01/2023",
            "esperado": "2023-01-20"
        },
        {
            "nome": "Teste de data ISO",
            "descricao": "Testa o formato de data ISO (YYYY-MM-DD)",
            "data": "2023-01-20",
            "esperado": "2023-01-20"
        },
        {
            "nome": "Teste de intervalo de datas",
            "descricao": "Testa o tratamento de intervalo de datas",
            "data": "20 de Janeiro a 25 de Janeiro de 2023",
            "esperado": None
        },
        {
            "nome": "Teste de data inválida",
            "descricao": "Testa o tratamento de data inválida",
            "data": "data inválida",
            "esperado": "data inválida"
        }
    ]
    
    # Executa os testes
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Teste {i}: {test_case['nome']} ---")
        print(f"Descrição: {test_case['descricao']}")
        print(f"Data de entrada: {test_case['data']}")
        
        try:
            resultado = standardize_date_format(test_case['data'])
            print(f"Resultado: {resultado}")
            
            if resultado == test_case['esperado']:
                print("Status: ✓ Teste passou")
            else:
                print(f"Status: ✗ Teste falhou (esperado: {test_case['esperado']})")
                
        except Exception as e:
            print(f"Erro durante o teste: {str(e)}")
        
        print("\n" + "="*50)

# ============================================================================
# Exports
# ============================================================================

__all__ = ['standardize_date_format', 'parse_date'] 