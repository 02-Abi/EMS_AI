from .models import AuditLog
from django.contrib.auth import get_user_model

User = get_user_model()

class AuditService:
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def log_action(user, action_type, target_model, target_id, ip_address=None, details=''):
        if isinstance(user, User):
            user_id = user
        else:
            user_id = User.objects.get(pk=user) if user else None
        
        return AuditLog.objects.create(
            user=user_id,
            action_type=action_type,
            target_model=target_model,
            target_id=target_id,
            ip_address=ip_address,
            details=details
        )
    
    @staticmethod
    def get_user_logs(user, limit=100):
        return AuditLog.objects.filter(user=user)[:limit]
    
    @staticmethod
    def get_model_logs(model_name, object_id=None, limit=100):
        logs = AuditLog.objects.filter(target_model=model_name)
        if object_id:
            logs = logs.filter(target_id=object_id)
        return logs[:limit]