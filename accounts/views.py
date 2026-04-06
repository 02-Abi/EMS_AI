from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    UserProfileUpdateForm,
    EmployeeSetPasswordForm
)
from .models import User
from audit.services import AuditService


# ==================== REGISTER VIEW ====================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'EMPLOYEE'
            user.save()
            user.employee_id = f"EMP{user.id:06d}"
            user.save()
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


# ==================== LOGIN VIEW ====================

def login_view(request):
    if request.user.is_authenticated:
        logout(request)
        request.session.flush()
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session.set_expiry(0)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


# ==================== LOGOUT VIEW ====================

@never_cache
@csrf_protect
def logout_view(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            AuditService.log_action(
                user=request.user,
                action_type='LOGOUT',
                target_model='User',
                target_id=request.user.id,
                ip_address=AuditService.get_client_ip(request)
            )
        request.session.flush()
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
        return redirect('accounts:login')
    else:
        return redirect('dashboard')


# ==================== PROFILE VIEW ====================

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


# ==================== SET PASSWORD VIEW ====================

def set_password_view(request):
    if request.method == 'POST':
        form = EmployeeSetPasswordForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Password set successfully for {user.username}. You can now log in.'
            )
            return redirect('accounts:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = EmployeeSetPasswordForm()
    return render(request, 'accounts/set_password.html', {'form': form})