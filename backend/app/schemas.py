from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class HoldingCreate(BaseModel):
    ticker: str
    quantity: Decimal
    buy_price: Decimal

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("ticker must not be empty")
        return v

    @field_validator("quantity", "buy_price")
    @classmethod
    def must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("must be positive")
        return v


class HoldingRead(BaseModel):
    id: int
    ticker: str
    quantity: Decimal
    buy_price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
