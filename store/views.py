from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.response import Response
from .document_store import review_store
from .models import Order, Product
from .serializers import OrderSerializer, ProductSerializer, ReviewSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)

        with transaction.atomic():
            locked_product = Product.objects.select_for_update().get(pk=product.pk)
            if locked_product.stock < quantity:
                return Response(
                    {"error": f"Insufficient stock. Available: {locked_product.stock}, requested: {quantity}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            locked_product.stock -= quantity
            locked_product.save(update_fields=["stock"])
            order = serializer.save()

        headers = self.get_success_headers(serializer.data)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED, headers=headers)


class ReviewViewSet(viewsets.ViewSet):
    def list(self, request):
        product_id = request.query_params.get("product_id")
        query = {}
        if product_id is not None:
            try:
                query["product_id"] = int(product_id)
            except ValueError:
                query["product_id"] = product_id
        reviews = review_store.find(query)
        return Response(reviews)

    def create(self, request):
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        result = review_store.insert_one(data)
        doc = review_store.find_one({"_id": result.inserted_id})
        return Response(doc, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        doc = review_store.find_one({"_id": pk})
        if not doc:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(doc)

    def update(self, request, pk=None):
        serializer = ReviewSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        res = review_store.update_one({"_id": pk}, {"$set": serializer.validated_data})
        if res.matched_count == 0:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        doc = review_store.find_one({"_id": pk})
        return Response(doc)

    def partial_update(self, request, pk=None):
        return self.update(request, pk=pk)
