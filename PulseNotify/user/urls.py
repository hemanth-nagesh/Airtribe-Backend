from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import register_user, login, PriceAlertViewSet, admin_summary, flight_price

router = DefaultRouter()
router.register(r'alerts', PriceAlertViewSet, basename='price-alert')

urlpatterns = [
    path('auth/register/', register_user, name='register'),
    path('auth/login/', login, name='login'),
    # path('flights/price/<str:route>/', flight_price, name='flight-price'),
    path('admin/summary/', admin_summary, name='admin-summary'),
    path('', include(router.urls)),
]
