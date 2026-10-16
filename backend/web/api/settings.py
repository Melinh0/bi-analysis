import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from bi_analysis.config.settings import apply_settings, get_env_file, get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


EDITABLE_FIELDS: List[str] = [
    "ollama_base_url",
    "ollama_api_key",
    "ollama_model",
    "ollama_embedding_model",
    "ollama_available_models",
    "instagram_email",
    "instagram_password",
    "log_level",
]


class SettingsResponse(BaseModel):
    settings: Dict[str, Any]
    env_file: str
    env_exists: bool


class SettingsUpdate(BaseModel):
    ollama_base_url: Optional[str] = None
    ollama_api_key: Optional[str] = None
    ollama_model: Optional[str] = None
    ollama_embedding_model: Optional[str] = None
    ollama_available_models: Optional[str] = None
    instagram_email: Optional[str] = None
    instagram_password: Optional[str] = None
    log_level: Optional[str] = None


def _current_response() -> SettingsResponse:
    settings = get_settings()
    env_path = get_env_file()
    return SettingsResponse(
        settings={name: getattr(settings, name) for name in EDITABLE_FIELDS},
        env_file=str(env_path),
        env_exists=env_path.exists(),
    )


@router.get("", response_model=SettingsResponse)
async def get_app_settings() -> SettingsResponse:
    return _current_response()


@router.put("", response_model=SettingsResponse)
async def update_app_settings(request: SettingsUpdate) -> SettingsResponse:
    updates = {
        name: getattr(request, name)
        for name in request.model_fields_set
        if name in EDITABLE_FIELDS
    }
    if not updates:
        raise HTTPException(status_code=400, detail="Nenhuma configuração enviada")

    try:
        apply_settings(updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except OSError as exc:
        logger.exception("Falha ao gravar o arquivo .env")
        raise HTTPException(status_code=500, detail=f"Falha ao gravar .env: {exc}")

    if "ollama_model" in updates or "ollama_base_url" in updates or "ollama_api_key" in updates:

        from bi_analysis.llm.client import reset_ollama_client

        reset_ollama_client()
    if "log_level" in updates:
        level = str(getattr(get_settings(), "log_level", "") or "")
        try:
            logging.getLogger().setLevel(level.upper())
        except ValueError:
            logger.warning("Log level inválido ignorado: %r", level)

    return _current_response()
