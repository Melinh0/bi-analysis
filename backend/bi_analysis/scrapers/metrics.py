







import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


_SUFIXOS: Dict[str, float] = {
    "k": 1e3,
    "mil": 1e3,
    "m": 1e6,
    "mi": 1e6,
    "milhao": 1e6,
    "milhoes": 1e6,
    "milhão": 1e6,
    "milhões": 1e6,
    "b": 1e9,
    "bi": 1e9,
    "bilhao": 1e9,
    "bilhoes": 1e9,
    "bilhão": 1e9,
    "bilhões": 1e9,
}


_ALIASES_CAMPO: Dict[str, Tuple[str, ...]] = {
    "curtidas": ("curtidas", "likes", "like_count", "likecount", "curtidas_count"),
    "comentarios": (
        "comentarios", "comentários", "comments", "num_comments",
        "comment_count", "respostas", "replies",
    ),
    "visualizacoes": (
        "visualizacoes", "visualizações", "views", "view_count",
        "viewcount", "plays", "visualizacoes_totais", "visualizações_totais",
    ),
    "pontuacao": ("pontuacao", "pontuação", "score", "upvotes", "points"),
    "compartilhamentos": (
        "compartilhamentos", "shares", "retweets", "compartilhadas",
    ),
    "inscritos": (
        "inscritos", "subscribercount", "subscribers", "seguidores",
        "followers",
    ),
}

_CAMPOS_NUMERICOS = (
    "curtidas", "comentarios", "visualizacoes", "pontuacao", "compartilhamentos",
)


def _para_numero(valor: Any) -> Optional[float]:

    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)

    texto = str(valor).strip().lower().replace("\u00a0", "").replace(" ", "")
    if not texto:
        return None

    multiplicador = 1.0
    for sufixo, fator in sorted(_SUFIXOS.items(), key=lambda kv: -len(kv[0])):
        if texto.endswith(sufixo):
            multiplicador = fator
            texto = texto[: -len(sufixo)]
            break
    texto = texto.strip(".,;: ")

    if re.fullmatch(r"-?\d{1,3}([,.]\d{3})+", texto):

        texto = texto.replace(",", "").replace(".", "")
    elif "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", "")

    try:
        return float(texto) * multiplicador
    except ValueError:
        return None


def _buscar_meta(meta: Dict[str, Any], aliases: Tuple[str, ...]) -> Any:
    mapa = {str(chave).lower(): valor for chave, valor in meta.items()}
    for alias in aliases:
        chave = str(alias).lower()
        if chave in mapa and mapa[chave] is not None:
            return mapa[chave]
    return None


def _data_iso(valor: Any) -> Optional[str]:
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(float(valor), tz=timezone.utc).date().isoformat()
    texto = str(valor).strip()
    if texto.isdigit():
        return datetime.fromtimestamp(float(int(texto)), tz=timezone.utc).date().isoformat()
    return texto[:10]


def normalizar_item(item_bd) -> Dict[str, Any]:

    meta = {str(k).lower(): v for k, v in dict(item_bd.extra_data or {}).items()}
    data_iso = item_bd.published_at.isoformat()[:10] if item_bd.published_at else None
    base: Dict[str, Any] = {
        "id": item_bd.id,
        "external_id": item_bd.external_id,
        "url": item_bd.url,
        "autor": item_bd.author,
        "plataforma": meta.get("plataforma"),
        "tipo_item": meta.get("tipo_item"),
        "imagem": meta.get("imagem"),
        "titulo": meta.get("titulo") or (item_bd.content or "")[:120],
        "conteudo": (item_bd.content or "")[:500],
        "publicado_em": str(meta.get("publicado_em") or ""), 
        "data": data_iso,
    }

    for campo, aliases in _ALIASES_CAMPO.items():
        base[campo] = _para_numero(_buscar_meta(meta, aliases))


    if base.get("curtidas") is None and base.get("pontuacao") is not None:
        base["curtidas"] = base["pontuacao"]

    base["engajamento"] = sum(
        base.get(campo) or 0.0 for campo in ("curtidas", "comentarios", "compartilhamentos")
    )
    return base


