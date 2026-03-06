from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from performance.models import Performance
from faker import Faker
import random
from datetime import datetime, timedelta

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Creates sample data for testing'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create departments
        departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations']
        roles = ['EMPLOYEE', 'MANAGER', 'HR']
        
        # Create users
        users = []
        for i in range(50):
            role = random.choice(roles)
            department = random.choice(departments)
            
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password='password123',
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                employee_id=f"EMP{1000 + i:06d}",
                department=department,
                designation=fake.job(),
                phone=fake.phone_number(),
                salary=random.randint(30000, 120000),
                role=role,
                employment_status='ACTIVE',
                date_of_joining=fake.date_between(start_date='-5y', end_date='today')
            )
            users.append(user)
            self.stdout.write(f'Created user: {user.username}')
        
        # Create performance records
        current_year = datetime.now().year
        for user in users:
            for month in range(1, 13):
                if random.random() > 0.3:  # 70% chance of having a record
                    Performance.objects.create(
                        employee=user,
                        month=month,
                        year=current_year,
                        rating=random.uniform(5, 10),
                        goals_completed=random.randint(5, 10),
                        attendance_percentage=random.uniform(85, 100)
                    )
            
            # Add some previous year records
            for month in range(1, 6):
                Performance.objects.create(
                    employee=user,
                    month=month,
                    year=current_year - 1,
                    rating=random.uniform(5, 10),
                    goals_completed=random.randint(5, 10),
                    attendance_percentage=random.uniform(85, 100)
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully created sample data'))