from django import forms
from .models import Performance
from accounts.models import User
from datetime import datetime


class PerformanceForm(forms.ModelForm):
    """Form for creating and updating performance records"""
    
    class Meta:
        model = Performance
        fields = ['employee', 'month', 'year', 'rating', 'goals_completed', 'attendance_percentage']
        
        widgets = {
            'employee': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select employee'
            }),
            'month': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 12,
                'placeholder': 'Enter month (1-12)'
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2000,
                'max': 2100,
                'placeholder': 'Enter year (e.g., 2026)'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'step': '0.1',
                'placeholder': 'Rate 1.0 to 10.0'
            }),
            'goals_completed': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 20,
                'placeholder': 'Number of goals completed (0-20)'
            }),
            'attendance_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': '0.1',
                'placeholder': 'Attendance percentage (0-100)'
            }),
        }
        
        labels = {
            'employee': 'Employee *',
            'month': 'Month *',
            'year': 'Year *',
            'rating': 'Rating (1-10) *',
            'goals_completed': 'Goals Completed *',
            'attendance_percentage': 'Attendance Percentage *',
        }
        
        help_texts = {
            'rating': 'Rate from 1 (poor) to 10 (excellent)',
            'goals_completed': 'Number of goals achieved this month (max 20)',
            'attendance_percentage': 'Attendance percentage for the month (0-100%)',
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with user context and dynamic queryset"""
        self.user = kwargs.pop('user', None)
        self.is_update = kwargs.get('instance') is not None
        super().__init__(*args, **kwargs)
        
        # Filter employees based on user role
        if self.user:
            # Base queryset - only active employees
            employees = User.objects.filter(
                is_soft_deleted=False,
                employment_status='ACTIVE'
            ).order_by('first_name', 'last_name')
            
            # Apply role-based filtering
            if self.user.role == 'MANAGER':
                employees = employees.filter(department=self.user.department)
            elif self.user.role == 'EMPLOYEE':
                employees = employees.filter(id=self.user.id)
            
            self.fields['employee'].queryset = employees
        
        # Set initial values for new records
        if not self.instance.pk:
            self.fields['month'].initial = datetime.now().month
            self.fields['year'].initial = datetime.now().year
        
        # Mark required fields
        for field_name in ['employee', 'month', 'year', 'rating', 'goals_completed', 'attendance_percentage']:
            self.fields[field_name].required = True
    
    # ==================== FIELD VALIDATION ====================
    
    def clean_month(self):
        """Validate month is between 1 and 12"""
        month = self.cleaned_data.get('month')
        if month and (month < 1 or month > 12):
            raise forms.ValidationError('❌ Month must be between 1 and 12.')
        return month
    
    def clean_year(self):
        """Validate year is reasonable"""
        year = self.cleaned_data.get('year')
        current_year = datetime.now().year
        if year and (year < 2000 or year > current_year + 1):
            raise forms.ValidationError(f'❌ Year must be between 2000 and {current_year + 1}.')
        return year
    
    def clean_rating(self):
        """Validate rating is between 1 and 10"""
        rating = self.cleaned_data.get('rating')
        if rating is not None:
            if rating < 1 or rating > 10:
                raise forms.ValidationError('❌ Rating must be between 1.0 and 10.0.')
        return rating
    
    def clean_goals_completed(self):
        """Validate goals completed is not negative"""
        goals = self.cleaned_data.get('goals_completed')
        if goals is not None:
            if goals < 0:
                raise forms.ValidationError('❌ Goals completed cannot be negative.')
            if goals > 20:
                raise forms.ValidationError('❌ Goals completed cannot exceed 20.')
        return goals
    
    def clean_attendance_percentage(self):
        """Validate attendance percentage is between 0 and 100"""
        attendance = self.cleaned_data.get('attendance_percentage')
        if attendance is not None:
            if attendance < 0 or attendance > 100:
                raise forms.ValidationError('❌ Attendance percentage must be between 0 and 100.')
        return attendance
    
    # ==================== CROSS-FIELD VALIDATION ====================
    
    def clean(self):
        """Validate that no duplicate performance record exists"""
        cleaned_data = super().clean()
        
        employee = cleaned_data.get('employee')
        month = cleaned_data.get('month')
        year = cleaned_data.get('year')
        
        if employee and month and year:
            # Check for existing record
            existing = Performance.objects.filter(
                employee=employee,
                month=month,
                year=year
            )
            
            # Exclude current instance when updating
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                existing_record = existing.first()
                raise forms.ValidationError(
                    f'❌ Performance record already exists for {employee.get_full_name()} '
                    f'in {month}/{year}. '
                    f'Score: {existing_record.calculated_score:.1f}'
                )
        
        return cleaned_data


class PerformanceSearchForm(forms.Form):
    """Form for searching and filtering performance records"""
    
    employee = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by employee name...',
            'class': 'form-control search-input'
        })
    )
    
    year = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control filter-select'})
    )
    
    month = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control filter-select'})
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize form with dynamic choices from database"""
        super().__init__(*args, **kwargs)
        
        # Get available years from database
        years = Performance.objects.values_list('year', flat=True).distinct().order_by('-year')
        
        if years:
            year_choices = [('', 'All Years')] + [(y, y) for y in years]
        else:
            # If no records, show current year
            current_year = datetime.now().year
            year_choices = [
                ('', 'All Years'),
                (current_year, current_year)
            ]
        
        self.fields['year'].choices = year_choices
        
        # Month choices with names
        months = [
            (1, 'January'), (2, 'February'), (3, 'March'),
            (4, 'April'), (5, 'May'), (6, 'June'),
            (7, 'July'), (8, 'August'), (9, 'September'),
            (10, 'October'), (11, 'November'), (12, 'December')
        ]
        self.fields['month'].choices = [('', 'All Months')] + months
    
    def get_filters(self):
        """Return active filters as a dictionary"""
        filters = {}
        if self.is_valid():
            data = self.cleaned_data
            
            if data.get('year'):
                filters['year'] = data['year']
            if data.get('month'):
                filters['month'] = data['month']
        
        return filters
    
    def get_search_query(self):
        """Return search query if any"""
        if self.is_valid():
            return self.cleaned_data.get('employee', '')
        return ''