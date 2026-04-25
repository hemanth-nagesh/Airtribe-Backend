from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.db.models import Count, Q
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from .models import Company, KBEntry, QueryLog
from .permissions import IsAdminUser

User = get_user_model()

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    company_name = request.data.get('company_name')

    if not username or not password or not email:
        return Response({'error': 'Username, password, and email are required'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)

    # Signal creates the Company record and API key on user creation.
    company = user.company
    if company_name:
        company.company_name = company_name
        company.save(update_fields=['company_name'])
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            'username': user.username,
            'api_key': company.api_key,
            'company_name': company.company_name,
            'access': str(refresh.access_token),
        },
        status=201,
    )


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=400)

    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=401)

    company = Company.objects.filter(user=user).first()
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            'message': 'Login successful',
            'access': str(refresh.access_token),
            # 'refresh': str(refresh),
            'company_name': company.company_name if company else None,
            'api_key': company.api_key if company else None,
        }
    )


@api_view(['POST'])
def query_kb(request):
    query = (request.data.get('query') or '').strip()
    if not query:
        return Response({'error': 'Query is required'}, status=400)

    company = request.user.company

    with transaction.atomic():
        entries = KBEntry.objects.filter(
            Q(question__icontains=query) | Q(answer__icontains=query)
        ).order_by('-created_at')
        results = list(
            entries.values('id', 'question', 'answer', 'category', 'created_at')
        )
        QueryLog.objects.create(
            company=company,
            search_team=query,
            result_count=len(results),
        )

    return Response({'count': len(results), 'results': results}, status=200)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def usage_summary(request):
    total_queries = QueryLog.objects.aggregate(total=Count('id'))['total'] or 0
    active_companies = QueryLog.objects.values('company').distinct().count()
    top_search_terms = list(
        QueryLog.objects.values('search_team')
        .annotate(count=Count('search_team'))
        .order_by('-count', 'search_team')
    )

    return Response(
        {
            'total_queries': total_queries,
            'active_companies': active_companies,
            'top_search_terms': top_search_terms,
        },
        status=200,
    )
