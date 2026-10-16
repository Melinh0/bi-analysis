from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from bi_analysis.database.session import get_db_session
from bi_analysis.database.models import Report, ExtractedItem, SourceType, ContentType
from bi_analysis.rag.reports import generate_report, ReportGenerator, REPORT_TEMPLATES

router = APIRouter()


class ReportRequest(BaseModel):
    title: str
    report_type: str
    filters: Dict[str, Any]
    template: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    title: str
    report_type: str
    status: str
    generated_content: Optional[str]
    created_at: datetime
    generated_at: Optional[datetime]


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]


def get_db():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=ReportResponse)
async def create_report(request: ReportRequest, db: Session = Depends(get_db)):
    try:
        report = generate_report(
            title=request.title,
            report_type=request.report_type,
            filters=request.filters,
            template=request.template,
        )
        return ReportResponse(
            id=report.id,
            title=report.title,
            report_type=report.report_type,
            status=report.status,
            generated_content=report.generated_content,
            created_at=report.created_at,
            generated_at=report.generated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("", response_model=ReportListResponse)
async def list_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(50).all()
    return ReportListResponse(
        reports=[
            ReportResponse(
                id=r.id,
                title=r.title,
                report_type=r.report_type,
                status=r.status,
                generated_content=r.generated_content,
                created_at=r.created_at,
                generated_at=r.generated_at,
            )
            for r in reports
        ]
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return ReportResponse(
        id=report.id,
        title=report.title,
        report_type=report.report_type,
        status=report.status,
        generated_content=report.generated_content,
        created_at=report.created_at,
        generated_at=report.generated_at,
    )


@router.get("/templates/list")
async def list_templates():
    return {"templates": list(REPORT_TEMPLATES.keys())}


@router.delete("/{report_id}")
async def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    db.delete(report)
    db.commit()
    return {"message": "Report deleted"}


@router.get("/types/list")
async def list_report_types():
    return {
        "types": [
            {"id": "executive_summary", "name": "Resumo Executivo", "description": "Visão geral com insights e recomendações"},
            {"id": "sentiment_analysis", "name": "Análise de Sentimento", "description": "Distribuição de sentimentos e tópicos"},
            {"id": "trend_report", "name": "Relatório de Tendências", "description": "Evolução temporal e picos de atividade"},
            {"id": "custom", "name": "Personalizado", "description": "Template customizado"},
        ]
    }
