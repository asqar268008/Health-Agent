# myapp/models.py
from debug_toolbar import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator
import re
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Set default values if not provided
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    # Increased max_length to accommodate any gender values
    email = models.EmailField(
        unique=True, 
        db_index=True,
        validators=[EmailValidator(message="Enter a valid email address")]
    )
    name = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(2, message="Name must be at least 2 characters")]
    )
    dob = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    
    # Increased to 20 to accommodate any gender identity
    gender = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say')
        ]
    )
    
    # Additional fields for better user management
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['name']),
            models.Index(fields=['-date_joined']),
        ]
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name.split()[0] if self.name else self.email
    
    def clean(self):
        # Validate age if provided
        if self.age and (self.age < 0 or self.age > 150):
            raise ValueError('Age must be between 0 and 150')

class HealthProfile(models.Model):
    """
    Minimal health and lifestyle data for a user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="health_profile"
    )
    
    SMOKING_CHOICES = [
        ("no", "No"),
        ("yes", "Yes"),
        ("former", "Former Smoker"),
    ]

    ALCOHOL_CHOICES = [
        ("none", "None"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ]

    EXERCISE_CHOICES = [
        ("none", "None"),
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ]

    DIET_CHOICES = [
        ("vegetarian", "Vegetarian"),
        ("non_vegetarian", "Non-Vegetarian"),
        ("vegan", "Vegan"),
        ("other", "Other"),
    ]

    VITAMIN_DEFICIENCY_OPTIONS = [
        "vitamin_d",
        "vitamin_b12",
        "iron_anemia",
        "vitamin_c",
        "folate_b9",
        "calcium",
        "zinc",
        "magnesium",
    ]

    # ------------------------
    # Basic Body Metrics
    # ------------------------

    height_cm = models.FloatField(blank=True, null=True)
    weight_kg = models.FloatField(blank=True, null=True)
    sleep_hours = models.FloatField(blank=True, null=True)

    # ------------------------
    # Vital Signs
    # ------------------------

    resting_heart_rate = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Beats per minute (BPM)"
    )

    systolic_bp = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Systolic Blood Pressure (mmHg)"
    )

    diastolic_bp = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Diastolic Blood Pressure (mmHg)"
    )

    # ------------------------
    # Lab Values
    # ------------------------

    fasting_blood_sugar = models.FloatField(
        blank=True,
        null=True,
        help_text="Fasting Blood Sugar (mg/dL)"
    )

    total_cholesterol = models.FloatField(
        blank=True,
        null=True,
        help_text="Total Cholesterol (mg/dL)"
    )

    vitamin_deficiency = models.JSONField(
        default=list,
        blank=True,
        help_text="List of vitamin deficiencies"
    )

    # ------------------------
    # Lifestyle
    # ------------------------

    smoking_status = models.CharField(
        max_length=10,
        choices=SMOKING_CHOICES,
        blank=True,
        null=True
    )

    alcohol_consumption = models.CharField(
        max_length=20,
        choices=ALCOHOL_CHOICES,
        blank=True,
        null=True
    )

    exercise_frequency = models.CharField(
        max_length=20,
        choices=EXERCISE_CHOICES,
        blank=True,
        null=True
    )

    diet_type = models.CharField(
        max_length=50,
        choices=DIET_CHOICES,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - HealthProfile"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_health_profile(sender, instance, created, **kwargs):
    if created:
        if hasattr(instance, "is_email_verified"):
            if instance.is_email_verified:
                HealthProfile.objects.get_or_create(user=instance)
        else:
            HealthProfile.objects.get_or_create(user=instance)