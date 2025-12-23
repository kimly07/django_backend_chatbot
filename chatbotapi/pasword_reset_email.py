# chatbotapi/utils/password_reset_email.py
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.models import Site

def send_password_reset_email(user_auth, request):
    """
    Send password reset email with secure token link
    user_auth = your Auth model instance
    request = Django request object (to build full URL)
    """
    
    # Get current domain 
    current_site = Site.objects.get_current()
    domain = current_site.domain
    
    # request 
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()

    #reset URL
    reset_url = f"{protocol}://{domain}{reverse('reset-password-confirm', kwargs={'token': user_auth.reset_token})}"

    # Send email
    send_mail(
        subject="Password Reset Request",
        message=f"""
        Hi {user_auth.temp_username or 'there'},

        You requested a password reset for your account.

        Click the link below to set a new password (valid for 15 minutes):

        {reset_url}

        If you didn't request this, please ignore this email.

        Thanks!
        Your App Team
        """.strip(),
        from_email=None, 
        recipient_list=[user_auth.email],
        fail_silently=False,
    )