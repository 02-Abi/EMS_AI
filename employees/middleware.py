# employees/middleware.py

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin


class ForceLoginMiddleware(MiddlewareMixin):
    """
    Middleware to ensure users are redirected to login page
    when session expires or browser is closed
    """
    
    def process_request(self, request):
        # List of URLs that don't require authentication
        public_urls = [
            reverse('accounts:login'),
            reverse('accounts:register'),
            '/admin/',
        ]
        
        # Get current path
        path = request.path_info
        
        # Check if it's a static file - allow access
        if path.startswith('/static/'):
            return None
        
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check if session should be valid
            if not request.session.exists(request.session.session_key):
                logout(request)
                return redirect('accounts:login')
            
            # Optional: Check if user is soft deleted
            if hasattr(request.user, 'is_soft_deleted') and request.user.is_soft_deleted:
                logout(request)
                return redirect('accounts:login')
            
            # Optional: Check if user is inactive
            if hasattr(request.user, 'employment_status') and request.user.employment_status != 'ACTIVE':
                logout(request)
                return redirect('accounts:login')
            
        else:
            # If not authenticated and not on public URL, redirect to login
            if not any(path.startswith(url) for url in public_urls):
                return redirect('accounts:login')
        
        return None


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to check session expiry and force logout
    """
    
    def process_request(self, request):
        # Skip for public URLs
        public_urls = [
            reverse('accounts:login'),
            reverse('accounts:register'),
            '/admin/',
            '/static/',
        ]
        
        path = request.path_info
        if any(path.startswith(url) for url in public_urls):
            return None
        
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check session expiry
            if not request.session.get('_auth_user_id'):
                logout(request)
                return redirect('accounts:login')
            
            # Check if session has expired
            try:
                if request.session.get_expiry_age() <= 0:
                    logout(request)
                    return redirect('accounts:login')
            except:
                pass
# employees/middleware.py - Create this file

class NoCacheMiddleware:
    """
    Prevent back button after logout - Like real websites
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add headers that real websites use
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response