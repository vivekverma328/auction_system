from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    account_balance: float

    model_config = ConfigDict(from_attributes=True)

class BalanceUpdate(BaseModel):
    account_balance: float = Field(gt=0)

class TokenResponse(BaseModel):
    access_token : str
    token_type : str