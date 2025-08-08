from django.urls import path,include
from . import views




urlpatterns = [
    path('register/', views.UserRegister.as_view()),
    path('verifyotp/', views.VerifyOTP.as_view()),
]
