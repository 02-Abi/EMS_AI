# create_risk_data.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ems.settings')
django.setup()

from accounts.models import User
from ml_engine.models import PerformancePrediction, ChurnRisk

for emp in User.objects.all():
    pred = PerformancePrediction.objects.filter(employee=emp).first()
    if pred:
        score = pred.next_month_score
        if score >= 85:
            risk_level = 'LOW'
            risk_score = 20
        elif score >= 75:
            risk_level = 'MEDIUM'
            risk_score = 50
        else:
            risk_level = 'HIGH'
            risk_score = 80

        ChurnRisk.objects.create(
            employee=emp,
            risk_score=risk_score,
            risk_level=risk_level,
            top_reasons=['Based on performance prediction'],
            recommended_action='Monitor performance'
        )
        print(f"✅ Created risk for {emp.username}")
    else:
        print(f"⚠️ No prediction for {emp.username}")