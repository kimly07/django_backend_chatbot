# from django.urls import path
# from . import views

# from .user_management import(
#     delete_user,
# )

# urlpatterns = [
#     path('signup/send-otp/', views.signup_send_otp),
#     path('signup/verify-otp/', views.signup_verify_otp),

#     path('delete-user/', delete_user, name='delete_user'),
#     path('login/', views.login, name='login'),

#     path('forgot-password/', views.forgot_password, name='forgot-password'),
#     path('reset-password/<str:token>/', views.reset_password_confirm, name='reset-password-confirm'),
#     # path('reset-password/', views.reset_password_confirm, name='reset-password-confirm'),
#     path('refresh_token/<str:token>/', views.refresh_token, name='refresh_token'),
# ]

from django.urls import path
from . import views
from .user_management import delete_user

urlpatterns = [
    # -------- SIGNUP --------
    path('signup/send-otp/', views.signup_send_otp),
    path('signup/verify-otp/', views.signup_verify_otp),

    # -------- AUTH --------
    path('login/', views.login, name='login'),
    path('refresh-token/', views.refresh_token, name='refresh_token'),
    path('delete-user/', delete_user, name='delete_user'),

    # -------- PASSWORD RESET (OTP) --------
    path('password/forgot/', views.forgot_password, name='forgot_password'),
    path('password/verify-otp/', views.verify_reset_otp, name='verify_reset_otp'),
    path('password/reset/', views.reset_password, name='reset_password'),
]
