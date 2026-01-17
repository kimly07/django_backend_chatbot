# serializers.py  ← your file, just fixed & upgraded a little

from datetime import timezone
from rest_framework import serializers
from .models import Auth, Chats, Conversation, User
from django.utils import timezone  
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from datetime import timedelta
from django.contrib.auth.hashers import make_password

class AuthSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auth
        fields = ['id', 'email', 'password']  
        extra_kwargs = {'password': {'write_only': True}} 


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'auth']  
        # fields = '__all__'  # use this if you want everything

class ChatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chats
        fields = ['id', 'user_id', 'name', 'is_premium']
        # or fields = '__all__'

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'

        
class SignupSendOTPSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8)

    def validate_email(self, value):
        if Auth.objects.filter(email=value, is_verified=True).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6, min_length=6)  

    def validate(self, data):
        email = data.get('email')
        otp_code = data.get('otp_code')

        try:
            auth = Auth.objects.get(email=email)
            if auth.otp_code != otp_code:
                raise serializers.ValidationError("Invalid OTP code")
            
            if auth.otp_created_at and (timezone.now() - auth.otp_created_at).total_seconds() > 600:
                raise serializers.ValidationError("OTP has expired")
                
        except Auth.DoesNotExist:
            raise serializers.ValidationError("Email not found")

        return data
    
class ResentOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True,min_length = 6)

    def validate(self,data):
        email = data.get('email')
        password = data.get('password')
        try:
            auth =  Auth.objects.get(email__isxact=email)    

            if auth.is_verified == True:
                raise serializers.ValidationError('This email is already verified')
            
            if not check_password(password, auth.password):
                raise serializers.ValidationError('Invalid password.')
            
            if auth.otp_created_at:
                time_since_last = timezone.now() - auth.otp_created_at
                if time_since_last < timedelta(seconds=30):
                    raise serializers.ValidationError("Please wait at least 30 seconds before requesting a new OTP.")

        except Auth.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password.')
        
        data['auth'] = auth
        return data

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            raise serializers.ValidationError("Email and password are required")

        try:
            auth_user = Auth.objects.get(email__iexact=email, is_verified=True)
            
            # FIX: Use check_password instead of direct comparison
            if not check_password(password, auth_user.password):
                raise serializers.ValidationError("Invalid email or password")

            data['user'] = auth_user
            return data

        except Auth.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")
        
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()

    def validate_email(self, value):
        if not Auth.objects.filter(email__iexact=value, is_verified=True).exists():
            raise serializers.ValidationError('No account with that email')
        return value.lower()
    
class VerifyResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if len(new_password) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long"
            )

        if new_password != confirm_password:
            raise serializers.ValidationError(
                "Passwords do not match"
            )

        return data

class AskGPTReqSerializer(serializers.Serializer):
    reset_token = serializers.CharField(max_length=512, min_length=1)
    email = serializers.EmailField(max_length=128, min_length=1)
    prompt = serializers.CharField(max_length=500, min_length=1)
    chat_id = serializers.CharField(min_length=1, required=False)


class GetChatSerializer(serializers.Serializer):
    reset_token = serializers.CharField(max_length=512, min_length=1)
    email = serializers.EmailField(max_length=128, min_length=1)
    
class NewChatSerializer(serializers.Serializer):
    reset_token = serializers.CharField(max_length=512, min_length=1)
    email = serializers.EmailField(max_length=128, min_length=1)
    chat_name = serializers.CharField(max_length=128, min_length=1)


# class changeEmailSendOTPSerializer(serializers.Serializer):
#     new_email = serializers.EmailField()

#     def validate_new_email(self, value):
#         if Auth.objects.filter(email__iexact=value, is_verified=True).exists():
#             raise serializers.ValidationError("This email is already registered.")
#         if Auth.objects.filter(new_email_pending__iexact=value).exists():
#             raise serializers.ValidationError("This email is already pending for change.")
#         return value.lower()
    
# class changeEmailVerifyOTPSerializer(serializers.Serializer):
#     new_email_pending = serializers.EmailField()
#     email_change_otp = serializers.CharField(max_length=6, min_length=6)
    
#     def validate(self, data):
#         new_email_pending = data.get('new_email_pending')
#         email_change_otp = data.get('email_change_otp')

#         try:
#             auth = Auth.objects.get(new_email_pending=new_email_pending)
#             if auth.email_change_otp != email_change_otp:
#                 raise serializers.ValidationError("Invalid OTP code")
            
#             if auth.otp_created_at and (timezone.now() - auth.otp_created_at).total_seconds() > 600:
#                 raise serializers.ValidationError("OTP has expired")
                
#         except Auth.DoesNotExist:
#             raise serializers.ValidationError("Email not found")

#         return data

    