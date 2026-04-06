from django import forms
from django.core.exceptions import ValidationError
from accounts.models import User
import re


class EmployeeForm(forms.ModelForm):
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
        self.user = kwargs.pop('user', None)
        self.is_update = kwargs.get('instance') is not None
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['role'].required = True
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['required'] = 'required'

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Case‑insensitive uniqueness check, but store as typed
            qs = User.objects.all_with_deleted().filter(username__iexact=username)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError('This username is already taken.')
        return username   # Keep original case

    def clean_email(self):
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
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = re.sub(r'[\s\-\(\)]', '', phone)
            if not re.match(r'^\+?[0-9]{10,15}$', phone):
                raise ValidationError(
                    'Enter a valid phone number with 10-15 digits (e.g., +1234567890).'
                )
        return phone

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary is not None and salary < 0:
            raise ValidationError('Salary cannot be negative.')
        return salary

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        department = cleaned_data.get('department')
        if role == 'MANAGER' and not department:
            raise ValidationError('Department is required for Manager role.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if not self.instance.pk:  # new user
            user.set_unusable_password()
        if commit:
            user.save()
        return user


class EmployeeSearchForm(forms.Form):
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
        departments = User.objects.filter(
            is_soft_deleted=False,
            department__isnull=False
        ).exclude(
            department=''
        ).values_list('department', flat=True).distinct().order_by('department')
        roles = User.objects.filter(
            is_soft_deleted=False
        ).values_list('role', flat=True).distinct()
        status_choices = [
            ('', 'All Statuses'),
            ('ACTIVE', 'Active'),
            ('INACTIVE', 'Inactive'),
            ('TERMINATED', 'Terminated'),
            ('ON_LEAVE', 'On Leave'),
        ]
        role_display = dict(User.ROLE_CHOICES)
        self.fields['department'].choices = [('', 'All Departments')] + [(d, d) for d in departments if d]
        self.fields['role'].choices = [('', 'All Roles')] + [(r, role_display.get(r, r)) for r in roles if r]
        self.fields['status'].choices = status_choices

    def get_filters(self):
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
        if self.is_valid():
            return self.cleaned_data.get('query', '')
        return ''