import csv, json, zipfile
import io
import uuid
import threading
from io import BytesIO
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .forms import ConnectServerForm, ServerAddForm
from .models import ScanProfiles, Servers, ServerStatus, ScanTask
from .services import run_scan, scan_and_save
from applications import test_connection, generate_server_csv_content
from .tasks import run_scan_task


# Create your views here.
@login_required
def index(request):
    results_data = None
    form = ConnectServerForm()

    profiles = ScanProfiles.objects.all()
    form.fields['check'].choices = [(r.id, r.name) for r in profiles]

    # Заполнение формы если передан GET
    selected_server = None
    server_id = request.GET.get('server_id')
    if server_id:
        try:
            selected_server = Servers.objects.get(id=server_id, created_by=request.user)
            initial = {
                'host': selected_server.host,
                'port': selected_server.port,
                'username': selected_server.username,
                'password': selected_server.password,
            }
            form = ConnectServerForm(initial=initial)
            form.fields['check'].choices = [(p.id, p.name) for p in profiles]
            # Если есть сохранённые результаты, показываем их
            if selected_server.last_scan_details:
                results_data = {
                    'type': 'scan',
                    'data': selected_server.last_scan_details,
                    'stats': selected_server.last_scan_summary,
                    'server_name': selected_server.name,
                }
        except Servers.DoesNotExist:
            pass

    if request.method == 'POST':

        form = ConnectServerForm(request.POST)

        profiles = ScanProfiles.objects.all()
        form.fields['check'].choices = [(r.id, r.name) for r in profiles]

        if form.is_valid():
            host = form.cleaned_data['host']
            port = form.cleaned_data['port']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            check_id = form.cleaned_data['check']
            profile = ScanProfiles.objects.get(id=check_id)
            checks = profile.checks.all()
            action = request.POST.get('action')

            if action == 'check':
                results_data = test_connection(host, port, username, password)
                print(results_data)
            elif action == 'scan':
                try:
                    server = Servers.objects.get(host=host, port=port, username=username, created_by=request.user)
                except Servers.DoesNotExist:
                    server = None
                scan_result = run_scan(host, port, username, password, checks)
                if server:
                    # Сохраняем результат в сервер
                    stats = scan_result.get('stats', {})
                    server.last_scan_date = timezone.now()
                    if stats.get('FAIL', 0) > 0:
                        server.last_scan_status = 'failed'
                    elif stats.get('ERROR', 0) > 0:
                        server.last_scan_status = 'error'
                    else:
                        server.last_scan_status = 'success'
                    server.last_scan_summary = stats
                    server.last_scan_details = scan_result.get('data', [])
                    server.save(
                        update_fields=['last_scan_date', 'last_scan_status', 'last_scan_summary', 'last_scan_details'])
                    results_data = {
                        'type': 'scan',
                        'data': scan_result.get('data'),
                        'stats': stats,
                        'server_name': server.name,
                    }
                else:
                    # Если сервер не найден в базе, просто показываем результат без сохранения
                    results_data = scan_result
            else:
                results_data  = f"❌ Неизвестное действие: {action}"
        else:
            results_data  = f"❌ Ошибка в форме: {form.errors}"

    return render(request, 'web_interface/index.html', {
        'form': form,
        'results': results_data,
        'selected_server': selected_server
    })


@login_required
def servers_list(request):
    servers = Servers.objects.filter(is_active=True)
    profiles = ScanProfiles.objects.filter(is_active=True)
    for server in servers:
        try:
            status_obj = ServerStatus.objects.get(server=server)
            if status_obj.status == 'ok':
                server.status_icon = '✅'
                server.status_text = 'Соединение установлено'
            else:
                server.status_icon = '❌'
                server.status_text = 'Не удалось подключиться'
            server.status_tooltip = status_obj.message
        except ServerStatus.DoesNotExist:
            server.status_icon = '❓'
            server.status_tooltip = 'Не проверялось'
    return render(request, 'web_interface/servers_list.html', {'servers': servers, 'profiles': profiles})


@login_required
def server_add(request):
    """Представление для добавления сервера"""

    if request.method == 'POST':
        form = ServerAddForm(request.POST)
        if form.is_valid():
            server = Servers(
                name=form.cleaned_data['name'],
                host=form.cleaned_data['host'],
                port=form.cleaned_data['port'],
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                is_active=form.cleaned_data['is_active'],
                created_by=request.user
            )
            server.save()
            return redirect('servers_list')
    else:
        form = ServerAddForm()

    return render(request, 'web_interface/server_form.html', {'form': form})


