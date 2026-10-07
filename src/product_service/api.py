"""Read-only HTTP catalog retaining the original GET /products response."""

import json
from importlib.resources import files

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
    # The original fixed catalog is application data bundled with each release.
    catalog = [
        ProductResponse.model_validate(item)
        for item in json.loads(files("product_service").joinpath("products.json").read_text())
    ]
    app = FastAPI(title="Product Service Python", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_credentials=False,
    )

    @app.get("/products", response_model=list[ProductResponse])
    def products() -> list[ProductResponse]:
        return catalog

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        return {"status": "ready"}

    return app
