from django.urls import path, include
from .views import LeadsViewSet,SalesPersonAllReferrerViewSet,ReferrerAllSalePersonViewSet,ReferrerDashboardViewSet
from rest_framework.routers import DefaultRouter

# viewtask = {
#     'get': 'list',
#     'post':'create'
# }
router = DefaultRouter()

router.register(r"referrer/dashboard", ReferrerDashboardViewSet, basename="referrer-dashboard")
urlpatterns = [
    path('leads/list/',LeadsViewSet.as_view({'get':'list'}),name="list-lead"),
    path('leads/create/',LeadsViewSet.as_view({'post':'create'}),name='create-lead'),
    path('leads/<int:pk>/update/',LeadsViewSet.as_view({'patch':'update'}),name='update-lead'),
    path('leads/<int:pk>/delete/',LeadsViewSet.as_view({'delete':'destroy'}), name='lead-delete'),
    path('leads/sale-person/',SalesPersonAllReferrerViewSet.as_view({'get':'list'}), name='get-saleperson-referrer'),
    path('leads/referrer-person/',ReferrerAllSalePersonViewSet.as_view({'get':'list'}), name='get-referrer-saleperson'),
    path('',include(router.urls)),

]

