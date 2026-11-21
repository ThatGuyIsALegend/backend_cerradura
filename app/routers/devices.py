from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import authenticate_device
from app.database.connection import get_db
from app.schemas.recognition import AccessAttemptResponse
from app.services import access_service, face_service
from app.routers.recognition import read_image

router = APIRouter(prefix="/devices", tags=["Cerradura"])


@router.post("/access-attempt", response_model=AccessAttemptResponse,
             dependencies=[Depends(authenticate_device)])
def access_attempt(image: UploadFile = File(...), db: Session = Depends(get_db)):
    user = None
    similarity = None
    try:
        embedding = face_service.extract_face_embedding(read_image(image))
        user, similarity = face_service.recognize_face(db, embedding)
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
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(log)
    return AccessAttemptResponse(
        authorized=authorized, result=result, reason=reason,
        similarity=similarity, user_id=user.id if authorized else None,
    )
