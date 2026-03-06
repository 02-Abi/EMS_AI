from django.utils.deprecation import MiddlewareMixin
from .services import AuditService
import threading

local = threading.local()

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        local.ip_address = AuditService.get_client_ip(request)
    
    def process_response(self, request, response):
        if hasattr(local, 'ip_address'):
            del local.ip_address
        return response

def get_current_ip():
    return getattr(local, 'ip_address', None)