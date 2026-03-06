from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
import re


class UserManager(BaseUserManager):
    """Custom manager for User model with soft delete support"""
    
    def get_queryset(self):
        """Default queryset excludes soft-deleted users"""
        return super().get_queryset().filter(is_soft_deleted=False)
    
    def all_with_deleted(self):
        """Return all users including soft-deleted ones"""
        return super().get_queryset()
    
    def deleted_only(self):
        """Return only soft-deleted users"""
        return super().get_queryset().filter(is_soft_deleted=True)
    
    def active(self):
        """Return only active users (not soft-deleted)"""
        return self.get_queryset()
    
    def by_role(self, role):
        """Filter users by role"""
        return self.get_queryset().filter(role=role)
    
    def by_department(self, department):
        """Filter users by department"""
        return self.get_queryset().filter(department=department)
    
    # 🔥 IMPORTANT: Add these required methods
    def _create_user(self, username, email, password, **extra_fields):
        """Create and save a user with the given username, email, and password."""
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create a regular user"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPERADMIN')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(username, email, password, **extra_fields)
    
    def get_by_natural_key(self, username):
        """Get user by natural key (username) including soft-deleted for auth"""
        return self.all_with_deleted().get(**{self.model.USERNAME_FIELD: username})


class User(AbstractUser):
    """Custom User model for Employee Management System"""
    
    # Role Choices
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Admin'),
        ('HR', 'Human Resources'),
        ('MANAGER', 'Manager'),
        ('EMPLOYEE', 'Employee'),
    ]
    
    # Status Choices
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('TERMINATED', 'Terminated'),
        ('ON_LEAVE', 'On Leave'),
    ]
    
    # Employee Information
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Employee ID"
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Department"
    )
    
    designation = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Designation"
    )
    
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(
            r'^\+?1?\d{9,15}$',
            'Enter a valid phone number (e.g., +1234567890)'
        )],
        verbose_name="Phone Number"
    )
    
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Annual Salary"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='EMPLOYEE',
        verbose_name="Role"
    )
    
    employment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Employment Status"
    )
    
    date_of_joining = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date of Joining"
    )
    
    is_soft_deleted = models.BooleanField(
        default=False,
        verbose_name="Soft Deleted",
        help_text="Designates whether the user is soft deleted."
    )
    
    # Use custom manager
    objects = UserManager()
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['employee_id']
        indexes = [
            models.Index(fields=['employee_id'], name='idx_employee_id'),
            models.Index(fields=['role'], name='idx_role'),
            models.Index(fields=['department'], name='idx_department'),
            models.Index(fields=['employment_status'], name='idx_status'),
            models.Index(fields=['is_soft_deleted'], name='idx_deleted'),
            models.Index(fields=['last_name', 'first_name'], name='idx_name'),
        ]
    
    def __str__(self):
        """String representation of the user"""
        return f"{self.employee_id} - {self.get_full_name() or self.username}"
    
    def get_full_name(self):
        """Return full name with proper formatting"""
        full_name = super().get_full_name()
        return full_name if full_name else self.username
    
    @property
    def is_superadmin(self):
        """Check if user is superadmin"""
        return self.role == 'SUPERADMIN'
    
    @property
    def is_hr(self):
        """Check if user is HR"""
        return self.role == 'HR'
    
    @property
    def is_manager(self):
        """Check if user is manager"""
        return self.role == 'MANAGER'
    
    @property
    def is_employee(self):
        """Check if user is employee"""
        return self.role == 'EMPLOYEE'
    
    @property
    def is_active_status(self):
        """Check if user has active employment status"""
        return self.employment_status == 'ACTIVE'
    
    # ==================== SOFT DELETE METHODS ====================
    
    def soft_delete(self):
        """Soft delete the user"""
        self.is_soft_deleted = True
        self.save(update_fields=['is_soft_deleted'])
    
    def restore(self):
        """Restore a soft deleted user"""
        self.is_soft_deleted = False
        self.save(update_fields=['is_soft_deleted'])
    
    # ==================== SAVE METHOD WITH AUTO ID GENERATION ====================
    
    def save(self, *args, **kwargs):
        """
        Save method with auto-generated employee_id
        Format: EMP000001, EMP000002, etc.
        """
        if not self.employee_id and not self.is_soft_deleted:
            self.employee_id = self._generate_employee_id()
        
        # Ensure username is lowercase
        if self.username:
            self.username = self.username.lower()
        
        # Ensure email is normalized
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)
        
        super().save(*args, **kwargs)
    
    def _generate_employee_id(self):
        """
        Generate a unique employee ID
        Format: EMP followed by 6-digit number
        """
        # Get the highest existing employee_id number
        max_num = 0
        all_users = User.objects.all_with_deleted()
        
        for user in all_users:
            if user.employee_id:
                # Extract number from EMP000001 format
                numbers = re.findall(r'\d+', user.employee_id)
                if numbers:
                    try:
                        num = int(numbers[0])
                        if num > max_num:
                            max_num = num
                    except (ValueError, IndexError):
                        continue
        
        # Generate next number
        next_num = max_num + 1
        return f"EMP{next_num:06d}"
    
    # ==================== UTILITY METHODS ====================
    
    def get_role_display_name(self):
        """Return display name for role"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def get_status_display_name(self):
        """Return display name for status"""
        return dict(self.STATUS_CHOICES).get(self.employment_status, self.employment_status)
    
    def years_of_service(self):
        """Calculate years of service"""
        if not self.date_of_joining:
            return None
        from django.utils import timezone
        delta = timezone.now().date() - self.date_of_joining
        return delta.days // 365
    
    @classmethod
    def get_department_choices(cls):
        """Get list of unique departments"""
        return cls.objects.exclude(department='').values_list('department', flat=True).distinct()