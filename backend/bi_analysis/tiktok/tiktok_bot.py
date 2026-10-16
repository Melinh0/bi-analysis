import logging
import random
import re
import time
from typing import Any, Dict, List, Optional

from bi_analysis.browser.stealth import (
    dispensar_banner_cookies,
    esperar_carregamento,
    mover_mouse_humano,
    scroll_humano,
)

logger = logging.getLogger(__name__)


class TikTokBot:
    def __init__(self, driver) -> None:
        self.driver = driver

    @staticmethod
    def resolver_alvo(alvo: str) -> Dict[str, Any]:
        texto = (alvo or "").strip()
        if not texto:
            raise ValueError("TikTok: informe um alvo (URL, @usuário, #hashtag ou termo).")

        m = re.search(r"tiktok\.com/@([\w.\-]+)/video/(\d+)", texto)
        if m:
            return {"tipo": "video", "usuario": m.group(1), "id": m.group(2)}

        m = re.search(r"tiktok\.com/@([\w.\-]+)", texto)
        if m:
            return {"tipo": "perfil", "usuario": m.group(1), "termo": texto}

        m = re.search(r"tiktok\.com/tag/([\w%\-]+)", texto)
        if m:
            return {"tipo": "hashtag", "tag": m.group(1), "termo": texto}

        if texto.startswith("@") and len(texto) > 1:
            return {"tipo": "perfil", "usuario": texto[1:].lstrip("@"), "termo": texto}

        if texto.startswith("#") and len(texto) > 1:
            return {"tipo": "hashtag", "tag": texto[1:], "termo": texto}

        return {"tipo": "busca", "termo": texto}

    def _detectar_bloqueio(self) -> None:
        url = (self.driver.current_url or "").lower()
        if "captcha" in url or "/verify" in url or "security-check" in url:
            raise RuntimeError(
                "TikTok: página de verificação (anti-bot) detectada. "
                "Desconecte e reconecte a sessão na aba Conexões pela janela visível "
                "e conclua a verificação manualmente."
            )

    def ir_para(self, url: str) -> None:
        try:
            self.driver.get("https://www.tiktok.com/")
            esperar_carregamento(self.driver)
            time.sleep(random.uniform(1.5, 2.5))

            try:
                dispensar_banner_cookies(self.driver)
            except Exception:
                pass

            mover_mouse_humano(self.driver)
            scroll_humano(self.driver, vezes=random.randint(1, 2))
        except RuntimeError:
            raise
        except Exception:
            logger.debug("Falha na navegação natural até a home do TikTok", exc_info=True)

        self.driver.get(url)
        esperar_carregamento(self.driver)
        self._detectar_bloqueio()
        time.sleep(random.uniform(1.5, 3.0))

        try:
            dispensar_banner_cookies(self.driver)
        except Exception:
            pass

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

    def _scroll_carregar(self, vezes: int = 6) -> None:
        for _ in range(vezes):
            if random.random() < 0.5:
                scroll_humano(self.driver, vezes=1)
            else:
                self.driver.execute_script(
                    "window.scrollBy({top: window.innerHeight * 0.85, behavior: 'smooth'})"
                )
                time.sleep(random.uniform(1.0, 2.0))
            if random.random() < 0.3:
                mover_mouse_humano(self.driver)
        self._detectar_bloqueio()

    @staticmethod
    def _parse_numero(texto: Optional[str]) -> Optional[int]:
        if not texto:
            return None
        t = texto.strip().lower().replace(".", "").replace(",", "")
        mult = 1
        for sufixo, valor in (("k", 1_000), ("mil", 1_000), ("m", 1_000_000), ("mi", 1_000_000), ("b", 1_000_000_000)):
            if t.endswith(sufixo):
                mult = valor
                t = t[: -len(sufixo)]
                break
        try:
            return int(float(t) * mult)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _item_de_video(href: str, views: Optional[str] = None) -> Optional[Dict[str, Any]]:
        m = re.search(r"/@([\w.\-]+)/video/(\d+)", href)
        if not m:
            return None
        usuario, video_id = m.group(1), m.group(2)
        url = f"https://www.tiktok.com/@{usuario}/video/{video_id}"
        return {
            "external_id": video_id,
            "url": url,
            "author": usuario,
            "content": f"Vídeo de @{usuario} ({video_id})",
            "metadata": {
                "plataforma": "tiktok",
                "usuario": usuario,
                "visualizacoes": TikTokBot._parse_numero(views),
            },
            "published_at": None,
        }

    def _coletar_videos_pagina(self, limite: int) -> List[Dict[str, Any]]:
        from selenium.webdriver.common.by import By

        vistos = set()
        itens: List[Dict[str, Any]] = []
        tentativas = 0

        while len(itens) < limite and tentativas < 8:
            tentativas += 1
            links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/video/"]')
            for link in links:
                if len(itens) >= limite:
                    break
                href = link.get_attribute("href") or ""
                m = re.search(r"/video/(\d+)", href)
                if not m or m.group(1) in vistos:
                    continue

                views = None
                try:
                    container = link
                    for _ in range(4):
                        container = container.find_element(By.XPATH, "..")
                        vis = container.find_elements(By.CSS_SELECTOR, '[data-e2e="video-views"]')
                        if vis:
                            views = vis[0].text
                            break
                except Exception:
                    pass

                item = self._item_de_video(href, views)
                if item:
                    vistos.add(m.group(1))
                    itens.append(item)

            if len(itens) < limite:
                self._scroll_carregar(vezes=3)

        return itens[:limite]

    def extrair_video(self, url: str) -> Optional[Dict[str, Any]]:
        self.ir_para(url)

        desc = self._texto_um([
            '[data-e2e="video-desc"]',
            'h1[data-e2e="video-desc"]',
            '[data-e2e="browse-video-desc"]',
        ])
        autor_unique = self._texto_um(['[data-e2e="video-author-uniqueid"]'])
        autor_nome = self._texto_um(['[data-e2e="video-author-nickname"]'])
        autor = autor_unique or autor_nome
        likes = self._texto_um(['[data-e2e="browse-like-count"]', '[data-e2e="like-count"]'])
        comentarios = self._texto_um(['[data-e2e="browse-comment-count"]', '[data-e2e="comment-count"]'])
        shares = self._texto_um(['[data-e2e="browse-share-count"]', '[data-e2e="share-count"]'])
        views = self._texto_um(['[data-e2e="video-views"]'])

        m = re.search(r"/video/(\d+)", url)
        video_id = m.group(1) if m else None

        if not desc and not views and not likes:
            logger.warning("TikTok: nenhum dado do vídeo encontrado em %s (seletores mudaram?)", url)
            return None

        return {
            "external_id": video_id,
            "url": url,
            "author": autor,
            "content": desc or url,
            "metadata": {
                "plataforma": "tiktok",
                "autor_nome": autor_nome,
                "autor_unique": autor_unique,
                "curtidas": self._parse_numero(likes),
                "comentarios": self._parse_numero(comentarios),
                "shares": self._parse_numero(shares),
                "visualizacoes": self._parse_numero(views),
            },
            "published_at": None,
        }

    def extrair_perfil(self, usuario: str, limite: int) -> List[Dict[str, Any]]:
        url = f"https://www.tiktok.com/@{usuario}"
        self.ir_para(url)

        nome = self._texto_um(['[data-e2e="user-subtitle"]', '[data-e2e="user-title"]'])
        seguidores = self._texto_um(['[data-e2e="user-followers"]'])
        likes = self._texto_um(['[data-e2e="user-likes"]'])

        itens = self._coletar_videos_pagina(limite)

        perfil: Dict[str, Any] = {
            "external_id": usuario,
            "url": url,
            "author": usuario,
            "content": (
                f"@{usuario}" + (f" ({nome})" if nome and nome != usuario else "")
                + f": {self._parse_numero(seguidores) or 0} seguidores"
            ).replace(".", "."),
            "metadata": {
                "tipo_item": "perfil",
                "plataforma": "tiktok",
                "usuario": usuario,
                "nome": nome,
                "seguidores": self._parse_numero(seguidores),
                "curtidas_total": self._parse_numero(likes),
            },
            "published_at": None,
        }
        return [perfil] + itens

    def extrair_hashtag(self, tag: str, limite: int) -> List[Dict[str, Any]]:
        url = f"https://www.tiktok.com/tag/{tag}"
        self.ir_para(url)

        video_count = self._texto_um(['[data-e2e="challenge-video-count"]'])
        views_total = self._texto_um(['[data-e2e="challenge-video-views"]'])

        itens = self._coletar_videos_pagina(limite)

        cabecalho: Dict[str, Any] = {
            "external_id": f"tag-{tag}",
            "url": url,
            "author": f"#{tag}",
            "content": f"Hashtag #{tag}: {video_count or '?'} vídeos, {views_total or '?'} visualizações",
            "metadata": {
                "tipo_item": "hashtag",
                "plataforma": "tiktok",
                "tag": tag,
                "total_videos": video_count,
                "visualizacoes_total": self._parse_numero(views_total),
            },
            "published_at": None,
        }
        return [cabecalho] + itens

    def extrair_busca(self, termo: str, limite: int) -> List[Dict[str, Any]]:
        from urllib.parse import quote

        url = f"https://www.tiktok.com/search?q={quote(termo)}"
        self.ir_para(url)
        itens = self._coletar_videos_pagina(limite)
        if not itens:
            raise RuntimeError(
                f"TikTok: nenhum vídeo encontrado para a busca {termo!r}. "
                "Verifique se a sessão está conectada na aba Conexões."
            )
        return itens
