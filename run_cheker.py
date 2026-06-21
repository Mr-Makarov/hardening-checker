""""
Модуль для запуска сканирования
"""
from core.ssh_client import SSHConnection
from core.checker import get_checks_from_db


def run_scaner(host: str, port: int, user: str, passwd: str, checks):
    """Функция запуска сканирования"""

    results = []

    # Подключаемся к серверу
    conn = SSHConnection()
    conn.connect(host, port, user, passwd)

    # Проверяем
    for check in checks:
        output, error, exit_code = conn.execute(check.command)

        # Получаем статус
        if exit_code != 0:
            status = 'ERROR'
        elif check.expected == output.strip():
            status = 'PASS'
        else:
            status = 'FAIL'
        # Записываем результат
        results.append({
            'code': check.code,
            'description': check.description,
            'verifiable_value': check.parameter_check,
            'status': status,
            'expected': check.expected,
            'current': output.strip()
        })
    return results




