from django.urls import path
from .views import LoginView,LogoutView, ProtectedView


urlpatterns = [
    path('login/',LoginView.as_view(),name='login-user'),
    path('logout/',LogoutView.as_view(),name='logout-user'),
    path('protected/',ProtectedView.as_view(),name='protected-view')
]