@login_required
def servers_import(request):
    """Представление для массового добавления серверов"""

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        # Проверяем расширение
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Файл должен быть в формате CSV')
            return redirect('servers_list')

        # Читаем файл
        decoded = csv_file.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        added = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                # Создаём сервер
                server = Servers(
                    name=row['name'],
                    host=row['host'],
                    port=int(row.get('port', 22)),
                    username=row['username'],
                    password=row['password'],
                    is_active=row.get('is_active', 'True').lower() == 'true',
                    created_by=request.user
                )
                server.save()
                added += 1
            except Exception as e:
                errors.append(f"Строка {row_num}: {str(e)}")

        # Сообщения пользователю
        if added:
            messages.success(request, f'Добавлено серверов: {added}')
        if errors:
            messages.error(request, f'Ошибки: {", ".join(errors[:5])}')

        return redirect('servers_list')

    return redirect('servers_list')


@login_required
def check_connection_ajax(request):
    """Представление проверки соединения для группы серверов"""

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            host = data.get('host')
            port = data.get('port')
            username = data.get('username')
            password = data.get('password')
            success, message = test_connection(host, port, username, password)
            return JsonResponse({'success': success, 'message': message})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=405)


@login_required
def update_server_status(request):
    """"Представление для обновления статусов серверов после проверки соединения"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            server_id = data.get('server_id')
            success = data.get('success')
            message = data.get('message', '')
            server = Servers.objects.get(id=server_id, created_by=request.user)
            status_obj, created = ServerStatus.objects.get_or_create(server=server)
            status_obj.status = 'ok' if success else 'error'
            status_obj.message = message
            status_obj.save()
            return JsonResponse({'success': True})
        except Servers.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Server not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=405)



@login_required
def mass_scan_thread(request):
    """Представление запуска массового сканиования"""

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        server_ids = data.get('server_ids', [])
        profile_id = data.get('profile_id')

        if not server_ids or not profile_id:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        profile = ScanProfiles.objects.get(id=profile_id)
        servers = Servers.objects.filter(id__in=server_ids, created_by=request.user)

        if not servers.exists():
            return JsonResponse({'error': 'No valid servers'}, status=400)

        # Генерируем уникальный ID задачи
        task_id = str(uuid.uuid4())

        # Создаём задачу в БД со статусом 'pending'
        task = ScanTask.objects.create(
            task_id=task_id,
            created_by=request.user,
            profile=profile,
            status='pending',
            total_servers=servers.count(),
            processed_servers=0,
            passed_total=0,
            failed_total=0,
            error_total=0
        )
        task.servers.set(servers)

        # Запускаем фоновый поток
        thread = threading.Thread(
            target=run_scan_task,
            args=(task_id, request.user.id, server_ids, profile_id)
        )
        thread.daemon = True  # поток завершится при остановке Django
        thread.start()

        return JsonResponse({'task_id': task_id})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def scan_server(request, server_id):
    server = get_object_or_404(Servers, id=server_id, created_by=request.user)
    # Получаем профиль (например, последний использованный или базовый)
    # Можно передавать profile_id через GET, но пока возьмём первый активный
    profile = ScanProfiles.objects.filter(is_base_profile=True).first()
    if not profile:
        profile = ScanProfiles.objects.first()
    # Сканируем
    scan_data = scan_and_save(server, profile)
    # Отображаем страницу с результатами
    return render(request, 'web_interface/server_scan_result.html', {
        'server': server,
        'results': scan_data.get('data', []),
        'stats': server.last_scan_summary,
    })

@login_required
def export_server_report_csv(request, server_id):
    """Представление для экспорта данных о сканирование в CSV"""
    server = get_object_or_404(Servers, id=server_id, created_by=request.user)
    csv_content = generate_server_csv_content(server)

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="server_{server.name}_scan_report.csv"'
    response.write(csv_content)
    return response


@login_required
def export_all_reports_zip(request):
    """Представление для скачивания архива с отчетами отсканированных серверов"""
    servers = Servers.objects.filter(created_by=request.user, is_active=True)
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for server in servers:
            csv_content = generate_server_csv_content(server)
            filename = f"server_{server.id}_{server.name}.csv"
            zip_file.writestr(filename, csv_content)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="all_reports.zip"'
    return response


@login_required
def task_status(request, task_id):
    try:
        task = ScanTask.objects.get(task_id=task_id, created_by=request.user)
        response = {
            'status': task.status,
            'processed': task.processed_servers,
            'total': task.total_servers,
            'passed_total': task.passed_total,
            'failed_total': task.failed_total,
            'error_total': task.error_total,
        }
        if task.error_message:
            response['error_message'] = task.error_message
        return JsonResponse(response)
    except ScanTask.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)



