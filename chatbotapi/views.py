# chatbotapi/views.py  ← Replace everything in your views.py with this

from datetime import datetime, timedelta
from datetime import datetime, timedelta
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

            # insert new access-token into db

            auth.reset_token = refresh.access_token
            
            auth.save()


            # insert new access-token into db

            auth.reset_token = refresh.access_token
            
            auth.save()

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
    print("data passing in")
    serializer = LoginSerializer(data=request.data)

    print("data validation complete")
    
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
    
    print("Getting user data")
    
    auth_user = serializer.validated_data['user']

    refresh = RefreshToken.for_user(auth_user)
    
    print("new refresh token")

    refresh_token = str(refresh)
    access_token = str(refresh.access_token)

    print("getting user info from db ...")

    auth = Auth.objects.get(email=auth_user.email)

    auth.reset_token = access_token
    auth.reset_token_expires = timezone.now() + timedelta(days=2)

    print("saving data ...")

    print(auth)
            
    auth.save()

    return Response({
        "success": True,
        "message": "Login Success",
        "user": {
            "id": auth_user.id,
            "email": auth_user.email,
            "username": auth.temp_username or auth_user.email.split('@')[0]
        },
        "tokens": {
            "access": access_token,
            "refresh": refresh_token,
            "access": access_token,
            "refresh": refresh_token
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
        print(e)
        print(e)
        return Response({
            "success": False,
            "error": "Invalid request or expired reset token"
        }, status=401)
        
    
    except requests.exceptions.RequestException as e:
        status_code = 500
        print(e)
        print(e)
        if e.response is not None:
            status_code = e.response.status_code
        return Response({
            'success': False,
            'error': str(e)
        }, status=status_code)
        
    except Exception as e:
        print(e)
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def get_chat(request):

    try:
        req_data = GetChatSerializer(data=request.data)

        if not req_data.is_valid():
            return Response({
                "success": False,
                "message": "Invalid request body, please include your email to verify."
            })
        
        valid_data = req_data.validated_data

        reset_token = valid_data.get("reset_token")

        print(reset_token)
        print(valid_data.get("email"))

        target_auth = Auth.objects.get(
            email=valid_data.get("email"),
            reset_token=reset_token,
            reset_token_expires__gt=timezone.now()
        )

        print("TARGET AUTH: ")
        print(target_auth)

        chat_resp_data = []
        for chat in target_auth.chats.all():
            chat_resp_data.append({
                'id': chat.id,
                'name': chat.name,
                'isPremium': chat.is_premium,
                'conversations': [
                    {
                        'id': convo.id,
                        'role': convo.role,
                        'message': convo.message
                    } for convo in chat.conversations.all()
                ]
                })
            
        return Response({
            "success": True,
            "data": chat_resp_data
        })

        
    except Auth.DoesNotExist as e:
        print(e)
        return Response({
            "success": False,
            "error": "Invalid request or expired reset token"
        }, status=401)

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(["POST"])
@permission_classes([AllowAny])
def create_chat(request):

    try:
        req_data = NewChatSerializer(data=request.data)

        if not req_data.is_valid():
            return Response({
                "success": False,
                "message": "Invalid request body, please include your chat-name to verify."
            })
        
        valid_data = req_data.validated_data

        reset_token = valid_data.get("reset_token")

        target_auth = Auth.objects.get(
            email=valid_data.get("email"),
            reset_token=reset_token,
            reset_token_expires__gt=timezone.now()
        )

        # new class 
        new_chat = Chats.objects.create(
            auth=target_auth,
            name=valid_data.get("chat_name")
        )

        return Response({
            "success": True,
            "chat_id": new_chat.id
        })

    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "Invalid request or expired reset token"
        }, status=401)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
    
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def deleteChat(request):
    
    if request.method == 'GET':
        return Response({
            "message": "Delete Chat",
            "endpoint": "/api/delete-chat/",
            "method": "POST",
            "description": "Delete a specific chat and all its conversations by chat_id",
            "request_body": {
                "email": "user@example.com",
                "reset_token": "your_reset_token_here",
                "chat_id": 1
            },
            "response_success": {
                "success": True,
                "message": "Chat deleted successfully",
                "deleted_conversations": 5
            },
            "response_error": {
                "success": False,
                "error": "Error message"
            }
        })
    
    # POST method - actual deletion
    try:
        # Validate request data
        email = request.data.get('email')
        reset_token = request.data.get('reset_token')
        chat_id = request.data.get('chat_id')
        
        if not all([email, reset_token, chat_id]):
            return Response({
                'success': False,
                'error': 'Email, reset_token, and chat_id are required'
            }, status=400)
        
        # Verify user authentication
        target_auth = Auth.objects.get(
            email=email,
            reset_token=reset_token,
            reset_token_expires__gt=timezone.now()
        )

        print("BEFORE GET CHAT ...")
        
        # Get the chat belonging to this user
        chat = Chats.objects.get(
            id=chat_id,
            auth=target_auth
        )

        print(chat)
        
        # Get conversation count before deletion (optional, for response)
        conversation_count = chat.conversations.count()
        
        # Delete the chat (will cascade delete all conversations)
        chat.delete()
        
        return Response({
            'success': True,
            'message': 'Chat deleted successfully',
            'deleted_conversations': conversation_count
        })
        
    except Auth.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid request or expired reset token'
        }, status=401)
        
    except Chats.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Chat not found or does not belong to this user'
        }, status=404)
        
    except Exception as e:
        print(e)
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)