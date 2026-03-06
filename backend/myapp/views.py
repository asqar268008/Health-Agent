# myapp/views.py
import json
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import User

# Set up logging
logger = logging.getLogger(__name__)

def home(request):
    """Render the home page with user data"""
    if request.user.is_authenticated:
        return redirect("/health/")
    return render(request, "index.html")

@ensure_csrf_cookie
def get_csrf_token(request):
    """Get CSRF token for frontend"""
    return JsonResponse({'detail': 'CSRF cookie set'})

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """
    Handle user login
    """
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    # Validate input
    if not email or not password:
        return JsonResponse({"error": "Email and password are required"}, status=400)

    # Authenticate user
    user = authenticate(request, email=email, password=password)

    if user is not None:
        login(request, user)
        logger.info(f"User logged in successfully: {email}")
        return JsonResponse({
            "success": True,
            "user": {
                "email": user.email,
                "name": user.name
            }
        })

    logger.warning(f"Failed login attempt for email: {email}")
    return JsonResponse({"error": "Invalid email or password"}, status=401)

@csrf_exempt
@require_http_methods(["POST"])
def api_signup(request):
    """
    Handle user registration
    """
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        name = data.get("name", "").strip()
        confirm_password = data.get("confirm_password", "")
        dob = data.get("dob", "")
        age = data.get("age")
        gender = data.get("gender", "")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)

    # Validate required fields
    if not all([email, password, name]):
        return JsonResponse({"error": "Email, password and name are required"}, status=400)

    # Validate email format
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({"error": "Invalid email format"}, status=400)

    # Validate password
    if len(password) < 8:
        return JsonResponse({"error": "Password must be at least 8 characters"}, status=400)
    
    if password != confirm_password:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    # Check cache first for performance
    cache_key = f"user_exists_{email}"
    if cache.get(cache_key):
        return JsonResponse({"error": "Email already exists"}, status=400)
    
    # Check database
    if User.objects.filter(email=email).exists():
        cache.set(cache_key, True, 300)  # Cache for 5 minutes
        return JsonResponse({"error": "Email already exists"}, status=400)

    # Validate age if provided
    if age:
        try:
            age = int(age)
            if age < 0 or age > 150:
                return JsonResponse({"error": "Age must be between 0 and 150"}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid age format"}, status=400)

    try:
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
            dob=dob if dob else None,
            age=age,
            gender=gender if gender else None
        )
        
        logger.info(f"New user created: {email}")
        
        # Clear cache
        cache.delete(cache_key)
        
        return JsonResponse({
            "success": True,
            "message": "Account created successfully",
            "user": {
                "email": user.email,
                "name": user.name
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating user {email}: {str(e)}")
        return JsonResponse({"error": "An error occurred during registration"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """Handle user logout"""
    if request.user.is_authenticated:
        logger.info(f"User logged out: {request.user.email}")
    logout(request)
    return JsonResponse({'success': True, 'message': 'Logged out successfully'})

@require_http_methods(["GET"])
def check_auth_status(request):
    """Check if user is authenticated"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'email': request.user.email,
                'name': request.user.name
            }
        })
    return JsonResponse({'authenticated': False})