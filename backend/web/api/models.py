from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from bi_analysis.config.settings import get_settings
from bi_analysis.llm.client import get_ollama_client

router = APIRouter()
settings = get_settings()


class ModelInfo(BaseModel):
    name: str
    type: str
    available: bool


class ModelsResponse(BaseModel):
    current_model: str
    embedding_model: str
    available_models: List[str]
    models: List[ModelInfo]


def _normalize(name: str) -> str:

    if not name:
        return ""
    base = name.split("/")[-1]
    if base.endswith(":latest"):
        base = base[: -len(":latest")]
    return base.lower()


@router.get("", response_model=ModelsResponse)
async def get_models():
    client = get_ollama_client()
    available_raw = client.list_models()
    available_lookup = {_normalize(m) for m in available_raw}

    configured_models = [
        m.strip() for m in settings.ollama_available_models.split(",") if m.strip()
    ]

    models = [
        ModelInfo(
            name=model,
            type="chat",
            # Cloud /api/tags may not list aliases (e.g. gemma4:cloud); the
            # configured current model is known to work, so trust it.
            available=(
                model == settings.ollama_model
                or (
                    _normalize(model) in available_lookup
                    if available_lookup
                    else True
                )
            ),
        )
        for model in configured_models
    ]

    return ModelsResponse(
        current_model=settings.ollama_model,
        embedding_model=settings.ollama_embedding_model,
        available_models=configured_models,
        models=models,
    )


@router.post("/pull/{model_name}")
async def pull_model(model_name: str):
    client = get_ollama_client()
    success = client.pull_model(model_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to pull model")
    return {"message": f"Model {model_name} pulled successfully"}
