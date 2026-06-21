"""
Чекер, осуществляет проверку безопасности
"""
from web_interface.models import Checks



class Check:
    """Класс проверки одного параметра безопасности"""
    def __init__(self, code: str, command: str, expected: str, parameter_check: str, description=""):
        """Инициализация класса проверки
        """
        self.code = code
        self.command = command
        self.expected = expected
        self.parameter_check = parameter_check
        self.description = description


def get_checks_from_db():
        """Получаем данные из БД"""

        queryset = Checks.objects.all()

        checks = []
        for db_check in queryset:
            check = Check(
                code=db_check.code,
                command=db_check.command,
                expected=db_check.expected,
                parameter_check=db_check.parameter_check,
                description=db_check.description
            )
            checks.append(check)

        return checks


