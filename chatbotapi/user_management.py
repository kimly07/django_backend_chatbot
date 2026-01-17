from datetime import datetime, timedelta
import random
import requests
from django.utils import timezone
import string
from django.conf import settings
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.core.exceptions import ObjectDoesNotExist


from .change_email_sendotp import change_email_send_otp 
from .models import Auth, Chats, User

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import check_password  


from django.contrib.auth.hashers import make_password

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def delete_user(request):
    """Delete user account + chats (DB schema compatible)"""

    if request.method == 'GET':
        return Response({
            "message": "Delete User API is working",
            "required_fields": ["email", "password", "confirmation"],
            "example": {
                "email": "user@gmail.com",
                "password": "123456",
                "confirmation": "yes"
            }
        })

    email = request.data.get('email')
    password = request.data.get('password')
    confirmation = request.data.get('confirmation')

    if not email or not password or confirmation != "yes":
        return Response({
            "success": False,
            "error": "Email, password and confirmation='yes' are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        auth = Auth.objects.get(email__iexact=email)
        user = User.objects.get(auth=auth)

        if not check_password(password, auth.password):
            return Response({
                "success": False,
                "error": "Invalid password"
            }, status=status.HTTP_401_UNAUTHORIZED)

        # ✅ DELETE chats FIRST (correct column: user_id)
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM chatbotapi_user WHERE id = %s"
                # [auth.id]
                , [user.id]
            )

        # ✅ Delete user & auth
        user.delete()
        auth.delete()

        return Response({
            "success": True,
            "message": "User and all related chats deleted successfully"
        })

    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "User not found"
        }, status=status.HTTP_404_NOT_FOUND)    

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def request_email_change_otp(request):
    if request.method == "GET":
        return Response({
            "message": "Request Email Change OTP API",
            "method": "POST",
            "required_fields": ["email", "new_email"],
            "example": {
                "email": "kimlyra55@gmail.com",
                "new_email": "kimlyra15@gmail.com"
            }
        })

    current_email = request.data.get('email')
    new_email     = request.data.get('new_email')

    if not current_email or not new_email:
        return Response({
            "success": False,
            "error": "Both 'email' (current) and 'new_email' are required"
        }, status=400)

    current_email = current_email.lower().strip()
    new_email     = new_email.lower().strip()

    try:
        auth = Auth.objects.get(email__iexact=current_email)
    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "No account found with this email"
        }, status=404)

    if Auth.objects.filter(email__iexact=new_email).exclude(id=auth.id).exists():
        return Response({
            "success": False,
            "error": "This new email is already in use by another account"
        }, status=400)

    if current_email == new_email:
        return Response({
            "success": False,
            "error": "New email is the same as current email"
        }, status=400)

    otp = ''.join(random.choices(string.digits, k=6))

    auth.email_change_otp    = otp
    auth.new_email           = new_email
    auth.new_otp_created_at  = timezone.now()
    auth.save()

    change_email_send_otp(
        username=auth.temp_username or "User",
        email=new_email,
        email_change_otp=otp
    )

    return Response({
        "success": True,
        "message": "OTP sent to the new email address",
        "sent_to": new_email[:3] + "***" + new_email[new_email.find('@'):]
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def verify_email_change_otp(request):
    """Verify OTP and update email"""
    if request.method == 'GET':
        return Response({
            "message": "Verify Email Change OTP API",
            "method": "POST",
            "required_fields": ["email", "email_change_otp"],
            "example": {
                "email": "kimlyra55@gmail.com",
                "email_change_otp": "123456"
            }
        })

    email = request.data.get('email')
    otp   = request.data.get('email_change_otp')

    if not email or not otp:
        return Response({"success": False, "error": "Email and OTP are required"}, status=400)

    try:
        user_auth = Auth.objects.get(email__iexact=email.strip().lower())
    except Auth.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)


    if not user_auth.email_change_otp or not user_auth.new_email:
        return Response({
            "success": False, 
            "error": "No pending request. Please request OTP again."
        }, status=400)

    if str(otp).strip() != str(user_auth.email_change_otp):
        return Response({"success": False, "error": "Invalid OTP"}, status=400)

    user_auth.email = user_auth.new_email 
    user_auth.email_change_otp = None 
    user_auth.new_email = None 
    user_auth.new_otp_created_at = None 
    user_auth.save()

    return Response({
        "success": True, 
        "message": "Email updated successfully",
        "new_email": user_auth.email
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def update_user(request):
    if request.method == 'GET':
        return Response({
            "message": "Update Profile API",
            "required_fields": ["email"], 
            "optional_fields": ["new_username", "new_password"],
            "example_request": {
                "email": "user@example.com",
                "new_username": "vanda_pro",
                "new_password": "newpassword123"
            }
        })

    email_id = request.data.get('email') 
    new_username = request.data.get('new_username')
    new_password = request.data.get('new_password')

    if not email_id:
        return Response({"success": False, "error": "Email is required"}, status=400)

    try:
        auth_obj = Auth.objects.get(email=email_id)
    except Auth.DoesNotExist:
        return Response({"success": False, "error": "User not found"}, status=404)

    if new_username:
        if Auth.objects.filter(temp_username=new_username).exclude(id=auth_obj.id).exists():
            return Response({"success": False, "error": "Username already taken"}, status=400)
        auth_obj.temp_username = new_username

    if new_password:
        if len(new_password) < 7:
            return Response({"success": False, "error": "Password too short"}, status=400)
        auth_obj.password = make_password(new_password)

    auth_obj.save()

    try:
        user_obj = auth_obj.user 
        if new_username:
            user_obj.username = new_username
            user_obj.save()
    except User.DoesNotExist:
        if new_username:
            User.objects.create(auth=auth_obj, username=new_username)

    return Response({
        "success": True, 
        "message": "Profile updated successfully",
        "data": {
            "username": auth_obj.temp_username, 
            "email": auth_obj.email
        }        
    })