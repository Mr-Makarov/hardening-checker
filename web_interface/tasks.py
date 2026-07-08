from django.utils import timezone
from django.db import transaction
from .models import ScanTask, Servers, ScanProfiles
from .services import run_scan


def run_scan_task(task_id, user_id, server_ids, profile_id):
    """
    Функция для выполнения сканирования в фоновом потоке
    """

    try:
        # Получаем задачу из БД
        task = ScanTask.objects.get(task_id=task_id)
        profile = ScanProfiles.objects.get(id=profile_id)
        servers = Servers.objects.filter(id__in=server_ids, created_by_id=user_id)

        # Обновляем статус
        task.status = 'running'
        task.save()

        total = servers.count()
        processed = 0
        passed_total = 0
        failed_total = 0
        error_total = 0

        for server in servers:
            try:
                scan_result = run_scan(server.host, server.port, server.username, server.password, profile)
                stats = scan_result.get('stats', {"PASS": 0, "FAIL": 0, "ERROR": 0})

                passed_total += stats.get('PASS', 0)
                failed_total += stats.get('FAIL', 0)
                error_total += stats.get('ERROR', 0)

                # Сохраняем результат в DB
                server.last_scan_date = timezone.now()
                if stats.get('FAIL', 0) > 0:
                    server.last_scan_status = 'failed'
                elif stats.get('ERROR', 0) > 0:
                    server.last_scan_status = 'error'
                else:
                    server.last_scan_status = 'success'
                server.last_scan_summary = stats
                server.last_scan_details = scan_result.get('data', [])
                server.save(update_fields=[
                    'last_scan_date',
                    'last_scan_status',
                    'last_scan_summary',
                    'last_scan_details'
                ])

            except Exception as e:
                error_total += 1
                # Сохраняем ошибку в DB
                server.last_scan_date = timezone.now()
                server.last_scan_status = 'error'
                server.last_scan_summary = {'PASS': 0, 'FAIL': 0, 'ERROR': 1}
                server.last_scan_details = []
                server.save(update_fields=[
                    'last_scan_date',
                    'last_scan_status',
                    'last_scan_summary',
                    'last_scan_details'
                ])

            processed += 1

            # Обновляем прогресс задачи в БД
            task.processed_servers = processed
            task.passed_total = passed_total
            task.failed_total = failed_total
            task.error_total = error_total
            task.save()

        # Завершаем задачу
        task.status = 'completed'
        task.save()

    except Exception as e:
        # Если произошла ошибка, помечаем задачу как failed
        try:
            task = ScanTask.objects.get(task_id=task_id)
            task.status = 'failed'
            task.error_message = str(e)
            task.save()
        except ScanTask.DoesNotExist:
            pass