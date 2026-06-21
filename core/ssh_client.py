"""
SSH клиент для подключения к удаленным серверам
"""

import paramiko


class SSHConnection:
    """Класс для ssh подключения"""

    def __init__(self):
        """Инициализация клиента"""
        self.client = None
        self.connected = False


    def connect(self, host: str, port: int, login: str, passwd: str):
        """Метод для установки соединения"""
        try:
            self.client = paramiko.SSHClient()

            # Настройка политики для неизвестных хостов
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # Подключение к серверу
            self.client.connect(host, port, login, passwd)
            self.connected = True

        except paramiko.AuthenticationException:
            print("Ошибка аутентификации")
        except paramiko.SSHException as e:
            print(f"SSH ошибка: {e}")
        except Exception as e:
            print(f"Общая ошибка: {e}")


    def execute(self, command: str):
        """Метод для выполнения команд на удаленном сервере"""
        # Проверяем есть ли подключение
        if not self.connected:
            raise Exception("Нет активного подключения.")

        stdin, stdout, stderr = self.client.exec_command(command)
        # Получение результата
        output = stdout.read().decode('utf-8')
        errors = stderr.read().decode('utf-8')
        exit_code = stdout.channel.recv_exit_status()

        # Если есть ошибка в stderr и нет вывода - считаем ошибкой
        if errors and not output:
            exit_code = 1

        return output, errors, exit_code

    def get_transport(self):
        """Получаем статус соединения"""
        return self.client.get_transport()


    def close(self):
        """Метод закрывает соединения"""
        self.client.close()
        self.connected = False

