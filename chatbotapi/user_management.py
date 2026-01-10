from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .models import Auth, Chats, User

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import check_password   # <-- ONLY NEW LINE


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
    
# @api_view(['GET', 'POST'])
# @permission_classes([AllowAny])
# def update_user(request):
#     """Update user profile - Compatible with Flutter"""

#     if request.method == 'GET':
#         return Response({
#             "message": "Update User Profile API is working!",
#             "instruction": "Send POST request with user credentials and updated profile data",
#             "required_fields": ["email", "password"],
#             "optional_fields": ["new_username", "new_email", "new_password"],
#             "example_request": {
#                 "email": "kimlyra15@gmail.com",
#                 "password": "12345678",
#                 "new_username": "lylyly01",
#                 "new_email": "new_email@example.com",
#                 "new_password": "new_password"
#             }
#         })

#     # POST
#     email = request.data.get('email')
#     password = request.data.get('password')

#     if not email or not password:
#         return Response({
#             "success": False,
#             "error": "Email and password are required"
#         }, status=status.HTTP_400_BAD_REQUEST)

#     try:
#         auth = Auth.objects.get(email__iexact=email)
#         user = User.objects.get(username=auth.user.username, username=auth.temp_username)

#     except ObjectDoesNotExist:
#         return Response({
#             "success": False,
#             "error": "Invalid email or password"
#         }, status=status.HTTP_401_UNAUTHORIZED)
#     #         "success": False,
#     #         "error": "Invalid email or password"
#     #     }, status=status.HTTP_401_UNAUTHORIZED)

#     # if not check_password(password, auth.password):
#     #     return Response({
#     #         "success": False,
#     #         "error": "Invalid password"
#     #     }, status=status.HTTP_401_UNAUTHORIZED)

#     # Update fields
#     new_username = request.data.get('new_username')
#     new_email = request.data.get('new_email')
#     new_password = request.data.get('new_password')

#     if new_username:
#         user.username = new_username

#     if new_email:
#         auth.email = new_email.lower()

#     if new_password:
#         auth.password = make_password(new_password)

#     user.save()
#     auth.save()

#     return Response({
#         "success": True,
#         "message": "Profile updated successfully",
#         "updated_profile": {
#             "username": user.username,
#             "email": auth.email
#         }
#     }) 

from django.core.exceptions import ObjectDoesNotExist

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def update_user(request):
    """Update user profile - Compatible with Flutter"""

    if request.method == 'GET':
        return Response({
            "message": "Update User Profile API is working!",
            "instruction": "Send POST request with user credentials and updated profile data",
            "required_fields": ["email", "password"],
            "optional_fields": ["new_username", "new_email", "new_password"],
            "example_request": {
                "email": "kimlyra15@gmail.com",
                "password": "12345678",
                "new_username": "lylyly01",
                "new_email": "new_email@example.com",
                "new_password": "new_password"
            }
        })

    # POST - Extract credentials
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({
            "success": False,
            "error": "Email and password are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Authenticate user
    try:
        auth = Auth.objects.get(email__iexact=email)
        print(f"✓ Found Auth - email: {auth.email}, temp_username: {auth.temp_username}")
        
        # Try to find user - if not exists, we'll handle it
        try:
            user = User.objects.get(username=auth.temp_username)
            print(f"✓ Found User - username: {user.username}")
        except User.DoesNotExist:
            print(f"✗ User doesn't exist with username: {auth.temp_username}")
            # Check if there's a ForeignKey relationship
            if hasattr(auth, 'user') and auth.user:
                user = auth.user
                print(f"✓ Found User via ForeignKey - username: {user.username}")
            else:
                return Response({
                    "success": False,
                    "error": "User profile incomplete. Please contact support."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Auth.DoesNotExist:
        print(f"✗ Auth not found for email: {email}")
        return Response({
            "success": False,
            "error": "Invalid email or password"
        }, status=status.HTTP_401_UNAUTHORIZED)

    # Verify password
    if not check_password(password, auth.password):
        print(f"✗ Password check failed")
        return Response({
            "success": False,
            "error": "Invalid email or password"
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    print(f"✓ Password verified")

    # Update fields with validation
    new_username = request.data.get('new_username')
    new_email = request.data.get('new_email')
    new_password = request.data.get('new_password')

    # Validate and update username
    if new_username:
        if User.objects.filter(username=new_username).exclude(id=user.id).exists():
            return Response({
                "success": False,
                "error": "Username already taken"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if Auth.objects.filter(temp_username=new_username).exclude(id=auth.id).exists():
            return Response({
                "success": False,
                "error": "Username already taken"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.username = new_username
        auth.temp_username = new_username

    # Validate and update email
    if new_email:
        new_email_lower = new_email.lower()
        if Auth.objects.filter(email__iexact=new_email_lower).exclude(id=auth.id).exists():
            return Response({
                "success": False,
                "error": "Email already in use"
            }, status=status.HTTP_400_BAD_REQUEST)
        auth.email = new_email_lower

    # Update password
    if new_password:
        if len(new_password) < 8:
            return Response({
                "success": False,
                "error": "Password must be at least 8 characters"
            }, status=status.HTTP_400_BAD_REQUEST)
        auth.password = make_password(new_password)

    # Save changes
    user.save()
    auth.save()

    return Response({
        "success": True,
        "message": "Profile updated successfully",
        "updated_profile": {
            "username": user.username,
            "email": auth.email
        }
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def send_otp_for_email_change(request):
    """Send OTP for email change - Placeholder function"""
    if request.method == 'GET':
        return Response({
            "message": "Send OTP for Email Change API is working!",
            "example_request": {
                "email": "kimlyra55@gmail.com"
            }
        })
    if request.method == 'POST':
        email = request.data.get('email')
        if not email:
            return Response({
                "success": False,
                "error": "Email is required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
    try: 
        auth = Auth.objects.get(email__iexact=email)
        if not auth.is_verified:
            return Response({
                "success": False,
                "error": "Email is not verified"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if auth.new_email_pending:
            return Response({
                "success": False,
                "error": "You have a pending email change request. Please verify the OTP sent to your new email."
            }, status=status.HTTP_400_BAD_REQUEST)
        # if auth.otp_created_at != otp
    except Auth.DoesNotExist:
        return Response({
            "success": False,
            "error": "User with this email does not exist"
        }, status=status.HTTP_404_NOT_FOUND)
        # Placeholder - actual OTP sending logic not implemented
    return Response({
        "success": True,
        "message": "OTP sent to new email (functionality not implemented)"
    })