"""HTTP API retaining the original fixed, in-code product data."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from product_service.config import Settings


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float = Field(ge=0)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title="Product Service Python", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_credentials=False,
    )

    @app.get("/products", response_model=list[ProductResponse])
    def products() -> list[dict[str, object]]:
        return [
            {"id": 1, "name": "Dog Food", "price": 19.99},
            {"id": 2, "name": "Cat Food", "price": 34.99},
            {"id": 3, "name": "Bird Seeds", "price": 10.99},
        ]

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready"}

    return app
