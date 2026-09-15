import json
from sqlalchemy import create_engine, TypeDecorator, Text, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.core.config import settings

# Custom dialect-aware Vector type to support pgvector on PostgreSQL
# while gracefully falling back to JSON for SQLite/offline test environments
class PGVectorType(TypeDecorator):
    """Dialect-aware Vector type.
    Uses pgvector's Vector type on PostgreSQL, and JSON serialization on SQLite/other dialects.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dimension=384, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dimension = dimension

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(self.dimension))
            except ImportError:
                return dialect.type_descriptor(Text)
        return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, (list, tuple)):
            return json.dumps(list(value))
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value

Base = declarative_base()

def get_engine(url=None):
    db_url = url or settings.DATABASE_URL
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(db_url, connect_args=connect_args)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
