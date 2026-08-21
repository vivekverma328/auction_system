from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.users import User
from app.schemas.bids import BidCreate, BidResponse
from app.services.bids import register_bid


router = APIRouter(
    prefix="/bids",
    tags=["Bids"]
)


@router.post("/", response_model=BidResponse)
def place_bid(
    bid_data: BidCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return register_bid(
            db,
            current_user.id,
            bid_data
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )