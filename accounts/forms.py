from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User
import re

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email, is_soft_deleted=False).exists():
            raise ValidationError('A user with this email already exists.')
        return email

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if user.is_soft_deleted:
            raise ValidationError('This account has been deactivated.', code='inactive')
        if user.employment_status != 'ACTIVE':
            raise ValidationError(f'This account is {user.employment_status.lower()}.', code='inactive')

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'department', 'designation')
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '+1234567890'}),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?1?\d{9,15}$', phone):
            raise ValidationError('Enter a valid phone number.')
        return phone