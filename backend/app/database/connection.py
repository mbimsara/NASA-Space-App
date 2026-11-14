
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQLite database stored in the backend directory
DATABASE_URL = "sqlite:///./agrosphere.db"

# Create database connection engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

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
