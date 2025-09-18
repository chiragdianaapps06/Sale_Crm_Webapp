from django.urls import path,include
from .views import LoginView,LogoutView, SendOTPForgetPassword
from . import views
from rest_framework.routers import DefaultRouter

router=DefaultRouter()

router.register(r'referrer', views.ReferrerViewSet, basename='referrer')

urlpatterns = [
    path('register/',views.UserRegister.as_view(),name='register'),
    path('signup/verifyotp/', views.VerifySignUpOTP.as_view(),name='verify-otp-signup'),
    path('reset-password/verifyotp/', views.VerifyResetPasswordOTP.as_view(),name='verify-otp-reset'),
    path('login/',LoginView.as_view(),name='login-user'),
    path('logout/',LogoutView.as_view(),name='logout-user'),
    path('delete/',views.DeleteUser.as_view(),name='delete-user'),
    path('forgetpassword/',SendOTPForgetPassword.as_view(),name='forget-password'),
    path('reset-password/',views.ResetPassword.as_view(),name='reset-password'),
    path('referrers/<str:id>/',views.ReferrerDetailView.as_view(),name='referrer-detail'),
    path('',include(router.urls)),
]