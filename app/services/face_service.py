import numpy as np

from sqlalchemy.orm import Session

from app.database.models import FaceEmbedding, User
from app.services.face_engine import face_engine


def extract_face_embedding(image_bytes: bytes):

    """
    Extrae el embedding de una fotografía.
    """

    return face_engine.extract_embedding(image_bytes)


def save_face_embedding(
    db: Session,
    user_id,
    embedding
):

    """
    Guarda el embedding asociado a una persona.
    """

    face = FaceEmbedding(
        user_id=user_id,
        embedding=np.asarray(
            embedding,
            dtype=np.float32
        ).tolist()
    )

    db.add(face)

    db.flush()

    return face


def delete_user_embeddings(
    db: Session,
    user_id
):

    """
    Elimina los embeddings asociados a una persona.
    """

    db.query(FaceEmbedding).filter(
        FaceEmbedding.user_id == user_id
    ).delete(
        synchronize_session=False
    )


def recognize_face(db: Session, embedding):
    """Compare normalized face vectors and return the best active user."""
    candidate = np.asarray(embedding, dtype=np.float32)
    best_user = None
    best_similarity = -1.0

    rows = (db.query(FaceEmbedding, User)
            .join(User, FaceEmbedding.user_id == User.id)
            .filter(User.active.is_(True)).all())
    for face, user in rows:
        stored = np.asarray(face.embedding, dtype=np.float32)
        similarity = float(np.dot(candidate, stored) /
                           (np.linalg.norm(candidate) * np.linalg.norm(stored)))
        if similarity > best_similarity:
            best_user, best_similarity = user, similarity

    return best_user, (best_similarity if best_user is not None else None)
