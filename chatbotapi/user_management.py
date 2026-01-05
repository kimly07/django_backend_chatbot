from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .models import Auth, Chats, User

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.hashers import check_password   # <-- ONLY NEW LINE

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def delete_user(request):
    """Delete user account - Compatible with Flutter"""
    
    if request.method == 'GET':
        return Response({
            "message": "Delete User API is working!",
            "instruction": "Send POST request with user credentials and confirmation",
            "warning": "This action is PERMANENT and cannot be undone!",
            "required_fields": ["email", "password", "confirmation"],
            "example_request": {
                "email": "user@example.com",
                "password": "your_password",
                "confirmation": "yes"
            },
            "note": "This will delete ALL user data including chat history and preferences"
        })
    
    if request.method == 'POST':
        try:
            # Get required fields
            email = request.data.get('email')
            password = request.data.get('password')
            confirmation = request.data.get('confirmation', '').lower().strip()
            
            if not email or not password:
                return Response({
                    "success": False,
                    "error": "Email and password are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if confirmation not in ['yes', 'y', 'true', '1', 'confirm', 'delete']:
                return Response({
                    "success": False,
                    "error": "Confirmation required. Send 'confirmation': 'yes' to proceed.",
                    "warning": "This will permanently delete your account and all data!"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find Auth by email only
            try:
                auth = Auth.objects.get(email=email)
            except Auth.DoesNotExist:
                return Response({
                    "success": False,
                    "error": "Invalid email or password"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Check hashed password (THIS IS THE ONLY CHANGE)
            if not check_password(password, auth.password):
                return Response({
                    "success": False,
                    "error": "Invalid email or password"
                }, status=status.HTTP_401_UNAUTHORIZED)

            # Now get the related User
            try:
                user = User.objects.get(auth=auth)
            except User.DoesNotExist:
                return Response({
                    "success": False,
                    "error": "User profile not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # Store user info before deletion
            deleted_user_info = {
                # "user_id": ,
                "username": user.username,
                "email": auth.email,
                "deleted_at": "Current timestamp"
            }
            # Chats.objects.filter(user_id=user.id).delete() 
             # This deletes all chats for this user safely
            # Delete both User and Auth records
            user.delete()
            auth.delete()
            
            return Response({
                "success": True,
                "message": "Account deleted successfully",
                "deleted_user": deleted_user_info,
                "note": "All your data has been permanently removed from our system"
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": f"Error deleting account: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)