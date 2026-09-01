from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app import models
from app.services import finnhub


@dataclass
class EnrichedHolding:
    holding: models.Holding
    current_price: Decimal | None
    cost_basis: Decimal
    market_value: Decimal | None
    gain_loss: Decimal | None
    gain_loss_pct: Decimal | None
    allocation_pct: Decimal | None


async def get_enriched_holdings(db: Session) -> list[EnrichedHolding]:
    holdings = db.query(models.Holding).order_by(models.Holding.created_at).all()
    tickers = list({h.ticker for h in holdings})
    quotes = await finnhub.get_quotes(tickers)

    partial = []
    for h in holdings:
        quote = quotes.get(h.ticker)
        current_price = Decimal(str(quote["c"])) if quote else None
        cost_basis = h.quantity * h.buy_price
        market_value = h.quantity * current_price if current_price is not None else None
        gain_loss = market_value - cost_basis if market_value is not None else None
        gain_loss_pct = gain_loss / cost_basis * 100 if gain_loss is not None and cost_basis != 0 else None
        partial.append((h, current_price, cost_basis, market_value, gain_loss, gain_loss_pct))

    total_market_value = sum((mv for *_, mv, _, _ in partial if mv is not None), Decimal("0"))

    enriched = []
    for h, current_price, cost_basis, market_value, gain_loss, gain_loss_pct in partial:
        allocation_pct = (
            market_value / total_market_value * 100
            if market_value is not None and total_market_value > 0
            else None
        )
        enriched.append(
            EnrichedHolding(
                holding=h,
                current_price=current_price,
                cost_basis=cost_basis,
                market_value=market_value,
                gain_loss=gain_loss,
                gain_loss_pct=gain_loss_pct,
                allocation_pct=allocation_pct,
            )
        )
    return enriched
