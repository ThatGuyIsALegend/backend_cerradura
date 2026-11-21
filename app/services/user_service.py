from sqlalchemy.orm import Session

from app.database.models import User


def create_user(
    db: Session,
    name: str,
    email: str | None = None
):

    user = User(
        name=name,
        email=email
    )

    db.add(user)
    db.flush()

    return user


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 50
):

    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_by_id(
    db: Session,
    user_id
):

    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )


def update_user(
    db: Session,
    user: User,
    data: dict
):

    for field, value in data.items():

        setattr(user, field, value)

    db.flush()

    return user


def delete_user(
    db: Session,
    user: User
):

    db.delete(user)
    db.flush()

    return True