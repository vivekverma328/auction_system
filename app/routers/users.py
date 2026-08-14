from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.users import UserCreate, UserResponse, BalanceUpdate
from app.services.users import register_user, get_user, add_balance
from app.core.dependencies import get_current_user
from app.models.users import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse)
def create_user(                                #same as create_user(taking two parameters)
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    return register_user(db, user_data)

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    user= get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail= "User not found"
        )
    return user

@router.patch("/me/balance", response_model=UserResponse)
def add_user_balance(
    balance_data: BalanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return add_balance(
        db,
        current_user,
        balance_data.account_balance
    )