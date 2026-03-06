import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import HealthProfile
from .services.decision import HealthAgent
from .services.recommendation import get_recommendations


# -----------------------------
# HOME PAGE
# -----------------------------
def home(request):
    if request.user.is_authenticated:
        return redirect("/health/")
    return render(request, "index.html")


# -----------------------------
# DASHBOARD PAGE
# -----------------------------
@login_required
def health(request):
    return render(request, "health.html")


# -----------------------------
# SIGNUP API
# -----------------------------
@csrf_exempt
def api_signup(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "Missing fields"}, status=400)

    from django.contrib.auth.models import User

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "User already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password)

    login(request, user)

    return JsonResponse({"status": "created"})


# -----------------------------
# LOGIN API
# -----------------------------
@csrf_exempt
def api_login(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    username = data.get("username")
    password = data.get("password")

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    login(request, user)

    return JsonResponse({"status": "logged_in"})


# -----------------------------
# LOGOUT
# -----------------------------
def logout_view(request):
    logout(request)
    return redirect("/")


# -----------------------------
# AUTH STATUS
# -----------------------------
def check_auth_status(request):
    return JsonResponse({
        "authenticated": request.user.is_authenticated
    })


# -----------------------------
# SAVE HEALTH PROFILE
# -----------------------------
@login_required
@csrf_exempt
def save_health_profile(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    profile, created = HealthProfile.objects.get_or_create(
        user=request.user
    )

    profile.height = data.get("height")
    profile.weight = data.get("weight")
    profile.sleep = data.get("sleep")

    profile.smoking = data.get("smoking")
    profile.alcohol = data.get("alcohol")
    profile.exercise = data.get("exercise")
    profile.diet = data.get("diet")

    profile.resting_heart_rate = data.get("resting_heart_rate")
    profile.systolic_bp = data.get("systolic_bp")
    profile.diastolic_bp = data.get("diastolic_bp")

    profile.blood_sugar = data.get("blood_sugar")
    profile.cholesterol = data.get("cholesterol")
    profile.vitamin_deficiency = data.get("vitamin_deficiency")

    profile.save()

    return JsonResponse({"status": "saved"})


# -----------------------------
# GET HEALTH PROFILE
# -----------------------------
@login_required
def get_health_profile(request):

    try:
        profile = HealthProfile.objects.get(user=request.user)

        data = {
            "height": profile.height,
            "weight": profile.weight,
            "sleep": profile.sleep,

            "smoking": profile.smoking,
            "alcohol": profile.alcohol,
            "exercise": profile.exercise,
            "diet": profile.diet,

            "resting_heart_rate": profile.resting_heart_rate,
            "systolic_bp": profile.systolic_bp,
            "diastolic_bp": profile.diastolic_bp,

            "blood_sugar": profile.blood_sugar,
            "cholesterol": profile.cholesterol,
            "vitamin_deficiency": profile.vitamin_deficiency,
        }

        return JsonResponse({"profile": data})

    except HealthProfile.DoesNotExist:
        return JsonResponse({"profile": None})


# -----------------------------
# AI HEALTH CHAT
# -----------------------------
@login_required
@csrf_exempt
def health_chat(request):

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)
    user_message = data.get("message")

    try:
        profile = HealthProfile.objects.get(user=request.user)
    except HealthProfile.DoesNotExist:
        return JsonResponse({
            "reply": "Please complete your health profile first."
        })

    # Prepare health data
    health_data = {
        "height": profile.height,
        "weight": profile.weight,
        "sleep": profile.sleep,
        "smoking": profile.smoking,
        "alcohol": profile.alcohol,
        "exercise": profile.exercise,
        "diet": profile.diet,
        "resting_heart_rate": profile.resting_heart_rate,
        "systolic_bp": profile.systolic_bp,
        "diastolic_bp": profile.diastolic_bp,
        "blood_sugar": profile.blood_sugar,
        "cholesterol": profile.cholesterol,
        "vitamin_deficiency": profile.vitamin_deficiency
    }

    # Run decision agent
    agent = HealthAgent()
    decision = agent.run(health_data)

    # Generate recommendations
    recommendations = get_recommendations(decision)

    return JsonResponse({
        "reply": recommendations
    })