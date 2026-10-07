from dataclasses import replace

from fastapi.testclient import TestClient

from product_service.api import create_app
from product_service.config import Settings

PRODUCTS = [
    {"id": 1, "name": "Dog Food", "price": 19.99},
    {"id": 2, "name": "Cat Food", "price": 34.99},
    {"id": 3, "name": "Bird Seeds", "price": 10.99},
]


def test_original_api_and_health_without_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with TestClient(create_app(Settings())) as client:
        response = client.get("/products")
        assert response.status_code == 200
        assert response.json() == PRODUCTS
        assert response.headers["content-type"] == "application/json"
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready"}
        assert client.post("/products").status_code == 405
        assert list(tmp_path.iterdir()) == []


def test_independent_instances_have_the_same_catalog():
    with TestClient(create_app(Settings())) as first, TestClient(create_app(Settings())) as second:
        assert first.get("/products").json() == PRODUCTS
        assert second.get("/products").json() == PRODUCTS


def test_default_cors_and_preflight():
    with TestClient(create_app(Settings())) as client:
        response = client.get("/products", headers={"Origin": "https://frontend.example"})
        assert response.headers["access-control-allow-origin"] == "*"
        response = client.options(
            "/products",
            headers={"Origin": "https://frontend.example", "Access-Control-Request-Method": "GET"},
        )
        assert response.status_code == 200


def test_cors_can_be_restricted():
    config = replace(Settings(), cors_origins=("https://allowed.example",))
    with TestClient(create_app(config)) as client:
        allowed = client.get("/products", headers={"Origin": "https://allowed.example"})
        assert allowed.headers["access-control-allow-origin"] == "https://allowed.example"
        blocked = client.get("/products", headers={"Origin": "https://blocked.example"})
        assert "access-control-allow-origin" not in blocked.headers


def test_cors_can_be_disabled():
    with TestClient(create_app(Settings(cors_origins=()))) as client:
        response = client.get("/products", headers={"Origin": "https://frontend.example"})
        assert "access-control-allow-origin" not in response.headers
