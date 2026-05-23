from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import get_flight_price, register_user, login, PriceAlertViewSet, admin_summary

router = DefaultRouter()
router.register(r'alerts', PriceAlertViewSet, basename='price-alert')

urlpatterns = [
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login, name='login'),
    path('admin/summary/', admin_summary, name='admin-summary'),
    path('flights/price/', get_flight_price, name='get-flight-price'),
    path('flights/price/<str:route>/', get_flight_price, name='get-flight-price-route'),
    path('', include(router.urls)),
]
