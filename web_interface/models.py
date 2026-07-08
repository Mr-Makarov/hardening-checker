from django.db import models
from django.contrib.auth.models import User


class Servers(models.Model):
    """Модель хранит данные о сканируемых серверах"""
    name = models.CharField(max_length=255, verbose_name="Имя", null=True, blank=True)
    host = models.CharField(max_length=255, verbose_name="IP-адрес", null=True, blank=True)
    port = models.IntegerField(default=22, verbose_name="Порт")
    username = models.CharField(max_length=25, verbose_name="Пользователь", null=True, blank=True)
    password = models.CharField(max_length=255, verbose_name="Пароль", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    # Связь с пользователем, кто добавил
    created_by = models.ForeignKey(User,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True,
                                    verbose_name="Кто добавил"
                                )
    # Результаты сканирования
    last_scan_date = models.DateTimeField(null=True, blank=True)
    last_scan_status = models.CharField(max_length=20, null=True, blank=True)
    last_scan_summary = models.JSONField(default=dict, blank=True)
    last_scan_details = models.JSONField(default=list, blank=True)


    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"

    class Meta:
        verbose_name = "Сервер"
        verbose_name_plural = "Серверы"



class ServerStatus(models.Model):
    """Модель для хранения статусов серверов"""
    server = models.OneToOneField(Servers, on_delete=models.CASCADE)
    last_check = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, default='unknown')
    message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.server.name}: {self.status}"



class ScanProfiles(models.Model):
    """"Модель для хранения профилей сканирования"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_base_profile = models.BooleanField(default=False)
    created_by = models.ForeignKey(User,
                                   on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True,
                                    verbose_name="Создатель")
    created_at = models.DateTimeField(auto_now_add=True)
    checks = models.ManyToManyField('Checks',
                                    blank=True,
                                    verbose_name="Проверки")

    def __str__(self):
        return self.name



class Checks(models.Model):
    """Модель для хранения проверок безопасности"""

    # Выбор категорий
    CATEGORY_CHOICES = [
        ('kernel', 'Ядро'),
        ('ssh', 'SSH'),
        ('files', 'Файлы'),
        ('grub', 'GRUB'),
        ('pam', 'PAM/Пароли'),
        ('services', 'Сервисы'),
        ('pentest', 'PenTest'),
    ]

    # Выбор важности
    IMPORTANCE_CHOICES = [
        ('critical', 'Критический'),
        ('high', 'Высокий'),
        ('medium', 'Средний'),
        ('low', 'Низкий'),
    ]

    code = models.CharField(max_length=10, unique=True, verbose_name="Код")
    category = models.CharField(max_length=10, verbose_name="Категория", choices=CATEGORY_CHOICES)
    # Категории: 'kernel', 'ssh', 'files', 'grub', 'pam', 'services'
    parameter_check = models.CharField(max_length=255, verbose_name="Проверяемый параметр")
    command = models.CharField(max_length=255, verbose_name="Команда")
    expected = models.CharField(max_length=255, verbose_name="Установленное значение",blank=True, null=True)
    description = models.TextField(verbose_name="Описание")
    importance = models.CharField(max_length=10, verbose_name="Важность", choices=IMPORTANCE_CHOICES)
    # 'critical', 'high', 'medium', 'low'

    def __str__(self):
        return f"{self.code} {self.category} {self.parameter_check} - {self.description[:50]}"



class ScanTask(models.Model):
    """Модель для хранения прогресса сканирования"""
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('running', 'Выполняется'),
        ('completed', 'Завершено'),
        ('failed', 'Ошибка'),
    ]
    task_id = models.CharField(max_length=36, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(ScanProfiles, on_delete=models.CASCADE)
    servers = models.ManyToManyField(Servers)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_servers = models.PositiveIntegerField(default=0)
    processed_servers = models.PositiveIntegerField(default=0)
    passed_total = models.PositiveIntegerField(default=0)
    failed_total = models.PositiveIntegerField(default=0)
    error_total = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Task #{self.id} - {self.status}"


