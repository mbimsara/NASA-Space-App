
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


DATABASE_URL = settings.database_url


def create_database_engine(database_url: str):
    # SQLite's thread option is not a valid argument for other DBAPI drivers.
    connect_args = (
        {"check_same_thread": False}
        if make_url(database_url).get_backend_name() == "sqlite"
        else {}
    )
    return create_engine(database_url, connect_args=connect_args)


engine = create_database_engine(DATABASE_URL)

# Create database session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False
)

# Base class for database tables
class Base(DeclarativeBase):
    pass


# Provide a database session to API routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
