from fastapi import FastAPI

from app.core.logging_config import configure_logging

from app.routers.users import router as user_router
from app.routers.auth import router as auth_router
from app.routers.auctions import router as auction_router
from app.routers.bids import router as bid_router

configure_logging()

app = FastAPI()

app.include_router(user_router)
app.include_router(auth_router) 
app.include_router(auction_router)
app.include_router(bid_router)

@app.get("/")
def home():
    return {"message": "Auction System"}