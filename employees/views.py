# employees/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.models import User
from .forms import EmployeeForm, EmployeeSearchForm
from .decorators import hr_required, hr_or_manager_required, appropriate_edit_permission
from audit.services import AuditService


# ==================== EMPLOYEE LIST VIEW ====================
@login_required
def employee_list(request):
    """
    Display list of employees with search, filter and pagination.
    Access depends on user role.
    """
    # Base queryset - exclude soft deleted
    employees = User.objects.filter(is_soft_deleted=False)
    
    # Apply role-based filtering
    if request.user.role == 'MANAGER':
        employees = employees.filter(department=request.user.department)
    elif request.user.role == 'EMPLOYEE':
        employees = employees.filter(id=request.user.id)
    
    # Initialize search form with GET data
    search_form = EmployeeSearchForm(request.GET)
    
    # Apply search filters if form is valid
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        department = search_form.cleaned_data.get('department')
        role = search_form.cleaned_data.get('role')
        status = search_form.cleaned_data.get('status')
        
        # Text search across multiple fields
        if query:
            employees = employees.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(employee_id__icontains=query) |
                Q(username__icontains=query)
            )
        
        # Apply dropdown filters
        if department:
            employees = employees.filter(department=department)
        if role:
            employees = employees.filter(role=role)
        if status:
            employees = employees.filter(employment_status=status)
    
    # Add permission flags for each employee
    for employee in employees:
        # View permission - everyone can view (but limited by role in detail view)
        employee.can_view = True
        
        # Edit permissions
        employee.can_edit = False
        if request.user.role == 'SUPERADMIN':
            employee.can_edit = True
        elif request.user.role == 'HR' and employee.role != 'SUPERADMIN':
            employee.can_edit = True
        elif request.user.role == 'MANAGER':
            if (employee.department == request.user.department and 
                employee.role not in ['SUPERADMIN', 'HR']):
                employee.can_edit = True
        
        # Delete permissions
        employee.can_delete = False
        if request.user.role == 'SUPERADMIN' and employee.username != request.user.username:
            employee.can_delete = True
        elif request.user.role == 'HR' and employee.role != 'SUPERADMIN' and employee.username != request.user.username:
            employee.can_delete = True
    
    # Pagination - 10 items per page
    paginator = Paginator(employees.order_by('employee_id'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Prepare context for template
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'is_hr': request.user.role == 'HR',
        'is_manager': request.user.role == 'MANAGER',
        'is_superadmin': request.user.role == 'SUPERADMIN',
    }
    
    return render(request, 'employees/list.html', context)


# ==================== EMPLOYEE CREATE VIEW ====================
@login_required
@hr_required
def employee_create(request):
    """
    Create new employee - HR and Admin only.
    Auto-generates employee_id and handles password.
    """
    if request.method == 'POST':
        form = EmployeeForm(request.POST, user=request.user)
        
        if form.is_valid():
            employee = form.save()
            
            # Log the creation action
            AuditService.log_action(
                user=request.user,
                action_type='CREATE',
                target_model='Employee',
                target_id=employee.id,
                ip_address=AuditService.get_client_ip(request),
                details=f"Created employee: {employee.get_full_name()}"
            )
            
            messages.success(
                request, 
                f'Employee {employee.get_full_name()} created successfully.'
            )
            return redirect('employees:list')
    else:
        form = EmployeeForm(user=request.user)
    
    return render(request, 'employees/create.html', {'form': form})


# ==================== EMPLOYEE DETAIL VIEW ====================
@login_required
def employee_detail(request, pk):
    """
    View employee details with proper permission checks.
    """
    employee = get_object_or_404(
        User.objects.filter(is_soft_deleted=False), 
        pk=pk
    )
    
    # Permission checks
    if request.user.role == 'EMPLOYEE' and request.user.id != employee.id:
        messages.error(request, 'You do not have permission to view this employee.')
        return redirect('dashboard')
    
    if request.user.role == 'MANAGER' and employee.department != request.user.department:
        messages.error(request, 'You can only view employees in your department.')
        return redirect('employees:list')
    
    # Add permission flags for template
    employee.can_edit = False
    employee.can_delete = False
    
    # Edit permissions
    if request.user.role == 'SUPERADMIN':
        employee.can_edit = True
    elif request.user.role == 'HR' and employee.role != 'SUPERADMIN':
        employee.can_edit = True
    elif request.user.role == 'MANAGER':
        if (employee.department == request.user.department and 
            employee.role not in ['SUPERADMIN', 'HR']):
            employee.can_edit = True
    
    # Delete permissions
    if request.user.role == 'SUPERADMIN' and employee.username != request.user.username:
        employee.can_delete = True
    elif request.user.role == 'HR' and employee.role != 'SUPERADMIN' and employee.username != request.user.username:
        employee.can_delete = True
    
    return render(request, 'employees/detail.html', {'employee': employee})


# ==================== EMPLOYEE UPDATE VIEW ====================
@login_required
@hr_or_manager_required
def employee_update(request, pk):
    """
    Update employee details with proper permission checks.
    """
    employee = get_object_or_404(
        User.objects.filter(is_soft_deleted=False), 
        pk=pk
    )
    
    # SUPERADMIN can edit anyone
    if request.user.role == 'SUPERADMIN':
        pass  # Allow
    
    # HR can edit everyone except SUPERADMIN
    elif request.user.role == 'HR':
        if employee.role == 'SUPERADMIN':
            messages.error(request, 'HR cannot edit SUPERADMIN accounts!')
            return redirect('employees:list')
    
    # Manager can only edit their department employees (not HR/SUPERADMIN)
    elif request.user.role == 'MANAGER':
        if employee.role in ['SUPERADMIN', 'HR']:
            messages.error(request, 'Managers cannot edit SUPERADMIN or HR accounts!')
            return redirect('employees:list')
        if employee.department != request.user.department:
            messages.error(request, 'You can only update employees in your department.')
            return redirect('employees:list')
    
    # Store old salary for audit tracking
    old_salary = employee.salary
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee, user=request.user)
        
        if form.is_valid():
            updated_employee = form.save()
            
            # Prepare audit details
            audit_details = f"Updated employee details"
            if old_salary != updated_employee.salary:
                audit_details += f". Salary changed from {old_salary} to {updated_employee.salary}"
            
            # Log the update action
            AuditService.log_action(
                user=request.user,
                action_type='UPDATE',
                target_model='Employee',
                target_id=employee.id,
                ip_address=AuditService.get_client_ip(request),
                details=audit_details
            )
            
            messages.success(
                request, 
                f'Employee {employee.get_full_name()} updated successfully.'
            )
            return redirect('employees:detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee, user=request.user)
    
    return render(
        request, 
        'employees/update.html', 
        {'form': form, 'employee': employee}
    )


# ==================== EMPLOYEE SOFT DELETE VIEW ====================
@login_required
def employee_delete(request, pk):
    """
    Soft delete employee - sets is_soft_deleted=True.
    Proper permission checks applied.
    """
    employee = get_object_or_404(
        User.objects.filter(is_soft_deleted=False), 
        pk=pk
    )
    
    # Permission checks
    if request.user.role == 'SUPERADMIN':
        if employee.username == request.user.username:
            messages.error(request, 'You cannot delete your own account!')
            return redirect('employees:list')
        # Allow
    
    elif request.user.role == 'HR':
        if employee.role == 'SUPERADMIN':
            messages.error(request, 'HR cannot delete SUPERADMIN accounts!')
            return redirect('employees:list')
        if employee.username == request.user.username:
            messages.error(request, 'You cannot delete your own account!')
            return redirect('employees:list')
        # Allow for others
    
    else:
        messages.error(request, 'You do not have permission to delete employees.')
        return redirect('employees:list')
    
    if request.method == 'POST':
        # Perform soft delete
        employee.is_soft_deleted = True
        employee.save()
        
        # Log the delete action
        AuditService.log_action(
            user=request.user,
            action_type='DELETE',
            target_model='Employee',
            target_id=employee.id,
            ip_address=AuditService.get_client_ip(request),
            details=f"Soft deleted employee: {employee.get_full_name()}"
        )
        
        messages.success(
            request, 
            f'Employee {employee.get_full_name()} has been deactivated.'
        )
        return redirect('employees:list')
    
    return render(request, 'employees/delete.html', {'employee': employee})


# ==================== EMPLOYEE RESTORE VIEW ====================
@login_required
@hr_required
def employee_restore(request, pk):
    """
    Restore soft deleted employee - sets is_soft_deleted=False.
    HR and Admin only.
    """
    employee = get_object_or_404(
        User.objects.all_with_deleted(), 
        pk=pk, 
        is_soft_deleted=True
    )
    
    if request.method == 'POST':
        # Restore the employee
        employee.is_soft_deleted = False
        employee.save()
        
        messages.success(
            request, 
            f'Employee {employee.get_full_name()} has been restored.'
        )
        return redirect('employees:list')
    
    return render(request, 'employees/restore.html', {'employee': employee})