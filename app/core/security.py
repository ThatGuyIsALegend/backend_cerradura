import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


def authenticate_device(x_device_key: str = Header(..., alias="X-Device-Key")):
    """Authenticate the single configured lock using its shared secret."""
    if not hmac.compare_digest(x_device_key, settings.DEVICE_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de la cerradura incorrectas",
        )
