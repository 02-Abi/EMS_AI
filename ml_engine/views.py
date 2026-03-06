from django.shortcuts import render, redirect  # ✅ Add redirect here
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PerformancePrediction, ChurnRisk, AnomalyAlert
from .predictors import PerformancePredictor
from accounts.models import User
from performance.models import Performance

@login_required
def ml_dashboard(request):
    """ML Dashboard view"""
    context = {
        'predictions': PerformancePrediction.objects.all()[:10],
        'high_risk': ChurnRisk.objects.filter(risk_level='HIGH')[:5],
        'anomalies': AnomalyAlert.objects.filter(is_resolved=False)[:5],
        'total_predictions': PerformancePrediction.objects.count(),
        'high_risk_count': ChurnRisk.objects.filter(risk_level='HIGH').count(),
        'anomaly_count': AnomalyAlert.objects.filter(is_resolved=False).count(),
    }
    return render(request, 'ml_engine/dashboard.html', context)

@login_required
def train_models(request):
    """Train ML models"""
    if request.method == 'POST':
        predictor = PerformancePredictor()
        success = predictor.train()
        if success:
            messages.success(request, '✅ ML Model trained successfully!')
            
            # Generate predictions for all employees
            for emp in User.objects.filter(is_soft_deleted=False):
                score, conf = predictor.predict_next_score(emp)
                if score:
                    PerformancePrediction.objects.create(
                        employee=emp,
                        next_month_score=score,
                        confidence=conf
                    )
        else:
            messages.warning(request, '⚠️ Not enough data for training')
    return redirect('ml_engine:dashboard')  # ✅ redirect now works