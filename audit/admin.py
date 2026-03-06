from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action_type', 'target_model', 'target_id')
    list_filter = ('action_type', 'target_model', 'timestamp')
    search_fields = ('user__username', 'details')
    readonly_fields = ('timestamp', 'ip_address')
    date_hierarchy = 'timestamp'