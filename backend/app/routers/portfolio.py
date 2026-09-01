from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.services import portfolio

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary", response_model=schemas.PortfolioSummary)
async def portfolio_summary(db: Session = Depends(get_db)):
    enriched = await portfolio.get_enriched_holdings(db)

    total_cost_basis = sum((e.cost_basis for e in enriched), Decimal("0"))
    total_market_value = sum(
        (e.market_value for e in enriched if e.market_value is not None), Decimal("0")
    )
    total_gain_loss = total_market_value - total_cost_basis
    total_gain_loss_pct = (
        total_gain_loss / total_cost_basis * 100 if total_cost_basis != 0 else None
    )

    holdings_summary = [
        schemas.HoldingSummary(
            id=e.holding.id,
            ticker=e.holding.ticker,
            quantity=e.holding.quantity,
            buy_price=e.holding.buy_price,
            current_price=e.current_price,
            cost_basis=e.cost_basis,
            market_value=e.market_value,
            gain_loss=e.gain_loss,
            gain_loss_pct=e.gain_loss_pct,
            allocation_pct=e.allocation_pct,
        )
        for e in enriched
    ]

    return schemas.PortfolioSummary(
        total_cost_basis=total_cost_basis,
        total_market_value=total_market_value,
        total_gain_loss=total_gain_loss,
        total_gain_loss_pct=total_gain_loss_pct,
        holdings=holdings_summary,
    )
