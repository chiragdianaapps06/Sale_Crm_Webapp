from django.urls import path
from .views import LoginView,LogoutView, SendOTPForgetPassword, VerifyOTP
from . import views

urlpatterns = [
    path('register/',views.UserRegister.as_view(),name='register'),
    path('verifyotp/', views.VerifyOTP.as_view(),name='verify-otp'),
    path('login/',LoginView.as_view(),name='login-user'),
    path('logout/',LogoutView.as_view(),name='logout-user'),
    path('delete/',views.DeleteUser.as_view(),name='delete-user'),
    path('forgetpassword/',SendOTPForgetPassword.as_view(),name='forget-password'),
    path('forgetpassword/verifyotp/',VerifyOTP.as_view(),name='verify-otp-forgetpassword'),
]