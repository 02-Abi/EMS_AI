from django import forms
from django.core.exceptions import ValidationError
from accounts.models import User
import re
import random
import string


class EmployeeForm(forms.ModelForm):
    """Form for creating and updating employees"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': 'Enter new password or leave blank'
        }),
        required=False,
        help_text=""  # Will be set dynamically in __init__
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
            'placeholder': 'Confirm new password'
        }),
        required=False,
        label="Confirm Password"
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'department', 'designation', 'phone', 'salary',
            'role', 'employment_status', 'date_of_joining'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'username',
                'placeholder': 'johndoe'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'autocomplete': 'email',
                'placeholder': 'john@company.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Doe'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Engineering'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Senior Developer'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '75000.00'
            }),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-control'}),
            'date_of_joining': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
        }
        labels = {
            'username': 'Username *',
            'email': 'Email *',
            'first_name': 'First Name *',
            'last_name': 'Last Name *',
            'department': 'Department',
            'designation': 'Designation',
            'phone': 'Phone',
            'salary': 'Salary',
            'role': 'Role *',
            'employment_status': 'Status',
            'date_of_joining': 'Date of Joining',
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with user context and dynamic help texts"""
        self.user = kwargs.pop('user', None)
        self.is_update = kwargs.get('instance') is not None
        super().__init__(*args, **kwargs)
        
        # Make required fields
        self.fields['email'].required = True
        self.fields['role'].required = True
        
        # Set password help text based on mode
        if self.instance.pk:
            # UPDATE mode
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = (
                "👆 LEAVE BLANK to keep current password | "
                "✏️ FILL BOTH fields to change password"
            )
            self.fields['password'].widget.attrs['placeholder'] = 'Leave blank to keep current'
        else:
            # CREATE mode
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = (
                "👆 LEAVE BLANK to auto-generate a password | "
                "✏️ FILL BOTH fields to set your own password"
            )
            self.fields['password'].widget.attrs['placeholder'] = 'Leave blank for auto-generate'
        
        # Add CSS classes for error styling
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = 'required'
    
    # ==================== VALIDATION METHODS ====================
    
    def clean_username(self):
        """Validate username uniqueness and format"""
        username = self.cleaned_data.get('username')
        if username:
            username = username.lower()
            qs = User.objects.all_with_deleted().filter(username=username)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('This username is already taken.')
        return username
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            qs = User.objects.filter(email=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('This email is already registered.')
        return email
    
    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = re.sub(r'[\s\-\(\)]', '', phone)
            if not re.match(r'^\+?[0-9]{10,15}$', phone):
                raise ValidationError(
                    'Enter a valid phone number with 10-15 digits (e.g., +1234567890).'
                )
        return phone
    
    def clean_salary(self):
        """Validate salary is not negative"""
        salary = self.cleaned_data.get('salary')
        if salary is not None and salary < 0:
            raise ValidationError('Salary cannot be negative.')
        return salary
    
    def clean(self):
        """Validate password match and other cross-field validations"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password:
            if password != confirm_password:
                raise ValidationError('Passwords do not match.')
            if len(password) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
        elif confirm_password:
            raise ValidationError('Please fill the password field as well.')
        
        role = cleaned_data.get('role')
        department = cleaned_data.get('department')
        
        if role == 'MANAGER' and not department:
            raise ValidationError('Department is required for Manager role.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save employee with password handling"""
        user = super().save(commit=False)
        
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        elif not self.instance.pk:
            random_password = ''.join(random.choices(
                string.ascii_letters + string.digits + '!@#$%^&*', k=10
            ))
            user.set_password(random_password)
            self.generated_password = random_password
        
        if commit:
            user.save()
        return user
    
    def get_generated_password(self):
        """Return auto-generated password if any"""
        return getattr(self, 'generated_password', None)


class EmployeeSearchForm(forms.Form):
    """Form for searching and filtering employees"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by name, email, or ID...',
            'class': 'search-input'
        })
    )
    
    department = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    
    role = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={'class': 'filter-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get distinct departments from database
        departments = User.objects.filter(
            is_soft_deleted=False,
            department__isnull=False
        ).exclude(
            department=''
        ).values_list('department', flat=True).distinct().order_by('department')
        
        # Get distinct roles from database
        roles = User.objects.filter(
            is_soft_deleted=False
        ).values_list('role', flat=True).distinct()
        
        # 🔥 FIX: Always show ALL possible statuses, not just from database
        status_choices = [
            ('', 'All Statuses'),
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
            ('TERMINATED', 'Terminated'),
            ('ON_LEAVE', 'On Leave'),
        ]
        
        # Get role display names
        role_display = dict(User.ROLE_CHOICES)
        
        # Set choices
        self.fields['department'].choices = [('', 'All Departments')] + [
            (d, d) for d in departments if d
        ]
        
        self.fields['role'].choices = [('', 'All Roles')] + [
            (r, role_display.get(r, r)) for r in roles if r
        ]
        
        self.fields['status'].choices = status_choices  # 🔥 Now shows all statuses
    
    def get_filters(self):
        """Return active filters as a dictionary"""
        filters = {}
        if self.is_valid():
            data = self.cleaned_data
            if data.get('department'):
                filters['department'] = data['department']
            if data.get('role'):
                filters['role'] = data['role']
            if data.get('status'):
                filters['employment_status'] = data['status']
        return filters
    
    def get_search_query(self):
        """Return search query if any"""
        if self.is_valid():
            return self.cleaned_data.get('query', '')
        return ''