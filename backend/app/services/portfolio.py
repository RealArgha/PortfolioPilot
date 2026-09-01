from dataclasses import dataclass
from datetime import date
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


def record_daily_snapshots(db: Session, enriched: list[EnrichedHolding]) -> None:
    """Upsert today's price for each held ticker into price_snapshots.

    Called as a side effect of normal dashboard usage (no cron needed for
    the MVP) so /portfolio/history has real data to show once a user has
    opened the dashboard on more than one day.
    """
    today = date.today()
    seen_tickers: set[str] = set()
    for e in enriched:
        ticker = e.holding.ticker
        if e.current_price is None or ticker in seen_tickers:
            continue
        seen_tickers.add(ticker)

        existing = (
            db.query(models.PriceSnapshot)
            .filter(models.PriceSnapshot.ticker == ticker, models.PriceSnapshot.snapshot_date == today)
            .first()
        )
        if existing:
            existing.price = e.current_price
        else:
            db.add(models.PriceSnapshot(ticker=ticker, price=e.current_price, snapshot_date=today))
    db.commit()


def get_history(db: Session) -> list[tuple[date, Decimal]]:
    """Total portfolio value per date, using *current* holdings' quantities
    against each date's stored snapshot price. Doesn't account for holdings
    added/removed over time — an acceptable approximation for the MVP.
    """
    holdings = db.query(models.Holding).all()
    qty_by_ticker: dict[str, Decimal] = {}
    for h in holdings:
        qty_by_ticker[h.ticker] = qty_by_ticker.get(h.ticker, Decimal("0")) + h.quantity

    if not qty_by_ticker:
        return []

    snapshots = (
        db.query(models.PriceSnapshot)
        .filter(models.PriceSnapshot.ticker.in_(qty_by_ticker.keys()))
        .order_by(models.PriceSnapshot.snapshot_date)
        .all()
    )

    totals: dict[date, Decimal] = {}
    for snap in snapshots:
        qty = qty_by_ticker[snap.ticker]
        totals[snap.snapshot_date] = totals.get(snap.snapshot_date, Decimal("0")) + qty * snap.price

    return sorted(totals.items())
