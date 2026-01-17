# import random
# from django.core.mail import send_mail
# from django.conf import settings
# from django.utils import timezone
# from datetime import timedelta

# from requests import Response

# # Step 1: Request OTP for email change
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def request_email_change_otp(request):
#     """Send OTP to new email address"""
#     if request.method == 'GET':
#         return Response({
#             "message": "Request Email Change OTP API is working!",
#             "instruction": "Send POST request with current email, password, and new_email to receive OTP",
#             "required_fields": ["email", "password", "new_email"],
#             "example_request": {
#                 "email": "",    
#                 "password": "current_password",
#                 "new_email": ""
#             }})
#     email = request.data.get('email')  # Current email
#     password = request.data.get('password')  # Current password
#     new_email = request.data.get('new_email')  # New email to change to
    
#     if not email or not password or not new_email:
#         return Response({
#             "success": False,
#             "error": "Email, password, and new_email are required"
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     # Validate email format
#     if '@' not in new_email or '.' not in new_email:
#         return Response({
#             "success": False,
#             "error": "Invalid email format"
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     # Authenticate user
#     try:
#         auth = Auth.objects.get(email__iexact=email)
#     except Auth.DoesNotExist:
#         return Response({
#             "success": False,
#             "error": "Invalid email or password"
#         }, status=status.HTTP_401_UNAUTHORIZED)
    
#     # Verify password
#     if not check_password(password, auth.password):
#         return Response({
#             "success": False,
#             "error": "Invalid email or password"
#         }, status=status.HTTP_401_UNAUTHORIZED)
    
#     # Check if new email already exists
#     new_email_lower = new_email.lower()
#     if Auth.objects.filter(email__iexact=new_email_lower).exists():
#         return Response({
#             "success": False,
#             "error": "Email already in use"
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     # Generate 6-digit OTP
#     otp = random.randint(100000, 999999)
    
#     # Store OTP in Auth model (you need to add these fields to your model)
#     auth.email_change_otp = str(otp)
#     auth.new_email_pending = new_email_lower
#     auth.otp_created_at = timezone.now()
#     auth.save()
    
#     # Send OTP via email
#     try:
#         send_mail(
#             subject='Email Change Verification Code',
#             message=f'Your verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, please ignore this email.',
#             from_email=settings.EMAIL_HOST_USER,
#             recipient_list=[new_email_lower],
#             fail_silently=False,
#         )
#     except Exception as e:
#         print(f"Email send error: {e}")
#         return Response({
#             "success": False,
#             "error": "Failed to send OTP. Please check the email address."
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#     return Response({
#         "success": True,
#         "message": f"OTP sent to {new_email_lower}. Please check your inbox.",
#         "expires_in": "10 minutes"
#     })


# # Step 2: Verify OTP and update email
# @api_view(['POST'])
# @permission_classes([AllowAny])
# def verify_email_change_otp(request):
#     """Verify OTP and update email"""
    
#     email = request.data.get('email')  # Current email
#     otp = request.data.get('otp')  # OTP code
    
#     if not email or not otp:
#         return Response({
#             "success": False,
#             "error": "Email and OTP are required"
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     # Find user
#     try:
#         auth = Auth.objects.get(email__iexact=email)
#     except Auth.DoesNotExist:
#         return Response({
#             "success": False,
#             "error": "Invalid email"
#         }, status=status.HTTP_401_UNAUTHORIZED)
    
#     # Check if OTP exists
#     if not auth.email_change_otp or not auth.new_email_pending:
#         return Response({
#             "success": False,
#             "error": "No OTP request found. Please request a new OTP."
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     # Check OTP expiration (10 minutes)
#     if auth.otp_created_at:
#         expiration_time = auth.otp_created_at + timedelta(minutes=10)
#         if timezone.now() > expiration_time:
#             # Clear expired OTP
#             auth.email_change_otp = None
#             auth.new_email_pending = None
#             auth.otp_created_at = None
#             auth.save()
            
#             return Response({
#                 "success": False,
#                 "error": "OTP has expired. Please request a new one."
#             }, status=status.HTTP_400_BAD_REQUEST)
    
#     # Verify OTP
#     if str(otp) != auth.email_change_otp:
#         return Response({
#             "success": False,
#             "error": "Invalid OTP"
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     # Update email
#     old_email = auth.email
#     auth.email = auth.new_email_pending
    
#     # Clear OTP data
#     auth.email_change_otp = None
#     auth.new_email_pending = None
#     auth.otp_created_at = None
#     auth.save()
    
#     return Response({
#         "success": True,
#         "message": "Email updated successfully",
#         "old_email": old_email,
#         "new_email": auth.email
#     })


# # Updated update_user function (without email change, only username and password)
# @api_view(['GET', 'POST'])
# @permission_classes([AllowAny])
# def update_user(request):
#     """Update user profile - Username and Password only"""

#     if request.method == 'GET':
#         return Response({
#             "message": "Update User Profile API is working!",
#             "instruction": "Send POST request with user credentials and updated profile data",
#             "required_fields": ["email", "password"],
#             "optional_fields": ["new_username", "new_password"],
#             "note": "To change email, use /request-email-change-otp and /verify-email-change-otp endpoints",
#             "example_request": {
#                 "email": "kimlyra15@gmail.com",
#                 "password": "12345678",
#                 "new_username": "lylyly01",
#                 "new_password": "new_password"
#             }
#         })

#     # POST - Extract credentials
#     email = request.data.get('email')
#     password = request.data.get('password')

#     if not email or not password:
#         return Response({
#             "success": False,
#             "error": "Email and password are required"
#         }, status=status.HTTP_400_BAD_REQUEST)

#     # Authenticate user
#     try:
#         auth = Auth.objects.get(email__iexact=email)
        
#         try:
#             user = User.objects.get(username=auth.temp_username)
#         except User.DoesNotExist:
#             if hasattr(auth, 'user') and auth.user:
#                 user = auth.user
#             else:
#                 return Response({
#                     "success": False,
#                     "error": "User profile incomplete. Please contact support."
#                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
#     except Auth.DoesNotExist:
#         return Response({
#             "success": False,
#             "error": "Invalid email or password"
#         }, status=status.HTTP_401_UNAUTHORIZED)

#     # Verify password
#     if not check_password(password, auth.password):
#         return Response({
#             "success": False,
#             "error": "Invalid email or password"
#         }, status=status.HTTP_401_UNAUTHORIZED)

#     # Update fields
#     new_username = request.data.get('new_username')
#     new_password = request.data.get('new_password')

#     # Validate and update username
#     if new_username:
#         if User.objects.filter(username=new_username).exclude(id=user.id).exists():
#             return Response({
#                 "success": False,
#                 "error": "Username already taken"
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         if Auth.objects.filter(temp_username=new_username).exclude(id=auth.id).exists():
#             return Response({
#                 "success": False,
#                 "error": "Username already taken"
#             }, status=status.HTTP_400_BAD_REQUEST)
        
#         user.username = new_username
#         auth.temp_username = new_username

#     # Update password
#     if new_password:
#         if len(new_password) < 8:
#             return Response({
#                 "success": False,
#                 "error": "Password must be at least 8 characters"
#             }, status=status.HTTP_400_BAD_REQUEST)
#         auth.password = make_password(new_password)

#     # Save changes
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