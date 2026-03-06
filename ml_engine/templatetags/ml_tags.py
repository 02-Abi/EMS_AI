from django import template
from ml_engine.models import PerformancePrediction, ChurnRisk, AnomalyAlert

register = template.Library()

@register.filter
def get_ml_prediction(employee):
    """Get latest performance prediction for an employee"""
    try:
        return PerformancePrediction.objects.filter(employee=employee).first()
    except:
        return None

@register.filter
def get_churn_risk(employee):
    """Get latest churn risk for an employee"""
    try:
        return ChurnRisk.objects.filter(employee=employee).first()
    except:
        return None

@register.simple_tag
def high_risk_count():
    """Count of high risk employees"""
    try:
        return ChurnRisk.objects.filter(risk_level='HIGH').count()
    except:
        return 0

@register.simple_tag
def anomaly_count():
    """Count of unresolved anomalies"""
    try:
        return AnomalyAlert.objects.filter(is_resolved=False).count()
    except:
        return 0

@register.simple_tag
def total_predictions():
    """Total number of predictions"""
    try:
        return PerformancePrediction.objects.count()
    except:
        return 0