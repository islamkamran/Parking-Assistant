"""Database setup: engine, session factory, declarative Base and the FastAPI session dependency."""
from collections.abc import Generator

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# Predictable constraint names (pk_, fk_, uq_, ix_, ck_).
# Without this, MySQL invents names and Alembic can't reliably drop/alter constraints later.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,    # test a pooled connection before using it (avoids "MySQL server has gone away")
    pool_recycle=3600,     # replace connections older than 1 hour (MySQL closes idle ones)
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """One session per request. Commit happens in the endpoint/service; rollback on any error."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
