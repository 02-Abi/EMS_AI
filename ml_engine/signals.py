# ml_engine/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from performance.models import Performance
from .predictors import PerformancePredictor
from .models import PerformancePrediction
from accounts.models import User

@receiver(post_save, sender=Performance)
def retrain_on_performance_save(sender, instance, **kwargs):
    # Avoid infinite loops and only train on new records (optional)
    if kwargs.get('created', False):
        # Run training in background (async) or use a task queue like Celery
        # For simplicity, we'll run it directly (may slow down the request)
        predictor = PerformancePredictor()
        if predictor.train():
            # Regenerate predictions for all employees
            for emp in User.objects.filter(is_soft_deleted=False):
                score, conf = predictor.predict_next_score(emp)
                if score:
                    PerformancePrediction.objects.update_or_create(
                        employee=emp,
                        defaults={
                            'next_month_score': score,
                            'confidence': conf
                        }
                    )