"""Run one-off administrative tasks against the configured database."""

import argparse
import json
import sys
from decimal import Decimal
from importlib.resources import files

from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from product_service.config import Settings
from product_service.database import Base, Product, create_database_engine


def initialize_database(engine: Engine) -> None:
    """Create the initial schema if absent; never drop existing data."""
    Base.metadata.create_all(engine)


def seed_database(engine: Engine) -> int:
    """Insert missing sample IDs without changing existing product records."""
    catalog = json.loads(files("product_service").joinpath("sample_products.json").read_text())
    inserted = 0
    with Session(engine) as session, session.begin():
        for item in catalog:
            if session.get(Product, item["id"]) is None:
                session.add(
                    Product(id=item["id"], name=item["name"], price=Decimal(str(item["price"])))
                )
                inserted += 1
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Product service database administration")
    parser.add_argument("command", choices=["init-db", "seed"])
    arguments = parser.parse_args()
    try:
        settings = Settings.from_env()
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    engine = create_database_engine(settings)
    try:
        if arguments.command == "init-db":
            initialize_database(engine)
            print("Database schema initialized")
        else:
            inserted = seed_database(engine)
            print(f"Inserted {inserted} sample products")
    except SQLAlchemyError:
        print("Database task failed; check connectivity, permissions, and schema", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
