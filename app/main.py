from fastapi import FastAPI

from app.database import engine

from app.models.base import Base
from app.models.users import User
from app.routers.users import router as user_router
from app.routers.auth import router as auth_router
from app.routers.auctions import router as auction_router

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(auction_router)

@app.get("/")
def home():
    return {"message": "Auction System"}