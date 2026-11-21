from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.connection import get_db

from app.schemas.user import (
    UserResponse,
    UserUpdate,
    FaceEmbeddingResponse,
)

from app.services import user_service
from app.services import face_service


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


# =====================================
# POST /users
# Registrar persona y rostro
# =====================================

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    name: str = Form(...),
    email: str | None = Form(default=None),
    consent: bool = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not consent:
        raise HTTPException(
            status_code=403,
            detail="Se requiere consentimiento"
        )

    if image.content_type not in (
        "image/jpeg",
        "image/png"
    ):
        raise HTTPException(
            status_code=415,
            detail="Formato de imagen no permitido"
        )

    image_bytes = image.file.read(5 * 1024 * 1024 + 1)

    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="La imagen supera los 5 MB"
        )

    try:

        # Extraer embedding facial
        embedding = face_service.extract_face_embedding(
            image_bytes
        )

        # Crear persona
        user = user_service.create_user(
            db=db,
            name=name.strip(),
            email=email.strip().lower() if email and email.strip() else None
        )

        # Guardar embedding
        face_service.save_face_embedding(
            db=db,
            user_id=user.id,
            embedding=embedding
        )

        # Confirmar transacción
        db.commit()
        db.refresh(user)

        return user

    except ValueError as e:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="El correo ya está registrado"
        )

    except Exception:

        db.rollback()
        raise


# =====================================
# POST /users/{id}/faces
# Agregar otra imagen facial
# =====================================

@router.post(
    "/{user_id}/faces",
    response_model=FaceEmbeddingResponse,
    status_code=status.HTTP_201_CREATED
)
def add_user_face(
    user_id: UUID,
    consent: bool = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not consent:
        raise HTTPException(
            status_code=403,
            detail="Se requiere consentimiento"
        )

    user = user_service.get_user_by_id(db=db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada"
        )

    if image.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=415,
            detail="Formato de imagen no permitido"
        )

    image_bytes = image.file.read(5 * 1024 * 1024 + 1)
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="La imagen supera los 5 MB"
        )

    try:
        embedding = face_service.extract_face_embedding(image_bytes)
        face = face_service.save_face_embedding(
            db=db,
            user_id=user.id,
            embedding=embedding
        )
        db.commit()
        db.refresh(face)
        return face
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        db.rollback()
        raise


# =====================================
# GET /users
# Listar personas
# =====================================

@router.get(
    "",
    response_model=list[UserResponse]
)
def get_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):

    if skip < 0 or limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Parámetros de paginación inválidos"
        )

    return user_service.get_users(
        db=db,
        skip=skip,
        limit=limit
    )


# =====================================
# GET /users/{id}
# Consultar persona
# =====================================

@router.get(
    "/{user_id}",
    response_model=UserResponse
)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):

    user = user_service.get_user_by_id(
        db=db,
        user_id=user_id
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada"
        )

    return user


# =====================================
# PUT /users/{id}
# Actualizar información
# =====================================

@router.put(
    "/{user_id}",
    response_model=UserResponse
)
def update_user(
    user_id: UUID,
    data: UserUpdate,
    db: Session = Depends(get_db)
):

    user = user_service.get_user_by_id(
        db=db,
        user_id=user_id
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada"
        )

    changes = data.model_dump(
        exclude_unset=True
    )

    if not changes:
        raise HTTPException(
            status_code=400,
            detail="No se proporcionaron cambios"
        )

    if "name" in changes:
        if changes["name"] is not None:
            changes["name"] = changes["name"].strip()

    if "email" in changes and changes["email"] is not None:
        changes["email"] = changes["email"].strip().lower() or None

    if "name" in changes and not changes["name"]:
        raise HTTPException(
            status_code=400,
            detail="El nombre no puede estar vacío"
        )

    try:

        user = user_service.update_user(
            db=db,
            user=user,
            data=changes
        )

        db.commit()
        db.refresh(user)

        return user

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="El correo ya está registrado"
        )


# =====================================
# DELETE /users/{id}
# Eliminar persona y embeddings
# =====================================

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):

    user = user_service.get_user_by_id(
        db=db,
        user_id=user_id
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Persona no encontrada"
        )

    try:

        user_service.delete_user(
            db=db,
            user=user
        )

        db.commit()

        return None

    except Exception:

        db.rollback()
        raise
