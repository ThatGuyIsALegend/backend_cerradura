from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


# El proyecto incluye psycopg2-binary; aceptar URLs copiadas con el driver
# psycopg 3 y normalizarlas al driver instalado.
database_url = settings.DATABASE_URL.replace(
    "postgresql+psycopg://", "postgresql+psycopg2://", 1
)

# Crear conexión a PostgreSQL
engine = create_engine(
    database_url,
    pool_pre_ping=True
)


# Administrador de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Clase base para los modelos
Base = declarative_base()


def get_db():
    """
    Proporciona una sesión de base de datos
    a los endpoints de FastAPI.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
