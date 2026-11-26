from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import authenticate_device
from app.database.connection import get_db
from app.schemas.recognition import AccessAttemptResponse
from app.services import access_service, face_service
from app.services.attempt_images import (
    delete_attempt_image,
    read_upload_bytes,
    save_attempt_image,
)

router = APIRouter(
    prefix="/devices",
    tags=["Cerradura"],
    dependencies=[Depends(authenticate_device)]
)

ALLOWED_IMAGE_TYPES = ("image/jpeg", "image/png")


@router.post("/access-attempt", response_model=AccessAttemptResponse)
def access_attempt(image: UploadFile = File(...), db: Session = Depends(get_db)):
    user = None
    similarity = None
    image_content_type: str | None = image.content_type
    image_filename: str | None = image.filename

    # Leer el upload COMPLETO antes de validar: todos los intentos guardan
    # su foto, incluso con tipo/tamaño inválidos o fallos de detección.
    raw_bytes, truncated = read_upload_bytes(
        image, settings.MAX_STORED_IMAGE_SIZE_BYTES)
    if truncated:
        raw_bytes = None

    try:
        if raw_bytes is None:
            raise HTTPException(
                status_code=413,
                detail="La imagen supera el tamaño máximo de almacenamiento",
            )
        if image_content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=415, detail="Formato de imagen no permitido")
        if len(raw_bytes) > settings.MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=413, detail="La imagen supera el tamaño permitido")
        embeddings = face_service.extract_face_embeddings(raw_bytes)
        user, similarity = face_service.recognize_faces(db, embeddings)
        authorized = user is not None and similarity >= settings.FACE_MATCH_THRESHOLD
        if authorized:
            result, reason = "granted", "face_match"
        elif user is None:
            result, reason = "denied", "no_registered_faces"
        else:
            result, reason = "denied", "no_match"
    except ValueError as exc:
        authorized = False
        result, reason = "denied", str(exc)[:100]
    except HTTPException as exc:
        # Bad uploads still represent an authenticated access attempt.
        if exc.status_code not in (413, 415):
            raise
        authorized = False
        result, reason = "denied", str(exc.detail)[:100]

    log = access_service.create_access_log(
        db, result=result, reason=reason,
        user_id=user.id if authorized else None,
        similarity=similarity,
    )
    db.flush()

    # Guardar la foto recibida y asociarla al log, sea el intento válido
    # o no (solo falta si el upload superó el tope de almacenamiento).
    if raw_bytes is not None:
        try:
            log.image_path = save_attempt_image(
                log.id, raw_bytes, image_content_type, image_filename)
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="No se pudo guardar la imagen del intento",
            ) from exc
    saved_path = log.image_path if raw_bytes is not None else None
    try:
        db.commit()
    except Exception:
        db.rollback()
        # Evitar archivos huérfanos si la transacción no se confirma.
        delete_attempt_image(saved_path)
        raise
    db.refresh(log)
    return AccessAttemptResponse(
        authorized=authorized, result=result, reason=reason,
        similarity=similarity, user_id=user.id if authorized else None,
        log_id=log.id, image_path=log.image_path,
    )
