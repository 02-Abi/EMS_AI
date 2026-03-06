from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('employee_id', 'username', 'email', 'first_name', 'last_name', 
                   'role', 'department', 'employment_status', 'is_soft_deleted')
    list_filter = ('role', 'department', 'employment_status', 'is_soft_deleted')
    search_fields = ('employee_id', 'username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'department', 'designation', 'phone', 
                      'salary', 'role', 'employment_status', 'date_of_joining', 
                      'is_soft_deleted'),
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Information', {
            'fields': ('employee_id', 'department', 'designation', 'phone', 
                      'salary', 'role', 'employment_status', 'date_of_joining'),
        }),
    )