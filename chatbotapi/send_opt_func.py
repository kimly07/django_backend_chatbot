from django.core.mail import send_mail
from django.conf import settings
import datetime
from django.utils import timezone


def send_otp_email(username, email, otp_code):  
    """Send OTP code to user's email"""
    subject = "Your OTP Code - ChatBot App"
    message = f"""
    🔐 Welcome to ChatBot App, Mr {username}!

    Your OTP verification code is: 
    
    {otp_code}

    This code will expire in 10 minutes.

    If you didn't request this, please ignore this email.

    Best regards,
    ChatBot Team
    """

    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [email],
        fail_silently=False,
    )


def is_otp_expired(otp_created_at):
    """Check if OTP is expired (10 minutes limit)"""
    if not otp_created_at:
        return True
    
    expiration_time = otp_created_at + datetime.timedelta(minutes=10)
    return timezone.now() > expiration_time