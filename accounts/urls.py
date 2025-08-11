from django.urls import path
from .views import LoginView,LogoutView
from . import views

urlpatterns = [
    path('register/', views.UserRegister.as_view()),
    path('verifyotp/', views.VerifyOTP.as_view()),
    path('login/',LoginView.as_view(),name='login-user'),
    path('logout/',LogoutView.as_view(),name='logout-user'),
    path('delete/',views.DeleteUser.as_view(),name='delete-user'),
]