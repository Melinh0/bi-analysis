import logging
import random
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from bi_analysis.browser.stealth import (
    dispensar_banner_cookies,
    esperar_carregamento,
    mover_mouse_humano,
    scroll_humano,
)

logger = logging.getLogger(__name__)


class RedditBot:
    def __init__(self, driver) -> None:
        self.driver = driver

    @staticmethod
    def resolver_alvo(alvo: str) -> Dict[str, str]:
        texto = (alvo or "").strip()
        if not texto:
            raise ValueError(
                "Reddit: informe a URL da postagem, r/subreddit, u/usuario ou um termo de busca."
            )

        m = re.search(r"reddit\.com/r/([\w]+)/comments/([\w]+)", texto)
        if m:
            return {"tipo": "postagem", "subreddit": m.group(1), "id": m.group(2), "termo": texto}

        m = re.search(r"reddit\.com/(?:r|comments)/([\w]+)", texto)
        if m:
            return {"tipo": "subreddit", "nome": m.group(1), "termo": texto}

        m = re.search(r"reddit\.com/(?:user|u)/([\w-]+)", texto)
        if m:
            return {"tipo": "usuario", "nome": m.group(1), "termo": texto}

        if texto.startswith("/r/"):
            return {"tipo": "subreddit", "nome": texto[3:], "termo": texto}
        if texto.startswith("r/"):
            return {"tipo": "subreddit", "nome": texto[2:], "termo": texto}
        if texto.startswith("/u/") or texto.startswith("u/"):
            return {"tipo": "usuario", "nome": texto.split("/", 1)[1], "termo": texto}

        return {"tipo": "busca", "termo": texto}

    def ir_para(self, url: str) -> None:
        self.driver.get(url)
        esperar_carregamento(self.driver)
        time.sleep(random.uniform(1.5, 2.5))

        try:
            dispensar_banner_cookies(self.driver)
        except Exception:
            pass

        mover_mouse_humano(self.driver)

    def _texto_um(self, candidatos: List[str]) -> Optional[str]:
        from selenium.webdriver.common.by import By

        for seletor in candidatos:
            try:
                elementos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                for el in elementos:
                    texto = (el.text or "").strip()
                    if texto:
                        return texto
            except Exception:
                continue
        return None

    @staticmethod
    def _parse_numero(texto: Optional[str]) -> Optional[int]:
        if not texto:
            return None
        t = texto.strip().lower().replace(".", "").replace(",", "")
        mult = 1
        for sufixo, valor in (("k", 1_000), ("mil", 1_000), ("m", 1_000_000), ("b", 1_000_000_000)):
            if t.endswith(sufixo):
                mult = valor
                t = t[: -len(sufixo)]
                break
        t = t.replace("pontos", "").replace("pts", "").strip()
        try:
            return int(float(t) * mult)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _url_antiga(url: str) -> str:
        url = url.strip()
        if url.startswith("/"):
            url = f"https://www.reddit.com{url}"
        return url.replace("https://www.reddit.com", "https://old.reddit.com").replace(
            "https://old.reddit.com", "https://old.reddit.com", 1
        )

    def _coletar_posts(self, limite: int) -> List[Dict[str, Any]]:
        from selenium.webdriver.common.by import By

        itens: List[Dict[str, Any]] = []
        vistos = set()
        tentativas = 0

        while len(itens) < limite and tentativas < 8:
            tentativas += 1
            try:
                coisas = self.driver.find_elements(By.CSS_SELECTOR, "div.thing")
            except Exception:
                coisas = []

            for coisa in coisas:
                if len(itens) >= limite:
                    break
                try:
                    permalink = coisa.get_attribute("data-permalink") or ""
                    if not permalink or permalink in vistos:
                        continue
                    vistos.add(permalink)

                    autor = coisa.get_attribute("data-author") or None
                    subreddit = coisa.get_attribute("data-subreddit-prefixed") or coisa.get_attribute("data-subreddit")

                    titulo = None
                    titulo_el = coisa.find_elements(By.CSS_SELECTOR, "a.search-title")
                    if titulo_el:
                        titulo = (titulo_el[0].text or "").strip() or None

                    score = None
                    score_el = coisa.find_elements(By.CSS_SELECTOR, "div.score.unvoted")
                    if score_el:
                        score = RedditBot._parse_numero(score_el[0].get_attribute("data-score"))

                    comentarios = None
                    comentarios_el = coisa.find_elements(By.CSS_SELECTOR, 'a[data-event-action="comments"]')
                    if comentarios_el:
                        comentarios = RedditBot._parse_numero((comentarios_el[0].text or "").split()[0])

                    publicado = None
                    tempo_el = coisa.find_elements(By.CSS_SELECTOR, "time.live-timestamp")
                    if tempo_el:
                        publicado = tempo_el[0].get_attribute("datetime")

                    url = RedditBot._url_antiga(permalink)
                    itens.append({
                        "external_id": permalink.rstrip("/").rsplit("/", 1)[-1],
                        "url": url.replace("old.reddit.com", "www.reddit.com"),
                        "author": autor,
                        "content": titulo or url,
                        "metadata": {
                            "plataforma": "reddit",
                            "subreddit": subreddit,
                            "score": score,
                            "comentarios": comentarios,
                        },
                        "published_at": publicado,
                    })
                except Exception:
                    continue

            if len(itens) < limite:
                scroll_humano(self.driver, vezes=2)
                time.sleep(random.uniform(0.8, 1.5))

        return itens[:limite]

    def extrair_postagem(self, alvo: str) -> Optional[Dict[str, Any]]:
        url = self._url_antiga(alvo)
        self.ir_para(url)

        titulo = self._texto_um(["div.titlebox h1 a", "h1.title a", "h1"])
        autor = None
        autor_el = self.driver.find_elements(By.CSS_SELECTOR, "a.author")
        if autor_el:
            autor = (autor_el[0].text or "").strip() or None

        score = None
        score_el = self.driver.find_elements(By.CSS_SELECTOR, "div.score.unvoted")
        if score_el:
            score = self._parse_numero(score_el[0].get_attribute("data-score"))

        comentarios = None
        comentarios_el = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-event-action="comments"]')
        if comentarios_el:
            comentarios = self._parse_numero((comentarios_el[0].text or "").split()[0])

        publicado = None
        tempo_el = self.driver.find_elements(By.CSS_SELECTOR, "time.live-timestamp")
        if tempo_el:
            publicado = tempo_el[0].get_attribute("datetime")

        if not titulo:
            logger.warning("Reddit: postagem não encontrada em %s", url)
            return None

        m = re.search(r"/comments/([\w]+)", url)
        return {
            "external_id": m.group(1) if m else url,
            "url": url.replace("old.reddit.com", "www.reddit.com"),
            "author": autor,
            "content": titulo,
            "metadata": {
                "plataforma": "reddit",
                "tipo_item": "postagem",
                "score": score,
                "comentarios": comentarios,
            },
            "published_at": publicado,
        }

    def extrair_subreddit(self, nome: str, limite: int) -> List[Dict[str, Any]]:
        url = f"https://old.reddit.com/r/{nome}/"
        self.ir_para(url)

        titulo = self._texto_um(["div.titlebox h1 a", "div.titlebox h1"])
        inscritos = self._parse_numero(self._texto_um(["div.subscribers .number", "span.subscribers-count"]))

        itens = self._coletar_posts(limite)

        cabecalho: Dict[str, Any] = {
            "external_id": f"r-{nome}",
            "url": f"https://www.reddit.com/r/{nome}/",
            "author": f"r/{nome}",
            "content": f"r/{nome}" + (f" ({titulo})" if titulo and titulo != nome else "") + f": {inscritos or 0} inscritos",
            "metadata": {
                "tipo_item": "subreddit",
                "plataforma": "reddit",
                "subreddit": nome,
                "inscritos": inscritos,
            },
            "published_at": None,
        }
        return [cabecalho] + itens

    def extrair_usuario(self, nome: str, limite: int) -> List[Dict[str, Any]]:
        url = f"https://old.reddit.com/user/{nome}/submitted/"
        self.ir_para(url)

        karma = self._texto_um(["div.titlebox .tagline .karma", "span.karma"])
        itens = self._coletar_posts(limite)

        perfil: Dict[str, Any] = {
            "external_id": f"u-{nome}",
            "url": f"https://www.reddit.com/user/{nome}/",
            "author": nome,
            "content": f"u/{nome}" + (f": karma {karma}" if karma else ""),
            "metadata": {
                "tipo_item": "perfil",
                "plataforma": "reddit",
                "usuario": nome,
                "karma": karma,
            },
            "published_at": None,
        }
        return [perfil] + itens

    def extrair_busca(self, termo: str, limite: int) -> List[Dict[str, Any]]:
        url = f"https://old.reddit.com/search/?q={quote(termo)}"
        self.ir_para(url)
        itens = self._coletar_posts(limite)
        if not itens:
            raise RuntimeError(
                f"Reddit: nenhum resultado para a busca {termo!r}. "
                "Verifique se a sessão está conectada na aba Conexões."
            )
        return itens
