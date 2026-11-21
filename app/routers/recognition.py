from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db
from app.schemas.recognition import RecognitionResponse
from app.services import face_service

router = APIRouter(prefix="/recognition", tags=["Reconocimiento"])


def read_image(image: UploadFile) -> bytes:
    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=415, detail="Formato de imagen no permitido")
    content = image.file.read(settings.MAX_IMAGE_SIZE_BYTES + 1)
    if len(content) > settings.MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="La imagen supera el tamaño permitido")
    return content


@router.post("/verify", response_model=RecognitionResponse)
def verify_face(image: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        embedding = face_service.extract_face_embedding(read_image(image))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    user, similarity = face_service.recognize_face(db, embedding)
    matched = user is not None and similarity >= settings.FACE_MATCH_THRESHOLD
    return RecognitionResponse(
        matched=matched,
        user_id=user.id if matched else None,
        user_name=user.name if matched else None,
        similarity=similarity,
    )
