from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import JsonResponse
from datetime import datetime
from .models import Performance
from .forms import PerformanceForm, PerformanceSearchForm
from employees.decorators import hr_or_manager_required, hr_required
from audit.services import AuditService
from accounts.models import User

@login_required
def performance_list(request):
    # Base queryset
    performances = Performance.objects.select_related('employee').filter(
        employee__is_soft_deleted=False
    )
    
    # Role-based filtering
    if request.user.role == 'MANAGER':
        performances = performances.filter(employee__department=request.user.department)
    elif request.user.role == 'EMPLOYEE':
        performances = performances.filter(employee=request.user)
    
    # Search form
    search_form = PerformanceSearchForm(request.GET)
    
    if search_form.is_valid():
        employee_query = search_form.cleaned_data.get('employee')
        year = search_form.cleaned_data.get('year')
        month = search_form.cleaned_data.get('month')
        
        if employee_query:
            performances = performances.filter(
                Q(employee__first_name__icontains=employee_query) |
                Q(employee__last_name__icontains=employee_query) |
                Q(employee__employee_id__icontains=employee_query)
            )
        
        if year:
            performances = performances.filter(year=year)
        
        if month:
            performances = performances.filter(month=month)
    
    # Pagination
    paginator = Paginator(performances.order_by('-year', '-month'), 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'can_add': request.user.role in ['HR', 'SUPERADMIN', 'MANAGER'],
    }
    
    return render(request, 'performance/list.html', context)

@login_required
@hr_or_manager_required
def performance_create(request):
    if request.method == 'POST':
        form = PerformanceForm(request.POST, user=request.user)
        if form.is_valid():
            performance = form.save()
            
            AuditService.log_action(
                user=request.user,
                action_type='CREATE',
                target_model='Performance',
                target_id=performance.id,
                ip_address=AuditService.get_client_ip(request),
                details=f"Created performance record for {performance.employee.get_full_name()}"
            )
            
            messages.success(request, 'Performance record created successfully.')
            return redirect('performance:list')
    else:
        form = PerformanceForm(user=request.user)
        # Pre-fill current month/year
        form.fields['month'].initial = datetime.now().month
        form.fields['year'].initial = datetime.now().year
    
    return render(request, 'performance/create.html', {'form': form})

@login_required
def performance_detail(request, pk):
    performance = get_object_or_404(
        Performance.objects.select_related('employee'),
        pk=pk,
        employee__is_soft_deleted=False
    )
    
    # Check permissions
    if request.user.role == 'EMPLOYEE' and request.user.id != performance.employee.id:
        messages.error(request, 'You do not have permission to view this record.')
        return redirect('performance:list')
    
    if request.user.role == 'MANAGER' and performance.employee.department != request.user.department:
        messages.error(request, 'You can only view performance records in your department.')
        return redirect('performance:list')
    
    return render(request, 'performance/detail.html', {'performance': performance})

@login_required
@hr_or_manager_required
def performance_update(request, pk):
    performance = get_object_or_404(Performance, pk=pk)
    
    # Check permissions for managers
    if request.user.role == 'MANAGER' and performance.employee.department != request.user.department:
        messages.error(request, 'You can only update performance records in your department.')
        return redirect('performance:list')
    
    if request.method == 'POST':
        form = PerformanceForm(request.POST, instance=performance, user=request.user)
        if form.is_valid():
            updated_performance = form.save()
            
            AuditService.log_action(
                user=request.user,
                action_type='UPDATE',
                target_model='Performance',
                target_id=performance.id,
                ip_address=AuditService.get_client_ip(request),
                details=f"Updated performance record for {performance.employee.get_full_name()}"
            )
            
            messages.success(request, 'Performance record updated successfully.')
            return redirect('performance:detail', pk=performance.pk)
    else:
        form = PerformanceForm(instance=performance, user=request.user)
    
    return render(request, 'performance/update.html', {'form': form, 'performance': performance})

@login_required
@hr_required
def performance_delete(request, pk):
    performance = get_object_or_404(Performance, pk=pk)
    
    if request.method == 'POST':
        employee_name = performance.employee.get_full_name()
        performance.delete()
        
        AuditService.log_action(
            user=request.user,
            action_type='DELETE',
            target_model='Performance',
            target_id=pk,
            ip_address=AuditService.get_client_ip(request),
            details=f"Deleted performance record for {employee_name}"
        )
        
        messages.success(request, 'Performance record deleted successfully.')
        return redirect('performance:list')
    
    return render(request, 'performance/delete.html', {'performance': performance})

@login_required
def leaderboard(request):
    # Get top performers based on calculated_score
    current_year = datetime.now().year
    
    performances = Performance.objects.filter(
        year=current_year,
        employee__is_soft_deleted=False
    ).select_related('employee')
    
    # Role-based filtering
    if request.user.role == 'MANAGER':
        performances = performances.filter(employee__department=request.user.department)
    elif request.user.role == 'EMPLOYEE':
        performances = performances.filter(employee=request.user)
    
    # Get latest performance for each employee
    from django.db.models import Max
    latest_performances = performances.values('employee').annotate(
        latest=Max('created_at')
    ).values_list('latest', flat=True)
    
    top_performers = performances.filter(
        created_at__in=latest_performances
    ).order_by('-calculated_score')[:10]
    
    context = {
        'top_performers': top_performers,
        'current_year': current_year,
    }
    
    return render(request, 'performance/leaderboard.html', context)

@login_required
def department_average(request):
    departments = User.objects.filter(
        is_soft_deleted=False,
        performances__isnull=False
    ).values_list('department', flat=True).distinct()
    
    year = request.GET.get('year', datetime.now().year)
    
    department_stats = []
    for dept in departments:
        if dept:  # Skip empty departments
            stats = Performance.get_department_average(dept, int(year))
            if stats['avg_score']:
                department_stats.append({
                    'name': dept,
                    'avg_score': round(stats['avg_score'], 2),
                    'avg_rating': round(stats['avg_rating'], 2),
                    'avg_attendance': round(stats['avg_attendance'], 2),
                })
    
    # Sort by average score
    department_stats.sort(key=lambda x: x['avg_score'], reverse=True)
    
    context = {
        'department_stats': department_stats,
        'selected_year': year,
        'years': range(2020, datetime.now().year + 1),
    }
    
    return render(request, 'performance/department_avg.html', context)