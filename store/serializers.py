from rest_framework import serializers
from .models import Product, Order


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "sku", "price", "stock"]


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "product", "quantity", "status", "created_at"]
        read_only_fields = ["status", "created_at"]


class ReviewSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    product_id = serializers.IntegerField()
    author = serializers.CharField(max_length=120)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=1000)
