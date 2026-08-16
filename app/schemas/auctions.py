from pydantic import BaseModel
from datetime import datetime

class AuctionCreate(BaseModel):
    title: str
    description: str
    starting_price: float
    start_time: datetime
    end_time: datetime

class AuctionResponse(BaseModel):
    id: int
    title: str
    description: str
    starting_price: float
    start_time: datetime
    end_time: datetime
    status: str
    seller_id: int
    