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


class HoldingWithValue(HoldingRead):
    current_price: Decimal | None = None
    market_value: Decimal | None = None
    gain_loss: Decimal | None = None
    gain_loss_pct: Decimal | None = None


class HoldingSummary(BaseModel):
    id: int
    ticker: str
    quantity: Decimal
    buy_price: Decimal
    current_price: Decimal | None
    cost_basis: Decimal
    market_value: Decimal | None
    gain_loss: Decimal | None
    gain_loss_pct: Decimal | None
    allocation_pct: Decimal | None


class PortfolioSummary(BaseModel):
    total_cost_basis: Decimal
    total_market_value: Decimal
    total_gain_loss: Decimal
    total_gain_loss_pct: Decimal | None
    holdings: list[HoldingSummary]
