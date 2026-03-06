from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import traceback
from .services.decision import HealthAgent
from .services.recommendation import get_recommendations
from .models import HealthProfile

def health(request):
    if request.user.is_authenticated:
        context = {
            'user': {
                'name': request.user.name,
                'email': request.user.email
            }
        }
        return render(request, "health.html", context)
    else:
        return redirect('/')


@csrf_exempt
@require_http_methods(["POST"])
def health_chat(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()

        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        health_agent = HealthAgent()

        decision_output = health_agent.make_decision(
            user=request.user,
            user_message=user_message
        )

        recommendations = get_recommendations(decision_output)

        return JsonResponse({
            "decision": decision_output,
            "recommendations": recommendations
        })

    except Exception as e:
        import traceback
        print("\n========== HEALTH ERROR ==========")
        traceback.print_exc()
        print("==================================\n")

        return JsonResponse({
            "error": str(e)   # 🔥 show real error
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def save_health_profile(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    try:
        data = json.loads(request.body)

        profile, created = HealthProfile.objects.get_or_create(user=request.user)

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

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)

def get_health_profile(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    try:
        profile = HealthProfile.objects.filter(user=request.user).first()

        if not profile:
            return JsonResponse({"profile": None})

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
            "fasting_blood_sugar": profile.fasting_blood_sugar,
            "total_cholesterol": profile.total_cholesterol,
            "vitamin_deficiency": profile.vitamin_deficiency
        }

        return JsonResponse({"profile": data})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)