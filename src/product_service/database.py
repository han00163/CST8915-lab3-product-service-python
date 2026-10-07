"""Database access uses an attached resource specified by DATABASE_URL."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String, create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import StaticPool

from product_service.config import Settings


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (CheckConstraint("price >= 0", name="positive_product_price"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


def create_database_engine(settings: Settings) -> Engine:
    url = make_url(settings.database_url)
    options: dict = {"pool_pre_ping": True, "hide_parameters": True}
    if url.get_backend_name() == "sqlite":
        # SQLite is for isolated tests / local previews, not shared deployments.
        options["connect_args"] = {"check_same_thread": False}
        if url.database in {None, "", ":memory:"}:
            options["poolclass"] = StaticPool
    else:
        options["connect_args"] = {"connect_timeout": settings.db_connect_timeout}
    return create_engine(url, **options)
