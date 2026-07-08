""""
Модуль для запуска сканирования
"""
import subprocess
from core.ssh_client import SSHConnection



def run_scaner(host: str, port: int, user: str, passwd: str, profile):
    """Функция запуска сканирования"""

    results = []
    conn = SSHConnection()

    # Получаем проверки из профиля
    checks = profile.checks.all()
    # Проверяем, есть ли SSH-проверки
    has_ssh_checks = any(check.category != 'pentest' for check in checks)
    if has_ssh_checks:
        try:
            conn.connect(host, port, user, passwd)
        except Exception as e:
            print(f"SSH подключение не установлено: {e}")

    for check in checks:

        command = check.command
        category = check.category

        if category == 'pentest':
            # Локальное выполнение (nmap)
            cmd = command.format(host=host)
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=90)
                output = result.stdout.strip()
                error = result.stderr.strip()
                exit_code = result.returncode
            except subprocess.TimeoutExpired:
                output = ''
                error = 'Timeout'
                exit_code = 1
        else:
            # SSH выполнение
            try:
                output, error, exit_code = conn.execute(command)
                output = output.strip()
                error = error.strip()
            except Exception as e:
                output = ''
                error = str(e)
                exit_code = 1

        # Определяем статус
        if exit_code != 0:
            results.append({
                'code': check.code,
                'description': check.description,
                'verifiable_value': check.parameter_check,
                'status': 'ERROR',
                'expected': check.expected,
                'current': None,
                'message': error[:100] if error else f"Exit code {exit_code}"
            })
        elif check.expected == output:
            results.append({
                'code': check.code,
                'description': check.description,
                'verifiable_value': check.parameter_check,
                'status': 'PASS',
                'expected': check.expected,
                'current': output,
                'message': None
            })
        else:
            results.append({
                'code': check.code,
                'description': check.description,
                'verifiable_value': check.parameter_check,
                'status': 'FAIL',
                'expected': check.expected,
                'current': output if output else '(пусто)',
                'message': None
            })

    if conn.connected:
        conn.close()

    return results



