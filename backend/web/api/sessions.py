import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from bi_analysis.sessions import manager

router = APIRouter()
logger = logging.getLogger(__name__)


class SessionStatus(BaseModel):
    fonte: str
    nome: str
    status: str
    last_login: str | None = None
    last_validated: str | None = None
    error: str | None = None


class SessionListResponse(BaseModel):
    sessions: list[SessionStatus]


def _para_status(estado: dict) -> SessionStatus:
    nome = manager.PLATAFORMAS.get(estado.get("fonte", ""), {}).get("nome", estado.get("fonte", ""))
    return SessionStatus(
        fonte=estado.get("fonte", ""),
        nome=nome,
        status=estado.get("status", "disconnected"),
        last_login=estado.get("last_login"),
        last_validated=estado.get("last_validated"),
        error=estado.get("error"),
    )


def _executar_login(fonte: str, timeout: int) -> None:
    try:
        manager.login_manual(fonte, timeout=timeout)
    except Exception:
        logger.exception("Falha no login manual de %s", fonte)


@router.get("", response_model=SessionListResponse)
async def listar_sessoes():
    return SessionListResponse(sessions=[_para_status(e) for e in manager.status_todas()])


@router.get("/{fonte}", response_model=SessionStatus)
async def obter_sessao(fonte: str):
    try:
        estado = manager.status_de(fonte)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _para_status(estado)


@router.post("/{fonte}/login", response_model=SessionStatus)
async def iniciar_login(fonte: str, background_tasks: BackgroundTasks, timeout: int = 300):
    try:
        manager.status_de(fonte)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if not manager._desktop_disponivel():
        raise HTTPException(
            status_code=400,
            detail="Sem interface gráfica disponível para o login manual.",
        )

    estado = manager.status_de(fonte)
    if estado.get("status") == "logging_in":
        return _para_status(estado)

    background_tasks.add_task(_executar_login, fonte, timeout)
    return _para_status(manager._gravar_estado(fonte, status="logging_in", error=None))


@router.delete("/{fonte}", response_model=SessionStatus)
async def desconectar_sessao(fonte: str):
    try:
        estado = manager.logout(fonte)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _para_status(estado)
