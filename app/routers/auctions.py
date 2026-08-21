from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.schemas.auctions import AuctionCreate, AuctionResponse
from app.schemas.bids import BidResponse
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.users import User
from app.services.auctions import register_auction, get_auction, fetch_all_auctions
from app.services.bids import fetch_auction_bids

from typing import List

router = APIRouter(prefix="/auctions", tags=["Auctions"])


@router.post("/", response_model=AuctionResponse)
def create_auction(
    auction_data: AuctionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return register_auction(db, current_user, auction_data)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.get("/{auction_id}", response_model=AuctionResponse)
def get_auction_by_id(auction_id:int, db: Session = Depends(get_db)):
    auction = get_auction(db, auction_id)

    if not auction:
        raise HTTPException (
            status_code=404,
            detail="Auction not found"
        )

    return auction


@router.get("/", response_model=List[AuctionResponse])
def get_all_auctions(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    offset: int = Query(
        default=0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    return fetch_all_auctions(
        db,
        limit,
        offset
    )

@router.get(
    "/{auction_id}/bids",
    response_model=List[BidResponse]
)
def get_auction_bids(
    auction_id: int,
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    offset: int = Query(
        default=0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    try:
        return fetch_auction_bids(
            db,
            auction_id,
            limit,
            offset
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )