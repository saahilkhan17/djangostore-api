import pytest
from rest_framework.test import APIClient
from store.models import Product, Order
from store.document_store import review_store


@pytest.fixture(autouse=True)
def clean_document_store():
    review_store.clear()
    yield
    review_store.clear()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_product(db):
    return Product.objects.create(name="Widget", sku="WDG-001", price="19.99", stock=10)


@pytest.mark.django_db
def test_create_product(api_client):
    payload = {"name": "Gadget", "sku": "GDG-001", "price": "29.99", "stock": 15}
    response = api_client.post("/api/products/", payload, format="json")
    assert response.status_code == 201
    assert response.data["name"] == "Gadget"
    assert response.data["sku"] == "GDG-001"
    assert Product.objects.filter(sku="GDG-001").exists()


@pytest.mark.django_db
def test_list_products(api_client, sample_product):
    response = api_client.get("/api/products/")
    assert response.status_code == 200
    assert len(response.data) >= 1
    skus = [p["sku"] for p in response.data]
    assert sample_product.sku in skus


@pytest.mark.django_db
def test_retrieve_product(api_client, sample_product):
    response = api_client.get(f"/api/products/{sample_product.id}/")
    assert response.status_code == 200
    assert response.data["id"] == sample_product.id
    assert response.data["sku"] == sample_product.sku


@pytest.mark.django_db
def test_update_product(api_client, sample_product):
    payload = {"name": "Widget Deluxe", "sku": sample_product.sku, "price": "24.50", "stock": 8}
    response = api_client.put(f"/api/products/{sample_product.id}/", payload, format="json")
    assert response.status_code == 200
    sample_product.refresh_from_db()
    assert sample_product.name == "Widget Deluxe"
    assert str(sample_product.price) == "24.50"
    assert sample_product.stock == 8


@pytest.mark.django_db
def test_delete_product(api_client, sample_product):
    response = api_client.delete(f"/api/products/{sample_product.id}/")
    assert response.status_code == 204
    assert not Product.objects.filter(id=sample_product.id).exists()


@pytest.mark.django_db
def test_create_order_decrements_stock(api_client, sample_product):
    initial_stock = sample_product.stock
    order_qty = 3
    payload = {"product": sample_product.id, "quantity": order_qty}
    response = api_client.post("/api/orders/", payload, format="json")
    assert response.status_code == 201
    assert response.data["quantity"] == order_qty
    assert response.data["status"] == "pending"

    sample_product.refresh_from_db()
    assert sample_product.stock == initial_stock - order_qty
    assert Order.objects.filter(product=sample_product, quantity=order_qty).exists()


@pytest.mark.django_db
def test_create_order_insufficient_stock_fails(api_client, sample_product):
    sample_product.stock = 2
    sample_product.save(update_fields=["stock"])

    payload = {"product": sample_product.id, "quantity": 5}
    response = api_client.post("/api/orders/", payload, format="json")
    assert response.status_code == 400
    assert "Insufficient stock" in response.data.get("error", "")

    sample_product.refresh_from_db()
    assert sample_product.stock == 2
    assert Order.objects.count() == 0


def test_reviews_round_trip(api_client):
    payload = {
        "product_id": 99,
        "author": "Alice",
        "rating": 5,
        "comment": "Outstanding build quality!",
    }
    create_resp = api_client.post("/api/reviews/", payload, format="json")
    assert create_resp.status_code == 201
    review_id = create_resp.data["id"]
    assert review_id is not None
    assert create_resp.data["author"] == "Alice"
    assert create_resp.data["rating"] == 5

    get_resp = api_client.get(f"/api/reviews/{review_id}/")
    assert get_resp.status_code == 200
    assert get_resp.data["id"] == review_id
    assert get_resp.data["comment"] == "Outstanding build quality!"


def test_filter_reviews_by_product(api_client):
    api_client.post("/api/reviews/", {"product_id": 1, "author": "Bob", "rating": 4, "comment": "Good"}, format="json")
    api_client.post("/api/reviews/", {"product_id": 2, "author": "Charlie", "rating": 3, "comment": "Okay"}, format="json")

    resp1 = api_client.get("/api/reviews/?product_id=1")
    assert resp1.status_code == 200
    assert len(resp1.data) == 1
    assert resp1.data[0]["author"] == "Bob"

    resp2 = api_client.get("/api/reviews/?product_id=2")
    assert resp2.status_code == 200
    assert len(resp2.data) == 1
    assert resp2.data[0]["author"] == "Charlie"


def test_update_review(api_client):
    create_resp = api_client.post(
        "/api/reviews/",
        {"product_id": 5, "author": "Dave", "rating": 2, "comment": "Bad battery"},
        format="json",
    )
    review_id = create_resp.data["id"]

    update_resp = api_client.put(
        f"/api/reviews/{review_id}/",
        {"product_id": 5, "author": "Dave", "rating": 4, "comment": "Fixed after update"},
        format="json",
    )
    assert update_resp.status_code == 200
    assert update_resp.data["rating"] == 4
    assert update_resp.data["comment"] == "Fixed after update"