def _resumo(itens: List[Dict[str, Any]], perfis: List[Dict[str, Any]]) -> Dict[str, Any]:
    totais: Dict[str, float] = {}
    for campo in _CAMPOS_NUMERICOS:
        soma = sum(item.get(campo) or 0.0 for item in itens)
        if any(item.get(campo) is not None for item in itens):
            totais[f"total_{campo}"] = soma

    engajamento_total = sum(item.get("engajamento") or 0.0 for item in itens)
    destaque = max(itens, key=lambda item: item.get("engajamento") or 0.0, default=None)
    volume_total = sum(item.get("visualizacoes") or 0.0 for item in itens)

    return {
        "total_itens": len(itens),
        "total_perfis": len(perfis),
        "totais": totais,
        "engajamento_total": engajamento_total,
        "media_engajamento": (engajamento_total / len(itens)) if itens else 0.0,
        "visualizacoes_total": volume_total,
        "taxa_engajamento": (engajamento_total / volume_total) if volume_total else None,
        "destaque": (
            {
                "id": destaque.get("id"),
                "titulo": destaque.get("titulo"),
                "url": destaque.get("url"),
                "engajamento": destaque.get("engajamento"),
            }
            if destaque and (destaque.get("engajamento") or 0.0) > 0
            else None
        ),
    }


def _serie_temporal(itens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    agrupado: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for item in itens:
        data = item.get("data")
        if not data:
            continue
        alvo = agrupado[data]
        alvo["engajamento"] += item.get("engajamento") or 0.0
        alvo["visualizacoes"] += item.get("visualizacoes") or 0.0
        alvo["comentarios"] += item.get("comentarios") or 0.0
        alvo["itens"] += 1
    return [
        {"data": data, **{chave: valor for chave, valor in valores.items()}}
        for data, valores in sorted(agrupado.items())
    ]


def _ranking(itens: List[Dict[str, Any]], metrica: str = "engajamento", limite: int = 10) -> List[Dict[str, Any]]:
    ordenados = sorted(
        itens, key=lambda item: item.get(metrica) or 0.0, reverse=True
    )[:limite]
    return [
        {
            "posicao": posicao,
            "id": item.get("id"),
            "titulo": item.get("titulo"),
            "url": item.get("url"),
            "autor": item.get("autor"),
            "valor": item.get(metrica) or 0.0,
            "curtidas": item.get("curtidas"),
            "comentarios": item.get("comentarios"),
            "visualizacoes": item.get("visualizacoes"),
            "metrica": metrica,
        }
        for posicao, item in enumerate(ordenados, start=1)
        if (item.get(metrica) or 0.0) > 0
    ]


def analisar_job(db, job_id: int) -> Optional[Dict[str, Any]]:

    from bi_analysis.database.models import ExtractionJob, ExtractedItem

    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if job is None:
        return None

    itens_bd = (
        db.query(ExtractedItem)
        .filter(ExtractedItem.job_id == job_id)
        .order_by(ExtractedItem.id.asc())
        .all()
    )

    itens: List[Dict[str, Any]] = []
    perfis: List[Dict[str, Any]] = []
    for item_bd in itens_bd:
        normalizado = normalizar_item(item_bd)
        if normalizado.get("tipo_item") == "perfil":
            perfis.append(normalizado)
        else:
            itens.append(normalizado)

    params = dict(job.query_params or {})
    alvo = params.get("alvo") or params.get("query") or params.get("termo") or params.get("url")

    return {
        "job_id": job.id,
        "fonte": job.source_type.value,
        "tipo_conteudo": job.content_type.value,
        "status": job.status,
        "alvo": alvo,
        "iniciado_em": job.started_at.isoformat() if job.started_at else None,
        "resumo": _resumo(itens, perfis),
        "perfis": perfis,
        "itens": itens,
        "serie_temporal": _serie_temporal(itens),
        "ranking": _ranking(itens),
    }


def compilar_relatorio_dados(db, job_id: int) -> Optional[Dict[str, Any]]:

    analise = analisar_job(db, job_id)
    if analise is None:
        return None

    resumo = analise.get("resumo") or {}
    totais = resumo.get("totais") or {}
    linhas = [
        f"# Análise do job #{job_id} — fonte {analise.get('fonte')} "
        f"({analise.get('tipo_conteudo')})",
        f"- Alvo: {analise.get('alvo') or 'não informado'}",
        f"- Itens analisados: {resumo.get('total_itens', 0)} "
        f"(perfis: {resumo.get('total_perfis', 0)})",
    ]
    for campo, valor in totais.items():
        linhas.append(f"- {campo.replace('_', ' ')}: {valor:,.0f}".replace(",", "."))
    linhas.append(
        f"- Engajamento total: {resumo.get('engajamento_total', 0):,.0f}".replace(",", ".")
    )

    destaque = resumo.get("destaque")
    if destaque:
        linhas.append(
            f"- Item de maior engajamento: {destaque.get('titulo')} "
            f"({destaque.get('engajamento', 0):,.0f})".replace(",", ".")
        )

    if analise.get("serie_temporal"):
        primeira = analise["serie_temporal"][0].get("data")
        ultima = analise["serie_temporal"][-1].get("data")
        linhas.append(f"- Série temporal disponível: {primeira} a {ultima}")

    return {"job_id": job_id, "texto": "\n".join(linhas), "analise": analise}
