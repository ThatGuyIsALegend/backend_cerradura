import uuid

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    func
)

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pgvector.sqlalchemy import Vector

from app.database.connection import Base


# =====================================
# TABLA: USERS
# =====================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String(150),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=True
    )

    active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relación con embeddings
    embeddings = relationship(
        "FaceEmbedding",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Relación con historial
    access_logs = relationship(
        "AccessLog",
        back_populates="user"
    )


# =====================================
# TABLA: FACE EMBEDDINGS
# =====================================

class FaceEmbedding(Base):

    __tablename__ = "face_embeddings"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    embedding = Column(
        Vector(512),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="embeddings"
    )


# =====================================
# TABLA: ACCESS LOGS
# =====================================

class AccessLog(Base):

    __tablename__ = "access_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    result = Column(
        String(20),
        nullable=False
    )

    reason = Column(
        String(100),
        nullable=True
    )

    similarity = Column(
        Float,
        nullable=True
    )

    image_path = Column(
        String(255),
        nullable=True
    )

    attempted_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="access_logs"
    )

