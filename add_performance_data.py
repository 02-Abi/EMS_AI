# add_performance_data.py
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ems.settings')
django.setup()

from accounts.models import User
from performance.models import Performance

employees = User.objects.all()

for month in [1, 2, 3]:  # January, February, March
    for emp in employees:
        rating = round(random.uniform(6.5, 9.5), 1)
        goals = random.randint(6, 10)
        attendance = round(random.uniform(85, 99), 1)
        
        Performance.objects.get_or_create(
            employee=emp,
            month=month,
            year=2026,
            defaults={
                'rating': rating,
                'goals_completed': goals,
                'attendance_percentage': attendance
            }
        )
print("✅ Added 3 months of performance data for all employees.")