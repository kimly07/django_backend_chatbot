# chatbotapi/views.py  ← Replace everything in your views.py with this

from datetime import timedelta
import random
import requests
import string
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import RefreshToken

from chatbotapi.repository.pota_gpt import ask_gpt

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
    if request.method == 'GET':
        return Response({
            "signup": {
                "username": "Kimly Smos",
                "email": "user@gmail.com",
                "password": "your_password"
            },
            "next_step": "/api/signup/verify-otp/"
        })

    serializer = SignupSendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)

    username = serializer.validated_data['username']
    email = serializer.validated_data['email'].lower()
    password = serializer.validated_data['password']

    try:
        auth = Auth.objects.filter(email=email).first()

        # Email already verified
        if auth and auth.is_verified:
            return Response({
                "success": False,
                "error": "Email already registered. Please login."
            }, status=400)

        # Create or reuse unverified user
        if not auth: 
            auth = Auth.objects.create(
                email=email,
                password=make_password(password),
                is_verified=False
            )
        else:
            auth.password = make_password(password)

        # Generate OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        auth.otp_code = otp_code
        auth.otp_created_at = timezone.now()
        auth.temp_username = username
        auth.save()

        send_otp_email(
            username=username,
            email=email,
            otp_code=otp_code
        )

        return Response({
            "success": True,
            "message": "OTP sent to your email",
            "email": email,
            "next_step": "/api/signup/verify-otp/"
        })

    except Exception as e:
        return Response({
            "success": False,
            "error": "Failed to send OTP"
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
                "errors": serializer.errors  
            }, status=400)

        email = serializer.validated_data['email']

        try:
            auth = Auth.objects.get(email=email)

            # Final checks (redundant but safe)
            if auth.otp_code != request.data['otp_code']:
                return Response({
                    'success': False, 
                    'error': 'Invalid OTP code'
                }, status=400)  
                
            if is_otp_expired(auth.otp_created_at):
                return Response({
                    'success': False, 
                    'error': 'OTP expired'
                }, status=400)  

            auth.is_verified = True
            auth.otp_code = ""
            auth.save()

            user = User.objects.create(
                auth=auth,
                username=auth.temp_username or "User"
            )

            refresh = RefreshToken.for_user(auth)
            return Response({
                "success": True,
                "message": "Account created successfully!",
                "user_id": user.id,
                "username": user.username,
                "email": email,
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh)
            }, status=201)  
        
        except Auth.DoesNotExist:
            return Response({
                'success': False, 
                'error': 'Email not found'
            }, status=404) 
            
        except Exception as e:
            print(f"Error in signup_verify_otp: {str(e)}")  
            return Response({
                'success': False, 
                'error': 'Server error occurred'
            }, status=500)  
        
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
            'error': 'Invalid email or Password'
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

        reset_token = str(uuid.uuid4())
        auth.reset_token = reset_token
        auth.reset_token_expires = timezone.now() + timedelta(minutes=30)
        auth.reset_otp = None
        auth.reset_otp_created_at = None
        auth.save()

        return Response({
            "success": True,
            "message": "OTP verified successfully",
            "reset_token": reset_token
        })

    except Auth.DoesNotExist:
        return Response({"success": False, "error": "Email not found"}, status=404)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def reset_password_confirm(request, token):
    """
    Reset password using a valid reset token
    """

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

    # GET → show example
    if request.method == 'GET':
        return Response({
            "success": True,
            "message": "Valid reset token. You can now reset your password.",
            "example_body": {
                "new_password": "12345678",
                "confirm_password": "12345678"
            }
        })

    # POST → reset password
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    auth.password = make_password(serializer.validated_data['new_password'])
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
                "email": "user@gmail.com",
                "new_password": "12345678",
                "confirm_password": "12345678"
            }
        })

    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = request.data.get('email')

    if not email:
        return Response({
            "success": False,
            "error": "Email required"
        }, status=400)

    try:
        auth = Auth.objects.get(email__iexact=email, is_verified=True)
        
        # Reset password
        auth.password = make_password(serializer.validated_data['new_password'])
        auth.save()

        if Auth.password == auth.password:
            return Response({
                "success": False,
                "error": "New password cannot be same as old password."
            }, status=400)

        return Response({
            "success": True,
            "message": "Password reset successfully"
        })
        
    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "Email not found"
        }, status=400)
    
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


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_prompt(request):

    try:
        req_info = AskGPTReqSerializer(data=request.data)

        if(req_info.is_valid(raise_exception=True)):
            
            valid_data = req_info.validated_data

            reset_token = valid_data.get("reset_token")
            
            Auth.objects.get(
                reset_token=reset_token,
                reset_token_expires__gt=timezone.now()
            )
            
            gpt_resp = ask_gpt(
                valid_data.get("email"),
                reset_token=valid_data.get("reset_token"),
                prompt=valid_data.get("prompt"),
                chat_id=valid_data.get("chat_id")
                ); 

            return Response({
                "success": True,
                "message": gpt_resp
            })

    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "Invalid request or expired reset token"
        }, status=400)
    
    except requests.exceptions.RequestException as e:
        status_code = 500
        if e.response is not None:
            status_code = e.response.status_code
        return Response({
            'success': False,
            'error': str(e)
        }, status=status_code)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
