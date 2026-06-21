from django.contrib import admin
from .models import Checks, ScanProfiles, Servers

# Register your models here.

admin.site.register(Checks)

class ScanProfilesAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_base_profile', 'created_at']
    list_filter = ['is_base_profile']
    search_fields = ['name']
    filter_horizontal = ['checks']

admin.site.register(ScanProfiles, ScanProfilesAdmin)


admin.site.register(Servers)
class ServersAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'username', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'host', 'username')