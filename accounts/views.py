from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileUpdateForm
from .models import User
from audit.services import AuditService


# ==================== REGISTER VIEW ====================

def register_view(request):
    """
    Register a new user (default role = EMPLOYEE)
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'EMPLOYEE'  # Default role for security
            user.save()
            
            # Auto-generate employee_id
            user.employee_id = f"EMP{user.id:06d}"
            user.save()
            
            # Log registration
            AuditService.log_action(
                user=user,
                action_type='LOGIN',
                target_model='User',
                target_id=user.id,
                ip_address=AuditService.get_client_ip(request)
            )
            
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to EMS.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

# accounts/views.py - Update login_view

def login_view(request):
    """
    Handle user login - Like real websites
    """
    # 🔥 Clear any existing session first
    if request.user.is_authenticated:
        logout(request)
        request.session.flush()
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Check if user is active
                if user.is_soft_deleted or user.employment_status != 'ACTIVE':
                    messages.error(request, 'Account inactive. Contact HR.')
                    return redirect('accounts:login')
                
                # Login
                login(request, user)
                
                # 🔥 Set session to expire on browser close
                request.session.set_expiry(0)
                
                messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


# accounts/views.py - Replace logout_view

from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

@never_cache
@csrf_protect
def logout_view(request):
    """
    Complete logout - Works like real websites
    """
    if request.method == 'POST':
        # Log the logout action
        if request.user.is_authenticated:
            AuditService.log_action(
                user=request.user,
                action_type='LOGOUT',
                target_model='User',
                target_id=request.user.id,
                ip_address=AuditService.get_client_ip(request)
            )
        
        # 🔥 CRITICAL: Clear everything
        request.session.flush()  # Delete all session data
        logout(request)           # Django logout
        
        messages.success(request, 'You have been logged out successfully.')
        return redirect('accounts:login')
    else:
        # GET requests to logout are ignored (like real sites)
        return redirect('dashboard')


# ==================== PROFILE VIEW ====================

@login_required
def profile_view(request):
    """
    View and edit user profile
    """
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})