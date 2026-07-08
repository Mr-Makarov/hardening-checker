from django.utils import timezone
from run_cheker import run_scaner


def run_scan(host, port, username, password, profile):
    """Запускаем сканирование"""
    scan_results = run_scaner(host, port, username, password, profile)

    stats = {'PASS': 0, 'FAIL': 0, 'ERROR': 0}
    for item in scan_results:
        stats[item['status']] += 1

    return {
        'type': 'scan',
        'data': scan_results,
        'stats': stats
    }


def scan_and_save(server, profile):
    """Сохраняем результат"""

    scan_data = run_scan(server.host, server.port, server.username, server.password, profile)
    stats = scan_data.get('stats', {})
    server.last_scan_date = timezone.now()
    if scan_data.get('type') == 'scan':
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
        server.last_scan_summary = {'PASS': 0, 'FAIL': 0, 'ERROR': 1}
        server.last_scan_details = []
    server.save(update_fields=['last_scan_date', 'last_scan_status', 'last_scan_summary', 'last_scan_details'])
    return scan_data