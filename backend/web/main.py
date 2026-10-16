import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
import sys

from bi_analysis.config.settings import get_settings
from bi_analysis.database.session import init_db, get_db_session
from web.api import chat, reports, extraction, health, models, settings as settings_api, sessions as sessions_api

settings = get_settings()

log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    level=settings.log_level,
    format=log_format,
    datefmt=date_format,
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("pydantic").setLevel(logging.WARNING)


logging.getLogger("sqlalchemy.engine").disabled = True
logging.getLogger("sqlalchemy.pool").disabled = True

logger = logging.getLogger("bi_analysis.web")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")

    try:
        from bi_analysis.database.models import ExtractionJob
        from datetime import datetime, timedelta

        db = get_db_session()
        try:
            corte = datetime.utcnow() - timedelta(hours=24)
            orfaos = (
                db.query(ExtractionJob)
                .filter(
                    ExtractionJob.status == "running",
                    ExtractionJob.started_at < corte,
                )
                .all()
            )
            for job in orfaos:
                job.status = "failed"
                job.error_message = "Servidor reiniciou durante a execução. Execute novamente."
                logger.warning("Job órfão %s marcado como failed.", job.id)
            db.commit()
        finally:
            db.close()
    except Exception:
        logger.warning("Falha ao recuperar jobs órfãos", exc_info=True)

    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="BI Analysis - Data extraction, RAG, and reporting platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(extraction.router, prefix="/api/extraction", tags=["extraction"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])
app.include_router(sessions_api.router, prefix="/api/sessions", tags=["sessions"])



BASE_DIR = Path(__file__).parent.parent.parent
frontend_build_path = BASE_DIR / "frontend" / "dist"

if frontend_build_path.exists():

    app.mount("/assets", StaticFiles(directory=str(frontend_build_path / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):

        if full_path.startswith("api/"):
            return {"detail": "Not found"}


        index_file = frontend_build_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"detail": "Frontend not built"}
else:
    @app.get("/")
    async def root():
        return {"message": "BI Analysis API", "docs": "/docs", "frontend": "Run 'npm run build' in frontend/ to serve UI"}


def main():
    reload_dirs = ["backend/web", "backend/bi_analysis"]
    reload_excludes = [".venv", "__pycache__", "*.pyc", ".git", "data", "logs", "*.db", "*.sqlite", "frontend/node_modules"]

    uvicorn.run(
        "web.main:app",
        host=settings.web_host,
        port=settings.web_port,
        reload=settings.debug,
        reload_dirs=reload_dirs,
        reload_excludes=reload_excludes,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()