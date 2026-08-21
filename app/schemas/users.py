from pydantic import BaseModel, ConfigDict, Field

from decimal import Decimal

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    account_balance: Decimal

    model_config = ConfigDict(from_attributes=True)

class BalanceUpdate(BaseModel):
    account_balance: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2
        )

class TokenResponse(BaseModel):
    access_token : str
    token_type : str