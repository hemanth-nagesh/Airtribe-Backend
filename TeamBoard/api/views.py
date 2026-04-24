from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Company, KBEntry, QueryLog

@api_view(['POST'])
def register_company(request):
    company_name = request.data.get('company_name')
    if not company_name:
        return Response({'error': 'Company name is required'}, status=400)
    
    company = Company.objects.create(company_name=company_name)
    return Response({'message': 'Company registered successfully', 'api_key': company.api_key}, status=201)
