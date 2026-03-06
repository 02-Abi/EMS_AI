from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import AuditLog
from .services import AuditService
from .middleware import get_current_ip
from accounts.models import User
from performance.models import Performance

User = get_user_model()

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditService.log_action(
        user=user,
        action_type='LOGIN',
        target_model='User',
        target_id=user.id,
        ip_address=AuditService.get_client_ip(request)
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        AuditService.log_action(
            user=user,
            action_type='LOGOUT',
            target_model='User',
            target_id=user.id,
            ip_address=AuditService.get_client_ip(request)
        )

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    if created and not kwargs.get('raw', False):
        AuditService.log_action(
            user=instance,
            action_type='CREATE',
            target_model='User',
            target_id=instance.id,
            ip_address=get_current_ip()
        )

@receiver(post_save, sender=Performance)
def log_performance_creation(sender, instance, created, **kwargs):
    if created and not kwargs.get('raw', False):
        AuditService.log_action(
            user=instance.employee,
            action_type='CREATE',
            target_model='Performance',
            target_id=instance.id,
            ip_address=get_current_ip()
        )