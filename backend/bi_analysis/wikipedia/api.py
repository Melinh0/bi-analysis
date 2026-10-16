





import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote, unquote, urlparse

import requests

logger = logging.getLogger(__name__)

API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"

_IDIOMAS_PADRAO = ("pt", "en")


class WikipediaAPIError(RuntimeError):
    pass


class WikipediaAPI:


    def __init__(self, idioma: Optional[str] = None) -> None:
        self.idioma = idioma or "pt"



    @staticmethod
    def resolver_alvo(alvo: str) -> Dict[str, str]:

        texto = (alvo or "").strip()
        if not texto:
            raise WikipediaAPIError(
                "Wikipédia: informe o nome do artigo ou a URL da página."
            )

        m = re.search(r"(?:https?://)?([a-z-]+)\.(?:m\.)?wikipedia\.org/wiki/([^?#]+)", texto)
        if m:
            return {"titulo": unquote(m.group(2)).replace("_", " "), "idioma": m.group(1)}

        return {"titulo": texto.replace("_", " "), "idioma": "pt"}



    def pageviews(self, titulo: str, dias: int = 30) -> List[Dict[str, Any]]:

        fim = datetime.now(timezone.utc).date() - timedelta(days=1)
        inicio = fim - timedelta(days=max(1, min(dias, 365)) - 1)
        projeto = f"{self.idioma}.wikipedia"
        caminho = (
            f"{API_BASE}/{projeto}/all-access/user/{quote(titulo.replace(' ', '_'), safe='')}"
            f"/daily/{inicio:%Y%m%d}/{fim:%Y%m%d}"
        )
        try:
            resposta = requests.get(caminho, timeout=30, headers={"User-Agent": "BI Analysis/1.0"})
        except (requests.Timeout, requests.ConnectionError) as exc:
            raise WikipediaAPIError(f"Wikipédia: falha de comunicação com a API ({exc}).") from exc

        if resposta.status_code == 404:
            raise WikipediaAPIError(
                f"Wikipédia: página '{titulo}' ({self.idioma}) não encontrada — "
                "confira o nome do artigo ou informe a URL completa."
            )
        if resposta.status_code != 200:
            raise WikipediaAPIError(
                f"Wikipédia: a API respondeu HTTP {resposta.status_code} ({resposta.text[:200]})"
            )
        return resposta.json().get("items") or []
