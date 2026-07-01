import csv
from io import StringIO
from core.ssh_client import SSHConnection


def test_connection(host, port, username, password):
    """
    Проверка SSH подключения
    """
    conn = SSHConnection()
    try:
        conn.connect(host, port, username, password)
        if conn.connected:
            # Проверяем, можем ли выполнить команду
            output, error, code = conn.execute('echo OK')
            if code == 0 and 'OK' in output:
                return {'type': 'check', 'data': f"✅ Успешное подключение к {username}@{host}:{port}"}
            else:
                return {'type': 'check', 'data': f"⚠️ Подключено, но команда не выполняется: {error}"}
        else:
            return {'type': 'check', 'data': f"❌ Не удалось подключиться"}
    except Exception as e:
        return {'type': 'check', 'data': f"❌ Ошибка: {str(e)}"}
    finally:
        conn.close()


def generate_server_csv_content(server):
    """
    Генерирует CSV-содержимое для одного сервера
    Возвращает строку с CSV
    """
    output = StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Код', 'Описание', 'Проверяемый параметр', 'Статус', 'Ожидалось', 'Получено'])

    if not server.last_scan_details:
        return "Нет данных сканирования для этого сервера."

    for item in server.last_scan_details:
        if item.get('status') == 'ERROR':
            current_value = item.get('message', 'Ошибка')
        else:
            current_value = item.get('current', '')
        writer.writerow([
            item.get('code', ''),
            item.get('description', ''),
            item.get('verifiable_value', ''),
            item.get('status', ''),
            item.get('expected', ''),
            current_value,
        ])

    return output.getvalue()
