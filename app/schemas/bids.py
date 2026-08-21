from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class BidCreate(BaseModel):
    auction_id : int
    amount: Decimal = Field(
        gt=0,
        max_digits=12,
        decimal_places=2
    )

class BidResponse(BaseModel):
    id: int
    auction_id: int
    bidder_id: int
    amount: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)