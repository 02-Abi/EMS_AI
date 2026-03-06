from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from accounts.models import User


def role_required(allowed_roles, redirect_url='dashboard'):
    """
    Decorator to check if user has required role.
    
    Args:
        allowed_roles (list): List of roles allowed to access the view
        redirect_url (str): URL to redirect if permission denied
    
    Returns:
        Decorated view function
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login to access this page.')
                return redirect('accounts:login')
            
            # Check if user has required role
            if request.user.role not in allowed_roles:
                messages.error(
                    request,
                    f'Access Denied: You need {_format_allowed_roles(allowed_roles)} permissions to view this page.'
                )
                return redirect(redirect_url)
            
            # User has permission - proceed
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def _format_allowed_roles(roles):
    """Helper function to format role list for error messages"""
    if len(roles) == 1:
        return roles[0]
    elif len(roles) == 2:
        return f"{roles[0]} or {roles[1]}"
    else:
        return ", ".join(roles[:-1]) + f" or {roles[-1]}"


# ==================== ROLE-BASED DECORATORS ====================

def hr_required(view_func):
    """Decorator for views that require HR or SUPERADMIN role"""
    return role_required(['HR', 'SUPERADMIN'])(view_func)


def manager_required(view_func):
    """Decorator for views that require MANAGER, HR, or SUPERADMIN role"""
    return role_required(['MANAGER', 'HR', 'SUPERADMIN'])(view_func)


def hr_or_manager_required(view_func):
    """Decorator for views that require HR, MANAGER, or SUPERADMIN role"""
    return role_required(['HR', 'MANAGER', 'SUPERADMIN'])(view_func)


def superadmin_required(view_func):
    """Decorator for views that require SUPERADMIN role only"""
    return role_required(['SUPERADMIN'])(view_func)


def employee_only(view_func):
    """Decorator for views that require EMPLOYEE role only"""
    return role_required(['EMPLOYEE'])(view_func)


# ==================== DEPARTMENT-SPECIFIC DECORATORS ====================

def manager_of_department(view_func):
    """
    Decorator to check if user is manager of the employee's department.
    Used for views that need department-level access control.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user has manager-level role
        if request.user.role not in ['MANAGER', 'HR', 'SUPERADMIN']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        # Get the employee being accessed (if pk in kwargs)
        employee_id = kwargs.get('pk')
        if employee_id and request.user.role == 'MANAGER':
            try:
                employee = User.objects.get(pk=employee_id)
                if employee.department != request.user.department:
                    messages.error(request, 'You can only access employees in your department.')
                    return redirect('employees:list')
            except User.DoesNotExist:
                messages.error(request, 'Employee not found.')
                return redirect('employees:list')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==================== PROTECTION DECORATORS ====================

