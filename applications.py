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
                return True, f"✅ Успешное подключение к {username}@{host}:{port}"
            else:
                return False, f"⚠️ Подключено, но команда не выполняется: {error}"
        else:
            return False, f"❌ Не удалось подключиться"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"
    finally:
        conn.close()
