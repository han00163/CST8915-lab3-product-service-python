"""Optional PostgreSQL contract test; use a dedicated test database."""

import os

import pytest
from fastapi.testclient import TestClient

from product_service.api import create_app
from product_service.config import Settings
from product_service.database import create_database_engine
from product_service.manage import initialize_database, seed_database


def test_postgres_catalog_contract():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL integration test")
    config = Settings(database_url=database_url)
    engine = create_database_engine(config)
    try:
        initialize_database(engine)
        assert seed_database(engine) in {0, 3}
        assert seed_database(engine) == 0
        with TestClient(create_app(config)) as client:
            response = client.get("/products")
            assert response.status_code == 200
            assert response.json() == [
                {"id": 1, "name": "Dog Food", "price": 19.99},
                {"id": 2, "name": "Cat Food", "price": 34.99},
                {"id": 3, "name": "Bird Seeds", "price": 10.99},
            ]
            assert client.get("/health/ready").status_code == 200
    finally:
        engine.dispose()