def prevent_superadmin_delete(view_func):
    """
    Decorator to prevent accidental deletion of SUPERADMIN users.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method == 'POST':
            employee_id = kwargs.get('pk')
            if employee_id:
                try:
                    employee = User.objects.get(pk=employee_id)
                    if employee.is_superuser or employee.role == 'SUPERADMIN':
                        messages.error(
                            request,
                            '❌ SUPERADMIN accounts cannot be deleted for security reasons.'
                        )
                        return redirect('employees:list')
                except User.DoesNotExist:
                    pass
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def prevent_hr_edit_superadmin(view_func):
    """
    Decorator to prevent HR from editing SUPERADMIN accounts.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        employee_id = kwargs.get('pk')
        
        # SUPERADMIN can edit anyone
        if request.user.role == 'SUPERADMIN':
            return view_func(request, *args, **kwargs)
        
        # HR can edit everyone except SUPERADMIN
        if request.user.role == 'HR' and employee_id:
            try:
                employee = User.objects.get(pk=employee_id)
                if employee.is_superuser or employee.role == 'SUPERADMIN':
                    messages.error(request, '❌ HR cannot edit SUPERADMIN accounts!')
                    return redirect('employees:list')
            except User.DoesNotExist:
                pass
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def prevent_manager_edit_superadmin_hr(view_func):
    """
    Decorator to prevent Managers from editing SUPERADMIN or HR accounts.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        employee_id = kwargs.get('pk')
        
        # SUPERADMIN can edit anyone
        if request.user.role == 'SUPERADMIN':
            return view_func(request, *args, **kwargs)
        
        # HR can edit (handled by separate decorator)
        if request.user.role == 'HR':
            return view_func(request, *args, **kwargs)
        
        # Managers can only edit employees in their department
        if request.user.role == 'MANAGER' and employee_id:
            try:
                employee = User.objects.get(pk=employee_id)
                
                # Cannot edit SUPERADMIN or HR
                if employee.is_superuser or employee.role in ['SUPERADMIN', 'HR']:
                    messages.error(request, '❌ Managers cannot edit SUPERADMIN or HR accounts!')
                    return redirect('employees:list')
                
                # Must be same department
                if employee.department != request.user.department:
                    messages.error(request, 'You can only edit employees in your department.')
                    return redirect('employees:list')
                    
            except User.DoesNotExist:
                pass
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def prevent_self_delete(view_func):
    """
    Decorator to prevent users from deleting their own account.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method == 'POST':
            employee_id = kwargs.get('pk')
            if employee_id and request.user.id == employee_id:
                messages.error(request, '❌ You cannot delete your own account!')
                return redirect('employees:list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==================== SELF-ACCESS DECORATOR ====================

def self_or_hr_required(view_func):
    """
    Decorator to allow access if user is viewing their own profile OR is HR/Admin.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        employee_id = kwargs.get('pk')
        
        # HR and Admin can access anyone
        if request.user.role in ['HR', 'SUPERADMIN']:
            return view_func(request, *args, **kwargs)
        
        # Employees can only access themselves
        if request.user.role == 'EMPLOYEE' and request.user.id == employee_id:
            return view_func(request, *args, **kwargs)
        
        # Managers can access their department employees
        if request.user.role == 'MANAGER' and employee_id:
            try:
                employee = User.objects.get(pk=employee_id)
                if employee.department == request.user.department:
                    return view_func(request, *args, **kwargs)
            except User.DoesNotExist:
                pass
        
        # If none of the above conditions met, deny access
        messages.error(request, 'You do not have permission to access this profile.')
        return redirect('dashboard')
    return _wrapped_view


# ==================== COMBINED DECORATORS ====================

def appropriate_edit_permission(view_func):
    """
    Combined decorator that applies all edit permission rules:
    - SUPERADMIN can edit anyone
    - HR can edit everyone except SUPERADMIN
    - Managers can only edit employees in their department (not HR/SUPERADMIN)
    - No one can edit themselves (optional)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        employee_id = kwargs.get('pk')
        
        if not employee_id:
            return view_func(request, *args, **kwargs)
        
        try:
            target_employee = User.objects.get(pk=employee_id)
            
            # SUPERADMIN can edit anyone
            if request.user.role == 'SUPERADMIN':
                return view_func(request, *args, **kwargs)
            
            # HR can edit everyone except SUPERADMIN
            if request.user.role == 'HR':
                if target_employee.is_superuser or target_employee.role == 'SUPERADMIN':
                    messages.error(request, '❌ HR cannot edit SUPERADMIN accounts!')
                    return redirect('employees:list')
                return view_func(request, *args, **kwargs)
            
            # Managers can only edit employees in their department (not HR/SUPERADMIN)
            if request.user.role == 'MANAGER':
                if target_employee.is_superuser or target_employee.role in ['SUPERADMIN', 'HR']:
                    messages.error(request, '❌ Managers cannot edit SUPERADMIN or HR accounts!')
                    return redirect('employees:list')
                
                if target_employee.department != request.user.department:
                    messages.error(request, 'You can only edit employees in your department.')
                    return redirect('employees:list')
                
                return view_func(request, *args, **kwargs)
            
            # Anyone else cannot edit
            messages.error(request, 'You do not have permission to edit this employee.')
            return redirect('employees:list')
            
        except User.DoesNotExist:
            messages.error(request, 'Employee not found.')
            return redirect('employees:list')
    
    return _wrapped_view


def appropriate_view_permission(view_func):
    """
    Combined decorator for view-only access:
    - SUPERADMIN can view anyone
    - HR can view anyone
    - Managers can view only their department
    - Employees can view only themselves
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        employee_id = kwargs.get('pk')
        
        if not employee_id:
            return view_func(request, *args, **kwargs)
        
        try:
            target_employee = User.objects.get(pk=employee_id)
            
            # SUPERADMIN and HR can view anyone
            if request.user.role in ['SUPERADMIN', 'HR']:
                return view_func(request, *args, **kwargs)
            
            # Managers can view only their department
            if request.user.role == 'MANAGER':
                if target_employee.department == request.user.department:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'You can only view employees in your department.')
                    return redirect('employees:list')
            
            # Employees can view only themselves
            if request.user.role == 'EMPLOYEE':
                if request.user.id == employee_id:
                    return view_func(request, *args, **kwargs)
                else:
                    messages.error(request, 'You can only view your own profile.')
                    return redirect('dashboard')
            
        except User.DoesNotExist:
            messages.error(request, 'Employee not found.')
            return redirect('employees:list')
    
    return _wrapped_view