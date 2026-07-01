from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index'),
    path('servers/', views.servers_list, name='servers_list'),
    path('servers/add/', views.server_add, name='server_add'),
    path('servers/import/', views.servers_import, name='servers_import'),
    path('check-connection/', views.check_connection_ajax, name='check_connection_ajax'),
    path('update-server-status/', views.update_server_status, name='update_server_status'),
    path('export-server-report-csv/<int:server_id>/', views.export_server_report_csv, name='export_server_report_csv'),
    path('mass-scan-thread/', views.mass_scan_thread, name='mass_scan_thread'),
    path('task-status/<str:task_id>/', views.task_status, name='task_status'),
    path('export-all-reports-zip/', views.export_all_reports_zip, name='export_all_reports_zip'),
]