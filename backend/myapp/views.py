import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import HealthProfile
from .services.decision import HealthAgent
from .services.stress import stressService
from .services.recommendation import get_recommendations
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    if request.user.is_authenticated:
        return redirect("/health/")
    return render(request, "index.html")

@login_required
def health(request):
    return render(request, "health.html")

@csrf_exempt
def api_signup(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=400)
    data = json.loads(request.body)
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    dob = data.get("dob")
    age = data.get("age")
    gender = data.get("gender")

    if not name or not email or not password:
        return JsonResponse({"success": False, "error": "Missing required fields"}, status=400)

    if password != confirm_password:
        return JsonResponse({"success": False, "error": "Passwords do not match"}, status=400)

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if User.objects.filter(email=email).exists():
        return JsonResponse({"success": False, "error": "Email already exists"}, status=400)

    user = User.objects.create_user(
        email=email,
        password=password,
        name=name,
        dob=dob if dob else None,
        age=age if age else None,
        gender=gender if gender else None
    )

    login(request, user)

    return JsonResponse({"success": True})

@csrf_exempt
def api_login(request):

    if request.method != "POST":
        return JsonResponse({"success": False})

    data = json.loads(request.body)

    email = data.get("email")
    password = data.get("password")

    try:
        user = User.objects.get(email=email)

        if user.check_password(password):
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Invalid password"})

    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"})

def logout_view(request):
    logout(request)
    return redirect("/")

def check_auth_status(request):
    return JsonResponse({
        "authenticated": request.user.is_authenticated
    })

@login_required
@csrf_exempt
def save_health_profile(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    profile, created = HealthProfile.objects.get_or_create(
        user=request.user
    )

    profile.height_cm = data.get("height")
    profile.weight_kg = data.get("weight")
    profile.sleep_hours = data.get("sleep")

    profile.smoking_status = data.get("smoking")
    profile.alcohol_consumption = data.get("alcohol")
    profile.exercise_frequency = data.get("exercise")
    profile.diet_type = data.get("diet")

    profile.resting_heart_rate = data.get("resting_heart_rate")
    profile.systolic_bp = data.get("systolic_bp")
    profile.diastolic_bp = data.get("diastolic_bp")

    profile.fasting_blood_sugar = data.get("blood_sugar")
    profile.total_cholesterol = data.get("cholesterol")
    profile.vitamin_deficiency = data.get("vitamin_deficiency")

    profile.save()

    return JsonResponse({"status": "saved"})

@login_required
def get_health_profile(request):

    try:
        profile = HealthProfile.objects.get(user=request.user)

        data = {
            "height": profile.height_cm,
            "weight": profile.weight_kg,
            "sleep": profile.sleep_hours,

            "smoking": profile.smoking_status,
            "alcohol": profile.alcohol_consumption,
            "exercise": profile.exercise_frequency,
            "diet": profile.diet_type,

            "resting_heart_rate": profile.resting_heart_rate,
            "systolic_bp": profile.systolic_bp,
            "diastolic_bp": profile.diastolic_bp,

            "blood_sugar": profile.fasting_blood_sugar,
            "cholesterol": profile.total_cholesterol,
            "vitamin_deficiency": profile.vitamin_deficiency,
        }

        return JsonResponse({"profile": data})

    except HealthProfile.DoesNotExist:
        return JsonResponse({"profile": None})

@login_required
@csrf_exempt
def health_decision_agent(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    user_message = data.get("message")

    if not user_message:
        return JsonResponse({"error": "Empty message"}, status=400)

    try:
        profile = HealthProfile.objects.get(user=request.user)

    except HealthProfile.DoesNotExist:

        return JsonResponse({
            "reply": "Please complete your health profile first."
        })

    agent = HealthAgent()

    decision = agent.make_decision(
        user=request.user,
        user_message=user_message
    )

    recommendations = get_recommendations(decision)

    return JsonResponse({

        "agent": "health_decision",

        "decision": decision,

        "recommendations": recommendations

    })

@login_required
@csrf_exempt
def stress_prediction_agent(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    try:

        result = stressService(request.user, data)

        stress_level = result["stress_level"]
        stress_score = result["stress_score"]

        recommendation = get_recommendations(
            f"User stress level is {stress_level}"
        )

        return JsonResponse({

            "agent": "stress_prediction",

            "stress_level": stress_level,
            "stress_score": stress_score,

            "recommendations": recommendation

        })
    except Exception as e:

        return JsonResponse({
            "error": str(e)
        }, status=400)