from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


settings = get_settings()
database_url = settings.database_url


def _resolve_database_url(url: str) -> str:
    """Resolve SQLite paths safely while leaving other databases unchanged."""
    if not url.startswith("sqlite:///"):
        return url

    raw_path = url.removeprefix("sqlite:///")

    # Absolute SQLite paths should be used exactly as configured.
    candidate = Path(raw_path)
    if candidate.is_absolute():
        database_path = candidate.resolve()
    else:
        # Resolve relative SQLite paths from the FarmLink project root,
        # not from the shell's current working directory.
        project_root = Path(__file__).resolve().parents[2]
        database_path = (project_root / candidate).resolve()

    database_path.parent.mkdir(parents=True, exist_ok=True)

    return f"sqlite:///{database_path.as_posix()}"


resolved_database_url = _resolve_database_url(database_url)

connect_args = (
    {"check_same_thread": False}
    if resolved_database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    resolved_database_url,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()