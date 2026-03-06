from django.db import models

# Create your models here.
# ml_engine/models.py

from django.db import models
from django.conf import settings
import pickle

class MLModel(models.Model):
    """Store trained ML models"""
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=50, choices=[
        ('PERFORMANCE', 'Performance Predictor'),
        ('CHURN', 'Churn Predictor'),
        ('ANOMALY', 'Anomaly Detector'),
    ])
    version = models.CharField(max_length=20)
    accuracy = models.FloatField(null=True, blank=True)
    trained_on = models.DateTimeField(auto_now_add=True)
    model_file = models.BinaryField()  # Serialized model
    is_active = models.BooleanField(default=True)
    
    def save_model(self, model_object):
        """Save sklearn model to database"""
        self.model_file = pickle.dumps(model_object)
        self.save()
    
    def load_model(self):
        """Load sklearn model from database"""
        return pickle.loads(self.model_file)

class PerformancePrediction(models.Model):
    """Store predictions for employees"""
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    prediction_date = models.DateTimeField(auto_now_add=True)
    next_month_score = models.FloatField()
    confidence = models.FloatField()
    trend = models.CharField(max_length=20, choices=[
        ('IMPROVING', 'Improving'),
        ('STABLE', 'Stable'),
        ('DECLINING', 'Declining'),
    ])
    action_needed = models.BooleanField(default=False)
    
class ChurnRisk(models.Model):
    """Employee churn predictions"""
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    risk_score = models.FloatField()  # 0-100
    risk_level = models.CharField(max_length=20, choices=[
        ('LOW', 'Low Risk'),
        ('MEDIUM', 'Medium Risk'),
        ('HIGH', 'High Risk'),
    ])
    top_reasons = models.JSONField()
    recommended_action = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class AnomalyAlert(models.Model):
    """Detect unusual patterns"""
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=50, choices=[
        ('SCORE_DROP', 'Sudden Score Drop'),
        ('ATTENDANCE_DROP', 'Attendance Drop'),
        ('GOALS_MISSING', 'Goals Not Met'),
        ('UNUSUAL_PATTERN', 'Unusual Pattern'),
    ])
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ])
    details = models.JSONField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)