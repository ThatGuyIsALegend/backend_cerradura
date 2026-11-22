from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Información del proyecto
    APP_NAME: str = "Smart Face Lock"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Base de datos
    DATABASE_URL: str

    # Seguridad
    SECRET_KEY: str
    DEVICE_API_KEY: str

    # Reconocimiento facial
    FACE_MATCH_THRESHOLD: float = 0.45
    MAX_IMAGE_SIZE_BYTES: int = 5 * 1024 * 1024

    # Almacenamiento de fotos de intentos de acceso
    ACCESS_ATTEMPTS_DIR: str = "storage/access_attempts"
    # Tope de seguridad al leer el upload para guardar TODOS los intentos,
    # incluidos los de tipo/tamaño inválidos. Debe ser mayor que
    # MAX_IMAGE_SIZE_BYTES.
    MAX_STORED_IMAGE_SIZE_BYTES: int = 25 * 1024 * 1024

    # Configuración CORS
    CORS_ORIGINS: str = "*"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
