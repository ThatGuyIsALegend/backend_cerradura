from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.security import authenticate_device
from app.database.connection import engine, Base
from app.services.attempt_images import storage_dir

# Importar modelos para que SQLAlchemy los registre
from app.database import models
from app.routers import users, recognition, devices, access_logs

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Inicializar extensión pgvector
    with engine.begin() as connection:
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector")
        )

    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)

    # `create_all` no migra tablas existentes: añadir la columna de la
    # foto si la base ya tenía `access_logs` creada.
    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE access_logs "
                 "ADD COLUMN IF NOT EXISTS image_path VARCHAR(255)")
        )

    # Crear directorio donde se guardan las fotos de los intentos.
    storage_dir()

    print("Base de datos inicializada correctamente")

    yield

    # Cerrar conexiones al apagar
    engine.dispose()


# Crear aplicación
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    # Ningún endpoint es accesible sin la clave del dispositivo.
    dependencies=[Depends(authenticate_device)]
)


# Configuración CORS
origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]



app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)




# Endpoint de prueba
@app.get("/")
def root():

    return {
        "success": True,
        "message": "Smart Face Lock API funcionando",
        "version": settings.APP_VERSION
    }


# Estado del servidor
@app.get("/health")
def health():

    return {
        "status": "online",
        "database": "configured"
    }



app.include_router(users.router, prefix="/api/v1")
app.include_router(recognition.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(access_logs.router, prefix="/api/v1")
