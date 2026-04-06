from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User
import re


class CustomUserCreationForm(UserCreationForm):
    """
    Form used when a new user registers.
    All new users default to the EMPLOYEE role.
    Username is stored exactly as typed (case preserved).
    """
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'password1', 'password2'
        )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Case‑insensitive uniqueness check
        if User.objects.all_with_deleted().filter(username__iexact=username).exists():
            raise ValidationError('This username is already taken.')
        return username  # Store as typed

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.all_with_deleted().filter(email__iexact=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email.lower()


class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form with case‑insensitive username and custom checks."""
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            # Case‑insensitive user lookup
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                raise ValidationError('Invalid username or password.', code='invalid')
            # Check password
            if not user.check_password(password):
                raise ValidationError('Invalid username or password.', code='invalid')
            # Custom checks (status, soft delete, usable password)
            if user.is_soft_deleted:
                raise ValidationError('This account has been deactivated.', code='inactive')
            if user.employment_status != 'ACTIVE':
                raise ValidationError(f'This account is {user.employment_status.lower()}.', code='inactive')
            if not user.has_usable_password():
                raise ValidationError(
                    'This account has no password set. Please use the "Set Password" link provided to you.',
                    code='inactive'
                )
            self.user_cache = user
        return self.cleaned_data


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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email

        qs = User.objects.all_with_deleted().filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('This email is already used by another employee.')
        return email.lower()


class EmployeeSetPasswordForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username')
    email = forms.EmailField(label='Email')
    first_name = forms.CharField(max_length=150, label='First Name')
    last_name = forms.CharField(max_length=150, label='Last Name', required=False)
    password1 = forms.CharField(widget=forms.PasswordInput, label='New Password', min_length=8)
    password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')

        # Case‑insensitive user lookup
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise ValidationError('No account with that username exists.')

        # Verify email (case‑insensitive)
        if user.email.lower() != email.lower():
            raise ValidationError('Email does not match the account.')

        # Verify first name (case‑insensitive)
        if user.first_name.lower() != first_name.lower():
            raise ValidationError('First name does not match the account.')

        # Verify last name if provided
        if last_name and user.last_name.lower() != last_name.lower():
            raise ValidationError('Last name does not match the account.')

        if p1 != p2:
            raise ValidationError('Passwords do not match.')

        self.user = user
        return cleaned_data

    def save(self):
        user = self.user
        user.set_password(self.cleaned_data['password1'])
        user.save()
        return user