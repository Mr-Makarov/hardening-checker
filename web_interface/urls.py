from django.urls import path
from . import views



urlpatterns = [
    path('', views.index, name='index'),
    path('servers/', views.servers_list, name='servers_list'),
    path('servers/add/', views.server_add, name='server_add'),
    path('servers/import/', views.servers_import, name='servers_import'),
    path('check-connection/', views.check_connection_ajax, name='check_connection_ajax'),
    path('update-server-status/', views.update_server_status, name='update_server_status'),
    path('mass-scan-sync/', views.mass_scan_sync, name='mass_scan_sync'),
    path('export-server-report-csv/<int:server_id>/', views.export_server_report_csv, name='export_server_report_csv'),
]
