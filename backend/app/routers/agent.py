import os
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import SessionLocal, get_db
from app.services import agent, exports, portfolio

router = APIRouter(prefix="/agent", tags=["agent"])

EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PPTX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _to_run_read(run: models.AgentRun) -> schemas.AgentRunRead:
    return schemas.AgentRunRead(
        id=run.id,
        status=run.status,
        summary=run.summary,
        started_at=run.started_at,
        completed_at=run.completed_at,
        excel_url=f"/agent/runs/{run.id}/excel" if run.excel_path else None,
        pptx_url=f"/agent/runs/{run.id}/pptx" if run.pptx_path else None,
    )


def _get_run_or_404(db: Session, run_id: int) -> models.AgentRun:
    run = db.query(models.AgentRun).filter(models.AgentRun.id == run_id).first()
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return run


async def _execute_run(run_id: int) -> None:
    db = SessionLocal()
    try:
        run = db.query(models.AgentRun).filter(models.AgentRun.id == run_id).first()
        analysis = await agent.run_analysis(db)
        holdings = await portfolio.get_enriched_holdings(db)
        excel_path = exports.generate_excel(run_id, analysis, holdings)
        pptx_path = exports.generate_pptx(run_id, analysis, holdings)

        run.status = "success"
        run.summary = analysis.overview
        run.excel_path = excel_path
        run.pptx_path = pptx_path
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:  # noqa: BLE001 - persist any failure onto the run row
        run.status = "failed"
        run.summary = f"{type(exc).__name__}: {exc}"
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


@router.post("/analyze", response_model=schemas.AgentRunRead, status_code=202)
def trigger_analysis(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = models.AgentRun(status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(_execute_run, run.id)
    return _to_run_read(run)


@router.get("/runs/{run_id}", response_model=schemas.AgentRunRead)
def get_run(run_id: int, db: Session = Depends(get_db)):
    return _to_run_read(_get_run_or_404(db, run_id))


@router.get("/runs/{run_id}/excel")
def download_excel(run_id: int, db: Session = Depends(get_db)):
    run = _get_run_or_404(db, run_id)
    if not run.excel_path or not os.path.exists(run.excel_path):
        raise HTTPException(status_code=404, detail="excel export not available")
    return FileResponse(
        run.excel_path,
        media_type=EXCEL_MEDIA_TYPE,
        filename=f"portfolio_analysis_{run_id}.xlsx",
    )


@router.get("/runs/{run_id}/pptx")
def download_pptx(run_id: int, db: Session = Depends(get_db)):
    run = _get_run_or_404(db, run_id)
    if not run.pptx_path or not os.path.exists(run.pptx_path):
        raise HTTPException(status_code=404, detail="pptx export not available")
    return FileResponse(
        run.pptx_path,
        media_type=PPTX_MEDIA_TYPE,
        filename=f"portfolio_analysis_{run_id}.pptx",
    )
