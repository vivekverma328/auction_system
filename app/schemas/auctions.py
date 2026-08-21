from pydantic import BaseModel, Field

from datetime import datetime
from decimal import Decimal

class AuctionCreate(BaseModel):
    title: str
    description: str
    starting_price: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )
    start_time: datetime
    end_time: datetime

class AuctionResponse(BaseModel):
    id: int
    title: str
    description: str
    starting_price: Decimal
    start_time: datetime
    end_time: datetime
    status: str
    seller_id: int
    