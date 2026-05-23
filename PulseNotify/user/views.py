from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, priceAlert, notification
from .serializers import PriceAlertSerializer
from .permissions import IsAdminUser
import requests
import os


@api_view(['POST'])
@permission_classes([])  # Allow anyone to access the registration endpoint
@authentication_classes([])  # Disable authentication for this view
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response(
            {'error': 'username, email, and password are required.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create the user
    user = User.objects.create_user(username=username, email=email, password=password)
    
    # Profile is automatically created due to signals (user/signals.py)
    profile = user.profile
    
    # Generate token pair based on SimpleJWT
    refresh = RefreshToken.for_user(user)

    return Response({
        'username': user.username,
        'role': profile.role,
        'token': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([])  # Allow anyone to access the registration endpoint
@authentication_classes([])  # Disable authentication for this view
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid username or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    if not user.check_password(password):
        return Response(
            {'error': 'Invalid username or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    # Generate token pair based on SimpleJWT
    refresh = RefreshToken.for_user(user)

    return Response({
        'username': user.username,
        'role': user.profile.role,
        'token': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_200_OK)

# ViewSet for managing Price Alerts

class PriceAlertViewSet(viewsets.ModelViewSet):
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter PriceAlerts to only return alerts belonging to the logged-in user.
        Returns an empty list if the user has no alerts.
        """
        return priceAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Always attach the authenticated user; never allow NULL/other user.
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Prevent user reassignment via PUT/PATCH.
        serializer.save(user=self.request.user)
    
    def destroy(self, request, pk=None):
        """
        Sets the alert status to INACTIVE instead of deleting the database row.
        Returns 404 if the alert does not exist or belongs to another user.
        """
        alert = get_object_or_404(priceAlert, id=pk)
        
        # Check if alert belongs to the current user
        if alert.user != request.user:
            return Response(
                {'error': 'Not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Set status to INACTIVE instead of deleting
        alert.status = priceAlert.Status.INACTIVE
        alert.save(update_fields=['status'])
        
        return Response(
            {'status': 'inactive'}, 
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_summary(request):
    """
    Returns platform-wide statistics about alerts and notifications.
    Only accessible to users with role = ADMIN.
    """
    # Get total_alerts, active_alerts, triggered_alerts counts
    alerts_stats = priceAlert.objects.aggregate(
        total_alerts=Count('id'),
        active_alerts=Count('id', filter=Q(status='active')),
        triggered_alerts=Count('id', filter=Q(status='triggered'))
    )
    
    # Get total_notifications count
    total_notifications = notification.objects.aggregate(
        count=Count('id')
    )['count'] or 0
    
    # Get top routes by alert count
    top_routes = list(
        priceAlert.objects
        .values('orign', 'destination')
        .annotate(alert_count=Count('id'))
        .order_by('-alert_count')[:10]
    )
    
    # Format top_routes response
    formatted_routes = [
        {
            'route': f"{item['orign']}-{item['destination']}",
            'alert_count': item['alert_count']
        }
        for item in top_routes
    ]
    
    return Response({
        'total_alerts': alerts_stats['total_alerts'],
        'active_alerts': alerts_stats['active_alerts'],
        'triggered_alerts': alerts_stats['triggered_alerts'],
        'total_notifications': total_notifications,
        'top_routes': formatted_routes
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([])
def get_flight_price(request, route=None):
    # Support both:
    # - /api/flights/price/?route=DEL-BOM
    # - /api/flights/price/DEL-BOM/
    route = route or request.query_params.get('route')
    if not route:
        return Response({'error': 'route is required'}, status=status.HTTP_400_BAD_REQUEST)

    price_server_url = os.environ.get(
        'FLIGHT_PRICE_SERVER_URL',
        'http://127.0.0.1:8080/api/flights/price/',
    )

    try:
        resp = requests.get(
            price_server_url,
            params={'route': route},
            timeout=10,
        )
    except requests.RequestException:
        return Response(
            {'error': 'Price server unavailable'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    try:
        data = resp.json()
    except Exception:
        data = {'error': 'Invalid response from price server'}

    return Response(data, status=resp.status_code)

