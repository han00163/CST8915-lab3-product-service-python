import logging
from dataclasses import replace
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from product_service.api import create_app
from product_service.config import Settings
from product_service.database import Product, create_database_engine
from product_service.manage import initialize_database, seed_database

SAMPLE_PRODUCTS = [
    {"id": 1, "name": "Dog Food", "price": 19.99},
    {"id": 2, "name": "Cat Food", "price": 34.99},
    {"id": 3, "name": "Bird Seeds", "price": 10.99},
]


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite:///{(tmp_path / 'products.db').as_posix()}")


def provision(settings, seed=True):
    engine = create_database_engine(settings)
    try:
        initialize_database(engine)
        if seed:
            seed_database(engine)
    finally:
        engine.dispose()


def test_original_api_and_health(settings):
    provision(settings)
    with TestClient(create_app(settings)) as client:
        response = client.get("/products")
        assert response.status_code == 200
        assert response.json() == SAMPLE_PRODUCTS
        assert response.headers["content-type"] == "application/json"
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready"}
        assert client.post("/products").status_code == 405


def test_products_come_from_attached_database(settings):
    provision(settings)
    engine = create_database_engine(settings)
    try:
        with Session(engine) as session, session.begin():
            product = session.get(Product, 1)
            product.name = "Updated Dog Food"
            product.price = Decimal("20.50")
        with TestClient(create_app(settings)) as client:
            assert client.get("/products").json()[0] == {
                "id": 1,
                "name": "Updated Dog Food",
                "price": 20.5,
            }
    finally:
        engine.dispose()


def test_changing_only_database_url_attaches_different_catalog(settings, tmp_path):
    other = replace(settings, database_url=f"sqlite:///{(tmp_path / 'other.db').as_posix()}")
    provision(settings)
    provision(other, seed=False)
    with TestClient(create_app(settings)) as first, TestClient(create_app(other)) as second:
        assert len(first.get("/products").json()) == 3
        assert second.get("/products").json() == []


def test_missing_schema_is_not_seeded_implicitly(settings, caplog):
    with TestClient(create_app(settings)) as client, caplog.at_level(logging.ERROR):
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
        response = client.get("/products")
        assert response.status_code == 503
        assert response.json() == {"detail": "Product catalog is unavailable"}
        assert settings.database_url not in caplog.text


def test_unavailable_postgres_returns_503_without_credentials(caplog):
    config = Settings(
        database_url="postgresql+psycopg://product:private_password@127.0.0.1:1/products",
        db_connect_timeout=1,
    )
    with TestClient(create_app(config)) as client, caplog.at_level(logging.ERROR):
        assert client.get("/health/live").status_code == 200
        assert client.get("/products").status_code == 503
        assert client.get("/health/ready").status_code == 503
        assert "private_password" not in caplog.text
        assert "private_password" not in repr(config)


def test_admin_tasks_are_repeatable_and_preserve_existing_products(settings):
    engine = create_database_engine(settings)
    try:
        initialize_database(engine)
        initialize_database(engine)
        assert seed_database(engine) == 3
        with Session(engine) as session, session.begin():
            session.get(Product, 1).name = "Existing product"
        assert seed_database(engine) == 0
        with Session(engine) as session:
            rows = session.scalars(select(Product).order_by(Product.id)).all()
            assert len(rows) == 3
            assert rows[0].name == "Existing product"
    finally:
        engine.dispose()


def test_default_cors_and_preflight(settings):
    provision(settings)
    with TestClient(create_app(settings)) as client:
        response = client.get("/products", headers={"Origin": "https://frontend.example"})
        assert response.headers["access-control-allow-origin"] == "*"
        response = client.options(
            "/products",
            headers={"Origin": "https://frontend.example", "Access-Control-Request-Method": "GET"},
        )
        assert response.status_code == 200


def test_cors_can_be_restricted_by_configuration(settings):
    provision(settings)
    with TestClient(create_app(replace(settings, cors_origins=("https://allowed.example",)))) as c:
        allowed = c.get("/products", headers={"Origin": "https://allowed.example"})
        assert allowed.headers["access-control-allow-origin"] == "https://allowed.example"
        blocked = c.get("/products", headers={"Origin": "https://blocked.example"})
        assert "access-control-allow-origin" not in blocked.headers
