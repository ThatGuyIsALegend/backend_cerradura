from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.access_log import AccessLogResponse
from app.services import access_service

router = APIRouter(prefix="/access-logs", tags=["Historial"])


@router.get("", response_model=list[AccessLogResponse])
def list_access_logs(skip: int = 0, limit: int = 50,
                     db: Session = Depends(get_db)):
    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Parámetros de paginación inválidos")
    return access_service.get_access_logs(db, skip=skip, limit=limit)


@router.get("/{log_id}", response_model=AccessLogResponse)
def get_access_log(log_id: UUID, db: Session = Depends(get_db)):
    log = access_service.get_access_log(db, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Intento no encontrado")
    return log
