
from django.urls import path
from . import views
from .user_management import (
    delete_user,
    update_user,
    request_email_change_otp,
    verify_email_change_otp
)
urlpatterns = [
    # -------- SIGNUP --------
    path('signup/send-otp/', views.signup_send_otp),
    path('signup/verify-otp/', views.signup_verify_otp),

    # -------- AUTH --------
    path('login/', views.login, name='login'),
    path('delete-user/', delete_user, name='delete_user'),
    path('refresh-token/', views.refresh_token, name='refresh_token'),

    # -------- PASSWORD RESET (OTP) --------
    path('reset-password/forgot/', views.forgot_password, name='forgot_password_resend/otp'),
    path('password/verify-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('password/reset/confirm/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
    # path('password/reset/<str:token>/', views.reset_password, name='reset_password'),

    path('password/reset/', views.reset_password, name='reset_password'),

    # ask gpt
    path('pota/gpt/chat', views.generate_prompt, name='generate_prompt'),
    path('pota/gpt/me/chat', views.get_chat, name='get_chat'),
    path('pota/gpt/create/chat', views.create_chat, name='create_chat'),
    path('pota/gpt/delete/chat', views.deleteChat, name='delete_chat'),
    
    path('user/update-user/', update_user, name='update_user_profile'),
    path('user/request-email-change-otp/', request_email_change_otp, name='send_otp_change_email'),
    path('user/verify-otp-change-email/', verify_email_change_otp, name='verify_otp_change_email'),
]
