from django.db import models
from django.conf import settings
from accounts.models import User  # Import directly

class EmployeeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_soft_deleted=False)
    
    def all_with_deleted(self):
        return super().get_queryset()
    
    def deleted_only(self):
        return super().get_queryset().filter(is_soft_deleted=True)

class Employee(User):  # Inherit from User class, not settings.AUTH_USER_MODEL
    class Meta:
        proxy = True
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
    
    objects = EmployeeManager()
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            last_employee = User.objects.all_with_deleted().order_by('-id').first()
            last_id = last_employee.id if last_employee else 0
            self.employee_id = f"EMP{(last_id + 1):06d}"
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return self.get_full_name()
    
    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"