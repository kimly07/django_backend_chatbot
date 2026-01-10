from django.core.mail import send_mail
from django.conf import settings
import datetime
from django.utils import timezone

def change_email_send_otp(username, email, otp_code):  
    """Send OTP code to user's email for changing email"""
    subject = "Your OTP Code for Changing Email - ChatBot App"
    message = f"""
    🔐 Hello {username}!

    You have requested to change your email address.

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