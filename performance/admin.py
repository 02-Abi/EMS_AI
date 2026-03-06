from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Performance

@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'rating', 'calculated_score', 'created_at')
    list_filter = ('year', 'month', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__employee_id')
    date_hierarchy = 'created_at'