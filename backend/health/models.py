from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


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