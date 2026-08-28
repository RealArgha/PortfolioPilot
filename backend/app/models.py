from sqlalchemy import Column, Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    quantity = Column(Numeric, nullable=False)
    buy_price = Column(Numeric, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (UniqueConstraint("ticker", "snapshot_date", name="uq_ticker_snapshot_date"),)

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), nullable=False)
    price = Column(Numeric, nullable=False)
    snapshot_date = Column(Date, nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=False)  # 'running' | 'success' | 'failed'
    summary = Column(Text)
    excel_path = Column(Text)
    pptx_path = Column(Text)
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
