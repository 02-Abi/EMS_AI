from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import re


# ============================
# DATE VALIDATION
# ============================

def validate_joining_date(value):
    """
    Ensure the joining date is realistic:
    - Year must be between 1900 and current_year + 10
    - No future dates
    """
    today = timezone.now().date()

    # Year range check (prevents years like 20202020)
    if value.year < 1900 or value.year > today.year + 10:
        raise ValidationError(
            f"Joining year must be between 1900 and {today.year + 10}."
        )

    # No future dates
    if value > today:
        raise ValidationError("Joining date cannot be in the future.")


# ============================
# USER MANAGER
# ============================

class UserManager(BaseUserManager):
    """Custom manager for User model with soft delete support."""

    def get_queryset(self):
        """Default queryset excludes soft‑deleted users."""
        return super().get_queryset().filter(is_soft_deleted=False)

    def all_with_deleted(self):
        """Return all users including soft‑deleted ones."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft‑deleted users."""
        return super().get_queryset().filter(is_soft_deleted=True)

    def by_role(self, role):
        return self.get_queryset().filter(role=role)

    def by_department(self, department):
        return self.get_queryset().filter(department=department)

    # ---------- Required user creation methods ----------
    def _create_user(self, username, email, password, **extra_fields):
        """Create and save a user with the given username, email and password."""
        if not username:
            raise ValueError("Username must be provided")

        email = self.normalize_email(email)
        username = self.model.normalize_username(username)

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)

        # Force validation before saving
        user.full_clean()

        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "SUPERADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)

    def get_by_natural_key(self, username):
        """Required for authentication; includes soft‑deleted users."""
        return self.all_with_deleted().get(**{self.model.USERNAME_FIELD: username})


# ============================
# USER MODEL
# ============================

class User(AbstractUser):
    """Custom User model for Employee Management System."""

    ROLE_CHOICES = [
        ("SUPERADMIN", "Super Admin"),
        ("HR", "Human Resources"),
        ("MANAGER", "Manager"),
        ("EMPLOYEE", "Employee"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
        ("TERMINATED", "Terminated"),
        ("ON_LEAVE", "On Leave"),
    ]

    # ---------- Fields ----------
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
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
        validators=[
            RegexValidator(
                r'^\+?1?\d{9,15}$',
                "Enter a valid phone number (e.g., +1234567890)."
            )
        ],
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
        default="EMPLOYEE",
        verbose_name="Role"
    )

    employment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ACTIVE",
        verbose_name="Employment Status"
    )

    date_of_joining = models.DateField(
        null=True,
        blank=True,
        validators=[validate_joining_date],
        verbose_name="Date of Joining"
    )

    is_soft_deleted = models.BooleanField(
        default=False,
        verbose_name="Soft Deleted",
        help_text="Designates whether the user is soft deleted."
    )

    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        ordering = ["employee_id"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.employee_id} - {self.username}"

    # ---------- Save method ----------
    def save(self, *args, **kwargs):
        # Validate the model before saving
        self.full_clean()

        # Generate employee ID if not already set
        if not self.employee_id:
            self.employee_id = self._generate_employee_id()

        # Normalize username to lowercase
        if self.username:
            self.username = self.username.lower()

        # Normalize email
        if self.email:
            self.email = self.__class__.objects.normalize_email(self.email)

        super().save(*args, **kwargs)

    # ---------- Employee ID Generation (Fixed) ----------
    def _generate_employee_id(self):
        """
        Generate a unique employee ID in the format EMP000001, EMP000002, ...
        Only considers existing IDs that start with 'EMP' followed by digits.
        """
        pattern = re.compile(r'^EMP(\d+)$')
        max_num = 0

        # Iterate over all users (including soft‑deleted) to find the highest EMP number
        for user in User.objects.all_with_deleted():
            if user.employee_id:
                match = pattern.match(user.employee_id)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num

        next_num = max_num + 1
        return f"EMP{next_num:06d}"

    # ---------- Soft Delete Methods ----------
    def soft_delete(self):
        """Mark the user as soft‑deleted."""
        self.is_soft_deleted = True
        self.save(update_fields=["is_soft_deleted"])

    def restore(self):
        """Restore a soft‑deleted user."""
        self.is_soft_deleted = False
        self.save(update_fields=["is_soft_deleted"])

    # ---------- Utility Methods ----------
    def years_of_service(self):
        """Calculate years of service based on date_of_joining."""
        if not self.date_of_joining:
            return None
        today = timezone.now().date()
        return today.year - self.date_of_joining.year

    @classmethod
    def get_department_choices(cls):
        """Return a list of distinct department names (excluding blank)."""
        return (
            cls.objects.exclude(department="")
            .values_list("department", flat=True)
            .distinct()
        )