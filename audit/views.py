from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import AuditLog

@login_required
def audit_log_list(request):
    logs = AuditLog.objects.all().order_by('-timestamp')
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'audit/list.html', {'page_obj': page_obj})

@login_required
def audit_log_detail(request, pk):
    log = get_object_or_404(AuditLog, pk=pk)
    return render(request, 'audit/detail.html', {'log': log})