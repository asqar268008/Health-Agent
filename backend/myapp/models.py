# myapp/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import MinLengthValidator, EmailValidator
import re

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