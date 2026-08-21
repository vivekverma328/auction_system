from sqlalchemy.orm import Session

from app.models.users import User

def create_user(db: Session, user: User):
    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id==user_id).first()

def get_user_by_email(db: Session, user_email: str):
    return db.query(User).filter(User.email==user_email).first()

def update_balance(db: Session, user: User, amount: float):
    user.account_balance += amount

    db.commit()
    db.refresh(user)

    return user

def get_users_by_ids_for_update(
    db: Session,
    user_ids: list[int]
):
    unique_ids = sorted(set(user_ids))

    return (
        db.query(User)
        .filter(User.id.in_(unique_ids))
        .order_by(User.id)
        .with_for_update()
        .all()
    )