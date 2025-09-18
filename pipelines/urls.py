from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter


router=DefaultRouter()

router.register(r'status', views.PipelineStatusViewset, basename='status')


urlpatterns = [
    path('create/',views.PipelineCreateView.as_view(),name='create-pipeline'),
    path('',include(router.urls)),
]
