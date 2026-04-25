from django.urls import path, include
from . import views
urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('kb/query/', views.query_kb, name='query_kb'),
    path('admin/usage-summary/', views.usage_summary, name='usage_summary'),
]