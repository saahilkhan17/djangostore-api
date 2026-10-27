# djangostore-api

Django REST Framework API demonstrating multi-database Django, Docker containerization, and multi-environment settings.

## Features
- **Multi-Environment Settings**: Split settings using `config.settings.dev` and `config.settings.prod`.
- **Multi-Database Support**:
  - Relational Database (Products, Orders): Default SQLite (`db.sqlite3`), overridable via `DATABASE_URL` (PostgreSQL).
  - Document Database (Reviews): MongoDB-compatible `DocumentStore` supporting in-memory storage (default) or MongoDB via `DOCUMENT_STORE_URL`.
- **Stock Management**: Creating an order decrements product stock and returns HTTP 400 when stock is insufficient.
- **Docker Ready**: Includes `Dockerfile` and `docker-compose.yml` (web and postgres).

## Settings & Environment Variables
- `DJANGO_SETTINGS_MODULE`: Set to `config.settings.dev` for development (default) or `config.settings.prod` for production.
- `DATABASE_URL`: Connection string for PostgreSQL (e.g., `postgresql://user:password@localhost:5432/dbname`).
- `DOCUMENT_STORE_URL`: Optional MongoDB connection string for reviews document store.
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames (used in `prod.py`).

## API Endpoints
- `GET /api/products/` - List products
- `POST /api/products/` - Create a product (`name`, `sku`, `price`, `stock`)
- `GET /api/products/{id}/` - Retrieve product details
- `PUT /api/products/{id}/` - Update product
- `DELETE /api/products/{id}/` - Delete product
- `GET /api/orders/` - List orders
- `POST /api/orders/` - Create order (`product`, `quantity`). Decrements stock or returns 400.
- `GET /api/orders/{id}/` - Retrieve order
- `GET /api/reviews/` - List all reviews (supports filtering: `?product_id=<id>`)
- `POST /api/reviews/` - Add a product review (`product_id`, `author`, `rating`, `comment`)
- `GET /api/reviews/{id}/` - Retrieve review
- `PUT /api/reviews/{id}/` - Update review

## Running Tests
Run pytest with the development settings (uses SQLite in-memory/isolated database):
```bash
pytest -q
```
