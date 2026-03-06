from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from datetime import datetime


class Performance(models.Model):
    """Performance record model for employee evaluations"""
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performances',  # 🔥 IMPORTANT: This should be 'performances'
        verbose_name="Employee"
    )
    
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name="Month"
    )
    
    year = models.IntegerField(
        verbose_name="Year"
    )
    
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(1.0), MaxValueValidator(10.0)],
        verbose_name="Rating (1-10)",
        help_text="Rate the employee from 1 (poor) to 10 (excellent)"
    )
    
    goals_completed = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Goals Completed",
        help_text="Number of goals achieved this month"
    )
    
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Attendance %",
        help_text="Attendance percentage for the month"
    )
    
    calculated_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Calculated Score",
        help_text="Auto-calculated performance score"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    
    class Meta:
        verbose_name = "Performance Record"
        verbose_name_plural = "Performance Records"
        unique_together = ['employee', 'month', 'year']  # Prevent duplicates
        ordering = ['-year', '-month']  # 🔥 Show newest first
        indexes = [
            models.Index(fields=['employee', 'year', 'month']),
            models.Index(fields=['rating']),
            models.Index(fields=['calculated_score']),
        ]
    
    def save(self, *args, **kwargs):
        """
        Calculate performance score before saving
        Formula: (rating/10 * 50) + (goals/10 * 30) + (attendance/100 * 20)
        """
        # Normalize values
        rating_weight = float(self.rating) / 10 * 50
        goals_weight = min(float(self.goals_completed) / 10, 1.0) * 30
        attendance_weight = float(self.attendance_percentage) / 100 * 20
        
        # Calculate total score
        self.calculated_score = rating_weight + goals_weight + attendance_weight
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        """String representation"""
        employee_name = self.employee.get_full_name() or self.employee.username
        return f"{employee_name} - {self.month}/{self.year} - Score: {self.calculated_score:.1f}"
    
    @property
    def month_name(self):
        """Get month name"""
        months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
        return months[self.month - 1]
    
    @property
    def performance_level(self):
        """Get performance level based on score"""
        if self.calculated_score >= 80:
            return "Excellent"
        elif self.calculated_score >= 60:
            return "Good"
        elif self.calculated_score >= 40:
            return "Average"
        else:
            return "Needs Improvement"
    
    @property
    def performance_color(self):
        """Get color class for performance level"""
        if self.calculated_score >= 80:
            return "success"
        elif self.calculated_score >= 60:
            return "primary"
        elif self.calculated_score >= 40:
            return "warning"
        else:
            return "danger"
    
    @classmethod
    def get_department_average(cls, department, year=None):
        """Get average performance for a department"""
        if not year:
            year = datetime.now().year
        
        return cls.objects.filter(
            employee__department=department,
            year=year,
            employee__is_soft_deleted=False
        ).aggregate(
            avg_score=Avg('calculated_score'),
            avg_rating=Avg('rating'),
            avg_attendance=Avg('attendance_percentage')
        )