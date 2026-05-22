from rest_framework import serializers
from .models import priceAlert


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = priceAlert
        fields = ['id', 'orign', 'destination', 'treshold_price', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']
