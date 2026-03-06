# ems/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, Max
from accounts.models import User
from performance.models import Performance
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
def dashboard(request):
    # Employee statistics
    total_employees = User.objects.filter(is_soft_deleted=False).count()
    active_employees = User.objects.filter(
        is_soft_deleted=False,
        employment_status='ACTIVE'
    ).count()
    
    inactive_employees = User.objects.filter(
        is_soft_deleted=False,
        employment_status='INACTIVE'
    ).count()
    
    terminated_employees = User.objects.filter(
        is_soft_deleted=False,
        employment_status='TERMINATED'
    ).count()
    
    # Department distribution
    departments = User.objects.filter(
        is_soft_deleted=False,
        department__isnull=False
    ).exclude(
        department=''
    ).values('department').annotate(
        count=Count('id')
    ).order_by('-count')
    
    department_labels = [dept['department'] for dept in departments[:10]]
    department_counts = [dept['count'] for dept in departments[:10]]
    
    # Monthly performance trend
    end_date = timezone.now()
    start_date = end_date - timedelta(days=180)
    
    monthly_performance = Performance.objects.filter(
        created_at__gte=start_date,
        employee__is_soft_deleted=False
    ).extra(
        {'month': "strftime('%%Y-%%m', created_at)"}
    ).values('month').annotate(
        avg_score=Avg('calculated_score')
    ).order_by('month')
    
    performance_labels = [perf['month'] for perf in monthly_performance]
    performance_data = [float(perf['avg_score']) if perf['avg_score'] else 0 for perf in monthly_performance]
    
    # 🏆 Top 5 Performers – one per employee (best score in current year)
    current_year = datetime.now().year
    
    # Step 1: Get the best score for each employee in current year
    best_scores = Performance.objects.filter(
        year=current_year,
        employee__is_soft_deleted=False
    ).values('employee').annotate(
        best=Max('calculated_score')
    ).order_by('-best')[:5]  # top 5 employees by best score
    
    # Step 2: Fetch the actual Performance objects (to have all details)
    top_performers = []
    for entry in best_scores:
        perf = Performance.objects.filter(
            employee=entry['employee'],
            calculated_score=entry['best'],
            year=current_year
        ).select_related('employee').first()
        if perf:
            top_performers.append(perf)
    
    # ML widget counts (if you use them in dashboard.html)
    try:
        from ml_engine.models import PerformancePrediction, ChurnRisk, AnomalyAlert
        total_predictions = PerformancePrediction.objects.count()
        high_risk_count = ChurnRisk.objects.filter(risk_level='HIGH').count()
        anomaly_count = AnomalyAlert.objects.filter(is_resolved=False).count()
    except:
        total_predictions = 0
        high_risk_count = 0
        anomaly_count = 0
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'inactive_employees': inactive_employees,
        'terminated_employees': terminated_employees,
        'department_count': departments.count(),
        'department_labels': list(department_labels),
        'department_counts': list(department_counts),
        'performance_labels': list(performance_labels),
        'performance_data': list(performance_data),
        'top_performers': top_performers,
        # ML widget data (optional, for the integrated dashboard)
        'total_predictions': total_predictions,
        'high_risk_count': high_risk_count,
        'anomaly_count': anomaly_count,
    }
    
    return render(request, 'dashboard.html', context)