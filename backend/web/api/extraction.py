from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from bi_analysis.database.session import get_db_session
from bi_analysis.database.models import ExtractionJob, ExtractedItem, SourceType, ContentType, ScheduledJob
from bi_analysis.config.settings import get_settings

router = APIRouter()
settings = get_settings()


class ExtractionRequest(BaseModel):
    source_type: SourceType
    content_type: ContentType
    query_params: Optional[Dict[str, Any]] = None


class ExtractionJobResponse(BaseModel):
    id: int
    source_type: SourceType
    content_type: ContentType
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    items_extracted: int
    items_stored: int
    error_message: Optional[str]


class ExtractionJobListResponse(BaseModel):
    jobs: List[ExtractionJobResponse]


class ScheduledJobRequest(BaseModel):
    name: str
    source_type: SourceType
    content_type: ContentType
    query_params: Optional[Dict[str, Any]] = None
    cron_expression: str


class ScheduledJobResponse(BaseModel):
    id: int
    name: str
    source_type: SourceType
    content_type: ContentType
    cron_expression: str
    is_active: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]


def get_db():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


def run_extraction(job_id: int):
    from bi_analysis.scrapers.orchestrator import run_extraction_job
    run_extraction_job(job_id)


def _rejeitar_fonte_removida(source_type: SourceType) -> None:

    if source_type == SourceType.KNEWIN:
        raise HTTPException(
            status_code=400,
            detail="A fonte Knewin foi removida da ferramenta. Use Instagram, TikTok, YouTube ou Reddit.",
        )
    if source_type == SourceType.TWITTER:
        raise HTTPException(
            status_code=400,
            detail="A fonte Twitter/X foi removida da ferramenta. Use Instagram ou TikTok.",
        )


@router.post("", response_model=ExtractionJobResponse)
async def create_extraction_job(
    request: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    _rejeitar_fonte_removida(request.source_type)
    job = ExtractionJob(
        source_type=request.source_type,
        content_type=request.content_type,
        query_params=request.query_params,
        status="running",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    background_tasks.add_task(run_extraction, job.id)
    
    return ExtractionJobResponse(
        id=job.id,
        source_type=job.source_type,
        content_type=job.content_type,
        status=job.status,
        started_at=job.started_at,
        completed_at=job.completed_at,
        items_extracted=job.items_extracted,
        items_stored=job.items_stored,
        error_message=job.error_message,
    )


@router.get("", response_model=ExtractionJobListResponse)
async def list_extraction_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ExtractionJob).order_by(ExtractionJob.started_at.desc()).limit(50).all()
    return ExtractionJobListResponse(
        jobs=[
            ExtractionJobResponse(
                id=j.id,
                source_type=j.source_type,
                content_type=j.content_type,
                status=j.status,
                started_at=j.started_at,
                completed_at=j.completed_at,
                items_extracted=j.items_extracted,
                items_stored=j.items_stored,
                error_message=j.error_message,
            )
            for j in jobs
        ]
    )


@router.get("/{job_id}", response_model=ExtractionJobResponse)
async def get_extraction_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return ExtractionJobResponse(
        id=job.id,
        source_type=job.source_type,
        content_type=job.content_type,
        status=job.status,
        started_at=job.started_at,
        completed_at=job.completed_at,
        items_extracted=job.items_extracted,
        items_stored=job.items_stored,
        error_message=job.error_message,
    )


@router.get("/{job_id}/analise")
async def get_extraction_analise(job_id: int, db: Session = Depends(get_db)):

    from bi_analysis.scrapers.metrics import analisar_job

    analise = analisar_job(db, job_id)
    if analise is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return analise


@router.get("/{job_id}/items")
async def get_extracted_items(job_id: int, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    items = db.query(ExtractedItem).filter(ExtractedItem.job_id == job_id).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": i.id,
                "external_id": i.external_id,
                "url": i.url,
                "author": i.author,
                "content": i.content[:500] + "..." if len(i.content) > 500 else i.content,
                "metadata": i.extra_data,
                "published_at": i.published_at,
                "extracted_at": i.extracted_at,
                "processed": i.processed,
            }
            for i in items
        ],
        "total": db.query(ExtractedItem).filter(ExtractedItem.job_id == job_id).count(),
    }


@router.post("/scheduled", response_model=ScheduledJobResponse)
async def create_scheduled_job(request: ScheduledJobRequest, db: Session = Depends(get_db)):
    _rejeitar_fonte_removida(request.source_type)
    job = ScheduledJob(
        name=request.name,
        source_type=request.source_type,
        content_type=request.content_type,
        query_params=request.query_params,
        cron_expression=request.cron_expression,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return ScheduledJobResponse(
        id=job.id,
        name=job.name,
        source_type=job.source_type,
        content_type=job.content_type,
        cron_expression=job.cron_expression,
        is_active=job.is_active,
        last_run=job.last_run,
        next_run=job.next_run,
    )


@router.get("/scheduled", response_model=List[ScheduledJobResponse])
async def list_scheduled_jobs(db: Session = Depends(get_db)):
    jobs = db.query(ScheduledJob).all()
    return [
        ScheduledJobResponse(
            id=j.id,
            name=j.name,
            source_type=j.source_type,
            content_type=j.content_type,
            cron_expression=j.cron_expression,
            is_active=j.is_active,
            last_run=j.last_run,
            next_run=j.next_run,
        )
        for j in jobs
    ]


@router.delete("/scheduled/{job_id}")
async def delete_scheduled_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    
    db.delete(job)
    db.commit()
    return {"message": "Scheduled job deleted"}


@router.post("/scheduled/{job_id}/toggle")
async def toggle_scheduled_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scheduled job not found")
    
    job.is_active = not job.is_active
    db.commit()
    return {"message": f"Scheduled job {'activated' if job.is_active else 'deactivated'}"}
