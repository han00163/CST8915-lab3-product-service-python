"""HTTP API preserving the original GET /products contract."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from product_service.config import Settings
from product_service.database import Product, create_database_engine

logger = logging.getLogger("uvicorn.error")


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = create_database_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Database provisioning is a release task, not a startup side effect.
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="Product Service Python", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_credentials=False,
    )

    @app.get("/products", response_model=list[ProductResponse])
    def products() -> list[ProductResponse]:
        try:
            with Session(engine) as session:
                rows = session.scalars(select(Product).order_by(Product.id)).all()
                return [ProductResponse.model_validate(row) for row in rows]
        except SQLAlchemyError:
            # Connection failure exceptions can contain credentials.
            logger.error("Product catalog database is unavailable")
            raise HTTPException(status_code=503, detail="Product catalog is unavailable") from None

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready() -> dict[str, str]:
        try:
            with engine.connect() as connection:
                # Check connectivity and schema, including for an empty catalog.
                connection.execute(select(Product.id).limit(1))
        except SQLAlchemyError:
            raise HTTPException(status_code=503, detail="Database is not ready") from None
        return {"status": "ready"}

    return app
