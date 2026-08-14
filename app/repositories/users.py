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