from django.urls import path,include
from .views import LoginView,LogoutView, SendOTPForgetPassword, VerifyOTP
from . import views
from rest_framework.routers import DefaultRouter

router=DefaultRouter()

router.register(r'referrer', views.ReferrerViewSet, basename='referrer')

urlpatterns = [
    path('register/',views.UserRegister.as_view(),name='register'),
    path('verifyotp/', views.VerifyOTP.as_view(),name='verify-otp'),
    path('login/',LoginView.as_view(),name='login-user'),
    path('logout/',LogoutView.as_view(),name='logout-user'),
    path('delete/',views.DeleteUser.as_view(),name='delete-user'),
    path('forgetpassword/',SendOTPForgetPassword.as_view(),name='forget-password'),
    path('forgetpassword/verifyotp/',VerifyOTP.as_view(),name='verify-otp-forgetpassword'),
    path('referrers/<str:id>/',views.ReferrerDetailView.as_view(),name='referrer-detail'),
    path('',include(router.urls)),
]