from sqlalchemy.orm import Session

from app.models.users import User
from app.schemas.users import UserCreate
from app.repositories.users import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    update_balance
    )
from app.core.security import hash_password, verify_password

def register_user(db: Session, user_data: UserCreate):
    user = User(
        name = user_data.name,
        email = user_data.email,
        password_hash = hash_password(user_data.password), 
        account_balance = 0.0
    )

    return create_user(db, user)

def get_user(db: Session, user_id: int):
    return get_user_by_id(db, user_id)

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user

def add_balance(db: Session, user: User, amount: float):
    return update_balance(db, user, amount)