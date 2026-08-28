from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import holdings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PortfolioPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(holdings.router)


@app.get("/health")
def health():
    return {"status": "ok"}
