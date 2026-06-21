from django.utils import timezone
from run_cheker import run_scaner


def run_scan(host, port, username, password, checks):
    """
    Запуск сканирования
    """
    scan_results = run_scaner(host, port, username, password, checks)

    # Подсчитываем статистику
    stats = {'PASS': 0, 'FAIL': 0, 'ERROR': 0}
    for item in scan_results:
        stats[item['status']] += 1

    # Возвращаем данные для отображения
    return {
        'type': 'scan',
        'data': scan_results,
        'stats': stats
    }


def scan_and_save(server, profile):
    """Функция для сканирования и сохранения результата в Servers"""
    checks = profile.checks.all()
    scan_data = run_scan(server.host, server.port, server.username, server.password, checks)
    # scan_data = {'type': 'scan', 'data': [...], 'stats': {...}}
    stats = scan_data.get('stats', {})
    server.last_scan_date = timezone.now()
    if scan_data.get('type') == 'scan':
        # определяем статус: если есть FAIL -> failed, если есть ERROR -> error, иначе success
        if stats.get('FAIL', 0) > 0:
            server.last_scan_status = 'failed'
        elif stats.get('ERROR', 0) > 0:
            server.last_scan_status = 'error'
        else:
            server.last_scan_status = 'success'
        server.last_scan_summary = stats
        server.last_scan_details = scan_data.get('data', [])
    else:
        server.last_scan_status = 'error'
        server.last_scan_summary = {'PASS':0, 'FAIL':0, 'ERROR':1}
        server.last_scan_details = []
    server.save(update_fields=['last_scan_date', 'last_scan_status', 'last_scan_summary', 'last_scan_details'])
    return scan_data
