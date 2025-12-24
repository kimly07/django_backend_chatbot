# chatbotapi/views.py  ← Replace everything in your views.py with this

from datetime import timedelta
import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Auth, User
from .send_opt_func import send_otp_email, is_otp_expired
from .serializers import *   
import uuid
from .pasword_reset_email import send_password_reset_email

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def signup_send_otp(request):
    """Send OTP to email for signup verification"""

    if request.method == 'GET':
        return Response({
            'Lbeab sign up': {
                'username': 'Kimly Smos',
                'email': 'kimlyra55@gmail.com',
                'password': 'your password'
            },
            'endpoint': {
                'next_step': 'api/signup/verify-otp/'
            }
        })

    if request.method == 'POST':
        serializer = SignupSendOTPSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": serializer.errors
            }, status=400)
        
        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            # Create or update Auth (save username temporarily)
            auth, created = Auth.objects.get_or_create(
                email=email,
                defaults={
                    'password': make_password(password), 
                    'is_verified': False
                }
            )

            if not created:
                auth.password = make_password(password)
                auth.temp_username = username   
                auth.save()

            # Generate OTP
            import random
            import string
            otp_code = ''.join(random.choices(string.digits, k=6))
            auth.otp_code = otp_code
            auth.otp_created_at = timezone.now()
            auth.temp_username = username   
            auth.save()

            # Send email
            send_otp_email(username=username, email=email, otp_code=otp_code)
            return Response({
                "success": True,
                "message": "OTP sent to your email. Please check your inbox.",
                "email": email,
                "next_step": "Call /api/signup/verify-otp/ with email + OTP"
            })

        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error sending OTP: {str(e)}"
            }, status=500)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def signup_verify_otp(request):

    """Verify OTP and complete registration"""

    if request.method == 'GET':
        return Response({
            'message': 'Signup verify OTP API is working',
            "example": {
                "email": "kimlyra55@gmail.com",
                "otp_code": "123456"
            },
        })

    if request.method == 'POST':
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": serializer.errors
            }, status=400)

        email = serializer.validated_data['email']

        try:
            auth = Auth.objects.get(email=email)

            # Final checks (redundant but safe)
            if auth.otp_code != request.data['otp_code']:
                return Response({'success': False, 'error': 'Invalid OTP code'})
            if is_otp_expired(auth.otp_created_at):
                return Response({'success': False, 'error': 'OTP expired'})

            # Success! Complete registration
            auth.is_verified = True
            auth.otp_code = ""
            auth.save()

            # Create User with saved username
            user = User.objects.create(
                auth=auth,
                username=auth.temp_username or "User"
            )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(auth)
            return Response({
                "success": True,
                "message": "Account created successfully!",
                "user_id": user.id,
                "username": user.username,
                "email": email,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh)
            })

        except Auth.DoesNotExist:
            return Response({'success': False, 'error': 'Email not found'})
        except Exception as e:
            return Response({'success': False, 'error': f'Error: {str(e)}'})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    
    if request.method == 'GET':
        return Response({
            "email": "sokha@gmail.com",
            "password": "123456"
            })
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=400)
    
    auth_user = serializer.validated_data['user']

    refresh = RefreshToken.for_user(auth_user)

    return Response({
        "success": True,
        "message": "Login Success",
        "user": {
            "id": auth_user.id,
            "email": auth_user.email,
            "username": auth_user.temp_username or auth_user.email.split('@')[0]
        },
        "tokens": {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
    })


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Send OTP for password reset"""
    
    # GET - Show API info
    if request.method == 'GET':
        return Response({
            "message": "Send OTP to reset password",
            "body_example": {
                "email": "example@gmail.com"
            }
        })
    
    # POST - Send OTP
    try:
        serializer = ForgetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": serializer.errors
            }, status=400)
        
        email = serializer.validated_data['email']
        
        # Check if user exists
        try:
            auth = Auth.objects.get(email__iexact=email, is_verified=True)
        except Auth.DoesNotExist:
            return Response({
                "success": False,
                "error": "No account found with this email"
            }, status=400)
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        auth.reset_otp = otp
        auth.reset_otp_created_at = timezone.now()
        auth.save()
        
        # Send OTP email
        send_otp_email(username=auth.temp_username or "User", email=email, otp_code=otp)
        
        return Response({
            "success": True,
            "message": "OTP sent to your email"
        })
        
    except Exception as e:
        return Response({
            "success": False,
            "error": f"Server error: {str(e)}"
        }, status=500)
    

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def verify_reset_otp(request):
    if request.method == 'GET':
        return Response({
            "message": "Verify reset password OTP",
            "example": {
                "email": "user@gmail.com",
                "otp": "123456"
            }
        })

    serializer = VerifyResetOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    otp = serializer.validated_data['otp']

    try:
        auth = Auth.objects.get(email__iexact=email)

        if auth.reset_otp != otp:
            return Response({"success": False, "error": "Invalid OTP"}, status=400)

        if timezone.now() - auth.reset_otp_created_at > timedelta(minutes=15):
            return Response({"success": False, "error": "OTP expired"}, status=400)

        auth.reset_otp = None
        auth.reset_otp_created_at = None
        auth.save()

        return Response({
            "success": True,
            "message": "OTP verified successfully"
        })

    except Auth.DoesNotExist:
        return Response({"success": False, "error": "Email not found"}, status=404)
    

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request, token):

    try:
        auth = Auth.objects.get(
            reset_token=token,
            reset_token_expires__gt=timezone.now()
        )
    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "Invalid or expired reset token"
        }, status=400)

    
    if request.method == 'GET':
        return Response({
            "success": True,
            "message": "Valid reset token"
        })

    
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    auth.password = make_password(
        serializer.validated_data['new_password']
    )

    auth.reset_token = None
    auth.reset_token_expires = None
    auth.save()

    return Response({
        "success": True,
        "message": "Password reset successfully"
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def reset_password(request):
    if request.method == 'GET':
        return Response({
            "message": "Reset password",
            "example": {
                "reset_token": "uuid-token-from-verify",
                "new_password": "12345678",
                "confirm_password": "12345678"
            }
        })

    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    reset_token = request.data.get('reset_token')

    if not reset_token:
        return Response({
            "success": False,
            "error": "Reset token required"
        }, status=400)

    try:
        auth = Auth.objects.get(
            reset_token=reset_token,
            reset_token_expires__gt=timezone.now()
        )
    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "Invalid or expired reset token"
        }, status=400)

    auth.password = make_password(serializer.validated_data['new_password'])

    auth.reset_token = None
    auth.reset_token_expires = None
    auth.save()

    return Response({
        "success": True,
        "message": "Password reset successfully"
    })

# views.py - Add refresh endpoint
@api_view(['POST'])
@permission_classes([AllowAny])

def refresh_token(request):
    """Get new access token using refresh token"""
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response({
            'success': False,
            'error': 'Refresh token is required'
        }, status=400)
    
    try:
        refresh = RefreshToken(refresh_token)
        new_access_token = str(refresh.access_token)
        
        return Response({
            'success': True,
            'access': new_access_token
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': 'Invalid refresh token'
        }, status=400)