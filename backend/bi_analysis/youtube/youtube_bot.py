import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

_URL_VIDEO = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|live/|embed/|v/))([\w-]{11})"
)


def _num_de_texto(texto: str) -> Optional[int]:
    if not texto:
        return None
    texto = texto.strip().lower().replace("\u00a0", " ")
    texto = re.sub(r"[^\d.,kmb\s]", "", texto)
    multiplicador = 1
    for sufixo, valor in (("k", 1_000), ("mil", 1_000), ("m", 1_000_000), ("mi", 1_000_000), ("b", 1_000_000_000)):
        if sufixo in texto:
            multiplicador = valor
            texto = texto.replace(sufixo, "")
            break
    texto = texto.strip().replace(".", "").replace(",", ".")
    try:
        return int(float(texto) * multiplicador)
    except ValueError:
        return None


class YouTubeBot:

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    @staticmethod
    def resolver_alvo(alvo: str) -> Dict[str, str]:
        texto = (alvo or "").strip()
        if not texto:
            raise RuntimeError(
                "YouTube: informe a URL do vídeo ou do canal, o @canal ou um termo de busca."
            )

        video = _URL_VIDEO.search(texto)
        if video:
            return {"tipo": "video", "id": video.group(1), "termo": texto}

        m = re.search(r"youtube\.com/channel/([\w-]+)", texto)
        if m:
            return {"tipo": "canal", "id": m.group(1), "termo": texto}

        m = re.search(r"youtube\.com/(?:@|c/|user/)([\w@.-]+)", texto)
        if m:
            return {"tipo": "canal", "canal": m.group(1).lstrip("@"), "termo": texto}

        if texto.startswith("@") and len(texto) > 2:
            return {"tipo": "canal", "canal": texto[1:], "termo": texto}

        if re.fullmatch(r"UC[\w-]{22}", texto):
            return {"tipo": "canal", "id": texto, "termo": texto}

        return {"tipo": "busca", "termo": texto}

    def ir_para(self, url: str) -> None:
        self.driver.get(url)
        time.sleep(3)

    def _texto_seguro(self, elemento) -> str:
        try:
            return elemento.text.strip()
        except StaleElementReferenceException:
            return ""

    def _extrair_de_video_page(self, url: str) -> Optional[Dict[str, Any]]:
        self.ir_para(url)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-watch-metadata h1 yt-formatted-string"))
            )
        except TimeoutException:
            logger.warning("YouTube: timeout ao carregar página do vídeo %s", url)
            return None

        try:
            titulo_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-watch-metadata h1 yt-formatted-string")
            titulo = self._texto_seguro(titulo_el)
        except NoSuchElementException:
            titulo = ""

        try:
            canal_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-watch-metadata #channel-name a")
            canal = self._texto_seguro(canal_el)
            canal_url = canal_el.get_attribute("href") or ""
        except NoSuchElementException:
            canal = ""
            canal_url = ""

        try:
            views_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-watch-info-text #info span:first-child")
            views_texto = self._texto_seguro(views_el)
            views = _num_de_texto(views_texto)
        except NoSuchElementException:
            views = None

        try:
            data_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-watch-info-text #info span:last-child")
            data_texto = self._texto_seguro(data_el)
        except NoSuchElementException:
            data_texto = ""

        try:
            likes_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-segmented-like-dislike-button-renderer #segmented-like-button yt-button-shape button")
            likes_texto = likes_el.get_attribute("aria-label") or self._texto_seguro(likes_el)
            likes = _num_de_texto(likes_texto)
        except NoSuchElementException:
            likes = None

        try:
            desc_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-text-inline-expander #description-inline-expander yt-formatted-string")
            descricao = self._texto_seguro(desc_el)[:2000]
        except NoSuchElementException:
            descricao = ""

        try:
            comentarios_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-comments-header-renderer #count yt-formatted-string")
            comentarios_texto = self._texto_seguro(comentarios_el)
            comentarios = _num_de_texto(comentarios_texto)
        except NoSuchElementException:
            comentarios = None

        video_id = None
        m = _URL_VIDEO.search(url)
        if m:
            video_id = m.group(1)
        else:
            m2 = re.search(r"[?&]v=([\w-]{11})", self.driver.current_url or "")
            if m2:
                video_id = m2.group(1)

        publicado_em = None
        try:
            data_abs_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-watch-info-text #info-strings yt-formatted-string")
            data_abs_texto = self._texto_seguro(data_abs_el)
        except NoSuchElementException:
            data_abs_texto = data_texto

        thumb = None
        try:
            thumb_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-watch-metadata meta[itemprop='thumbnailUrl']")
            thumb = thumb_el.get_attribute("content")
        except NoSuchElementException:
            pass

        return {
            "id": video_id,
            "titulo": titulo,
            "canal": canal,
            "canal_url": canal_url,
            "publicado_em": data_abs_texto or data_texto,
            "views": views,
            "likes": likes,
            "comentarios": comentarios,
            "descricao": descricao,
            "url": url if url.startswith("http") else f"https://www.youtube.com/watch?v={video_id}",
            "thumb": thumb,
        }

    def extrair_video(self, url: str) -> Optional[Dict[str, Any]]:
        return self._extrair_de_video_page(url)

    def _extrair_cards_busca(self, max_results: int) -> List[Dict[str, Any]]:
        videos: List[Dict[str, Any]] = []
        ids_vistos = set()
        last_position = self.driver.execute_script("return window.pageYOffset;")
        scrolling = True
        while scrolling and len(videos) < max_results:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer")
            except NoSuchElementException:
                break

            for card in cards:
                try:
                    a_el = card.find_element(By.CSS_SELECTOR, "a#video-title")
                    href = a_el.get_attribute("href") or ""
                    titulo = a_el.get_attribute("title") or self._texto_seguro(a_el)
                    video_id_m = re.search(r"[?&]v=([\w-]{11})", href)
                    if not video_id_m:
                        continue
                    vid = video_id_m.group(1)
                    if vid in ids_vistos:
                        continue
                    ids_vistos.add(vid)

                    try:
                        canal_el = card.find_element(By.CSS_SELECTOR, "ytd-channel-name a")
                        canal = self._texto_seguro(canal_el)
                        canal_url = canal_el.get_attribute("href") or ""
                    except NoSuchElementException:
                        canal = ""
                        canal_url = ""

                    try:
                        views_el = card.find_element(By.CSS_SELECTOR, "#metadata-line span:first-child")
                        views = _num_de_texto(self._texto_seguro(views_el))
                    except NoSuchElementException:
                        views = None

                    try:
                        data_el = card.find_element(By.CSS_SELECTOR, "#metadata-line span:last-child")
                        publicado = self._texto_seguro(data_el)
                    except NoSuchElementException:
                        publicado = ""

                    try:
                        dur_el = card.find_element(By.CSS_SELECTOR, "ytd-thumbnail-overlay-time-status-renderer span")
                        duracao = self._texto_seguro(dur_el)
                    except NoSuchElementException:
                        duracao = ""

                    try:
                        thumb_el = card.find_element(By.CSS_SELECTOR, "ytd-thumbnail img")
                        thumb = thumb_el.get_attribute("src")
                    except NoSuchElementException:
                        thumb = None

                    videos.append({
                        "id": vid,
                        "titulo": titulo,
                        "canal": canal,
                        "canal_url": canal_url,
                        "publicado_em": publicado,
                        "views": views,
                        "likes": None,
                        "comentarios": None,
                        "descricao": "",
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "thumb": thumb,
                        "duracao": duracao,
                    })
                except (NoSuchElementException, StaleElementReferenceException):
                    continue

            scroll_attempt = 0
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                current_position = self.driver.execute_script("return window.pageYOffset;")
                if last_position == current_position:
                    scroll_attempt += 1
                    if scroll_attempt > 3:
                        scrolling = False
                        break
                    time.sleep(2)
                else:
                    last_position = current_position
                    break

            if len(videos) >= max_results:
                break

        return videos[:max_results]

    def buscar_videos(self, termo: str, max_results: int = 25) -> List[Dict[str, Any]]:
        from urllib.parse import quote_plus

        url = f"https://www.youtube.com/results?search_query={quote_plus(termo)}&sp=EgIQAQ%253D%253D"
        self.ir_para(url)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer"))
            )
        except TimeoutException:
            logger.warning("YouTube: nenhum resultado de vídeo para %r", termo)
            return []
        return self._extrair_cards_busca(max_results)

    def videos_do_canal(self, canal_url: str, max_results: int = 25) -> List[Dict[str, Any]]:
        url_videos = canal_url.rstrip("/") + "/videos"
        self.ir_para(url_videos)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-rich-item-renderer, ytd-grid-video-renderer"))
            )
        except TimeoutException:
            logger.warning("YouTube: nenhum vídeo encontrado no canal %s", canal_url)
            return []
        return self._extrair_cards_busca(max_results)

    def extrair_canal(self, canal_ref: str) -> Optional[Dict[str, Any]]:
        if canal_ref.startswith("http"):
            url = canal_ref
        else:
            url = f"https://www.youtube.com/@{canal_ref.lstrip('@')}"

        self.ir_para(url)
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-channel-name #text"))
            )
        except TimeoutException:
            logger.warning("YouTube: timeout ao carregar canal %s", url)
            return None

        try:
            titulo_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-channel-name #text")
            titulo = self._texto_seguro(titulo_el)
        except NoSuchElementException:
            titulo = ""

        try:
            inscritos_el = self.driver.find_element(By.CSS_SELECTOR, "#subscriber-count")
            inscritos_texto = self._texto_seguro(inscritos_el)
            inscritos = _num_de_texto(inscritos_texto)
        except NoSuchElementException:
            inscritos = None

        try:
            videos_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-c4-tabbed-header-renderer tp-yt-app-header #videos-count")
            videos_texto = self._texto_seguro(videos_el)
            total_videos = _num_de_texto(videos_texto)
        except NoSuchElementException:
            try:
                videos_tab = self.driver.find_element(By.CSS_SELECTOR, "tp-yt-paper-tab .tp-yt-paper-tab-content")
                videos_texto = self._texto_seguro(videos_tab)
                total_videos = _num_de_texto(videos_texto)
            except NoSuchElementException:
                total_videos = None

        try:
            desc_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-channel-about-metadata-renderer #description")
            descricao = self._texto_seguro(desc_el)[:2000]
        except NoSuchElementException:
            descricao = ""

        try:
            views_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-channel-about-metadata-renderer #view-count")
            views_texto = self._texto_seguro(views_el)
            views_totais = _num_de_texto(views_texto)
        except NoSuchElementException:
            views_totais = None

        try:
            thumb_el = self.driver.find_element(By.CSS_SELECTOR, "ytd-c4-tabbed-header-renderer #avatar img")
            thumb = thumb_el.get_attribute("src")
        except NoSuchElementException:
            thumb = None

        channel_id = None
        try:
            canonical = self.driver.find_element(By.CSS_SELECTOR, "link[rel='canonical']")
            href = canonical.get_attribute("href") or ""
            m = re.search(r"/channel/(UC[\w-]{22})", href)
            if m:
                channel_id = m.group(1)
        except NoSuchElementException:
            pass

        return {
            "id": channel_id or url,
            "titulo": titulo,
            "descricao": descricao,
            "inscritos": inscritos,
            "visualizacoes_totais": views_totais,
            "videos": total_videos,
            "url": url,
            "thumb": thumb,
            "criado_em": None,
        }
