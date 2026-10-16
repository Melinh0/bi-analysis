import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from bi_analysis.database.session import get_db_session
from bi_analysis.database.models import ExtractionJob, ExtractedItem, SourceType, ContentType
from bi_analysis.config.settings import get_project_root
from bi_analysis.sessions import manager as session_manager

logger = logging.getLogger(__name__)


def run_extraction_job(job_id: int) -> None:
    db = get_db_session()
    try:
        job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        try:
            if job.source_type == SourceType.INSTAGRAM:
                items = extract_instagram(job.content_type, job.query_params or {})
            elif job.source_type == SourceType.TIKTOK:
                items = extract_tiktok(job.content_type, job.query_params or {})
            elif job.source_type == SourceType.YOUTUBE:
                items = extract_youtube(job.content_type, job.query_params or {})
            elif job.source_type == SourceType.REDDIT:
                items = extract_reddit(job.content_type, job.query_params or {})
            elif job.source_type == SourceType.WIKIPEDIA:
                items = extract_wikipedia(job.content_type, job.query_params or {})
            elif job.source_type == SourceType.KNEWIN:
                raise ValueError("A fonte Knewin foi removida da ferramenta. Use Instagram ou TikTok.")
            elif job.source_type == SourceType.TWITTER:
                raise ValueError("A fonte Twitter/X foi removida da ferramenta. Use Instagram ou TikTok.")
            else:
                raise ValueError(f"Fonte não suportada: {job.source_type}")

            job.items_extracted = len(items)

            stored = store_items(db, job_id, job.source_type, job.content_type, items)
            job.items_stored = stored
            job.status = "completed"
            job.completed_at = datetime.utcnow()

        except Exception as e:
            logger.exception(f"Extraction job {job_id} failed")
            job.status = "failed"
            job.error_message = str(e) or e.__class__.__name__
            job.completed_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()






def _desktop_disponivel() -> bool:

    import os
    import platform

    if platform.system() == "Linux":
        return bool(os.environ.get("DISPLAY"))
    return True


def _create_driver(headless: bool = True, user_data_dir: Optional[Path] = None):
    from bi_analysis.browser.stealth import criar_driver

    if user_data_dir is None:
        import tempfile

        user_data_dir = Path(tempfile.mkdtemp(prefix="bi_profile_"))
    return criar_driver(headless=headless, perfil=Path(user_data_dir))


def _quit_driver(driver) -> None:

    if driver is None:
        return
    try:
        driver.quit()
    except Exception:
        logger.debug("Não foi possível encerrar o WebDriver", exc_info=True)


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _perfil_dir(fonte: str) -> Path:
    return get_project_root() / "data" / "browser_profiles" / fonte


def _garantir_sessao(fonte: str, rotulo: str) -> None:
    """Garante que a plataforma tem sessão conectada; valida automaticamente antes de falhar."""
    if session_manager.sessao_conectada(fonte):
        return
    if session_manager.validar(fonte):
        return

    estado = session_manager.status_de(fonte)
    detalhe = estado.get("error") or ""
    raise RuntimeError(
        f"{rotulo}: nenhuma sessão conectada. "
        + (f"Detalhe: {detalhe} " if detalhe else "")
        + "Vá para a aba Conexões, clique em Conectar e faça o login manual na janela do navegador."
    )


def _dispensar_popups(driver) -> None:

    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.by import By

    for xpath in (
        "//button[contains(text(), 'Agora não')]",
        "//div[contains(text(), 'Agora não')]",
        "//button[contains(text(), 'Not now')]",
    ):
        try:
            driver.find_element(By.XPATH, xpath).click()
            time.sleep(1)
        except NoSuchElementException:
            continue






def _extrair_posts_instagram_api(
    alvo: str,
    params: Dict[str, Any],
    headless: bool,
) -> List[Dict[str, Any]]:
    from bi_analysis.instagram.api.api_bot import APIBot

    num_posts = _to_int(params.get("num_posts"), 50)
    bot = APIBot(
        perfil=str(_perfil_dir("instagram")),
        manual_login=False,
        headless=headless,
    )
    posts = bot.extrair_posts_instagram_api(link=alvo, num_posts=num_posts)

    if not isinstance(posts, list):
        raise RuntimeError(f"Instagram: extração de posts falhou — {posts}")

    items = []
    for post in posts:
        if not post:
            continue
        items.append({
            "external_id": post.get("code"),
            "url": post.get("link"),
            "author": None,
            "content": post.get("Texto:") or post.get("link") or "",
            "metadata": {
                "curtidas": post.get("Curtidas"),
                "comentarios": post.get("Comentários"),
                "visualizacoes": post.get("visualizações"),
                "url_imagem": post.get("url_imagem"),
            },
            "published_at": None,
        })
    return items


def extract_instagram(content_type: ContentType, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    from bi_analysis.instagram.instagram_bot import instagram_bot

    if content_type == ContentType.COMMENT:
        alvo = params.get("post_url")
        if not alvo:
            raise ValueError("Instagram: informe a URL da postagem (post_url).")
    elif content_type in (ContentType.POST, ContentType.REEL):
        alvo = params.get("profile_url")
        if not alvo:
            raise ValueError("Instagram: informe a URL do perfil (profile_url).")
    else:
        raise ValueError(f"Instagram: tipo de conteúdo não suportado: {content_type.value}")

    _garantir_sessao("instagram", "Instagram")

    headless = not _desktop_disponivel()
    if params.get("headless") is not None:
        headless = bool(params.get("headless"))

    if content_type == ContentType.POST:
        return _extrair_posts_instagram_api(alvo, params, headless)

    items = []
    driver = _create_driver(headless=headless, user_data_dir=_perfil_dir("instagram"))
    try:
        bot = instagram_bot(driver)

        bot.ir_para_post(alvo)
        time.sleep(3)
        _dispensar_popups(driver)

        if content_type == ContentType.COMMENT:
            max_clicks = _to_int(params.get("max_clicks"), 10)
            bot.carregar_mais_comentarios(limit=max_clicks)
            for comentario in bot.extrair_comentarios():
                if not comentario:
                    continue
                items.append({
                    "external_id": comentario.get("Usuário"),
                    "url": alvo,
                    "author": comentario.get("Usuário"),
                    "content": comentario.get("Texto", ""),
                    "metadata": {
                        "data": comentario.get("Data"),
                        "curtidas": comentario.get("Curtidas"),
                        "respostas": comentario.get("Respostas"),
                    },
                    "published_at": None,
                })
        else:
            num_reels = _to_int(params.get("num_reels"), 50)
            reels = bot.scroll_reels(limit=num_reels) or []
            for link, curtidas, comentarios, views in reels:
                if not link:
                    continue
                items.append({
                    "external_id": link,
                    "url": link,
                    "author": None,
                    "content": link,
                    "metadata": {
                        "curtidas": curtidas,
                        "comentarios": comentarios,
                        "visualizacoes": views,
                    },
                    "published_at": None,
                })
    finally:
        _quit_driver(driver)

    return items






def extract_tiktok(content_type: ContentType, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    from bi_analysis.tiktok.tiktok_bot import TikTokBot

    if content_type not in (ContentType.VIDEO, ContentType.PROFILE, ContentType.HASHTAG):
        raise ValueError(
            f"TikTok: tipo de conteúdo não suportado: {content_type.value}. "
            "Use vídeo (URL), perfil (@usuário) ou hashtag."
        )

    alvo = params.get("alvo") or params.get("query") or params.get("termo") or params.get("url")
    estado = TikTokBot.resolver_alvo(alvo)
    limite = _to_int(params.get("limite", params.get("num_videos")), 25)

    _garantir_sessao("tiktok", "TikTok")

    headless = not _desktop_disponivel()
    if params.get("headless") is not None:
        headless = bool(params.get("headless"))

    items: List[Dict[str, Any]] = []
    driver = _create_driver(headless=headless, user_data_dir=_perfil_dir("tiktok"))
    try:
        bot = TikTokBot(driver)

        if content_type == ContentType.VIDEO:
            if estado["tipo"] != "video":
                raise RuntimeError(
                    "TikTok: para extrair um vídeo, informe a URL dele "
                    "(tiktok.com/@usuario/video/...)."
                )
            url = f"https://www.tiktok.com/@{estado['usuario']}/video/{estado['id']}"
            video = bot.extrair_video(url)
            if not video:
                raise RuntimeError(f"TikTok: vídeo não encontrado ({estado['id']}).")
            items.append(video)

        elif content_type == ContentType.PROFILE:
            if estado["tipo"] != "perfil":
                raise RuntimeError(
                    "TikTok: para extrair um perfil, informe a URL ou @usuário "
                    "(tiktok.com/@usuario ou @usuario)."
                )
            items.extend(bot.extrair_perfil(estado["usuario"], limite))

        elif content_type == ContentType.HASHTAG:
            if estado["tipo"] == "hashtag":
                items.extend(bot.extrair_hashtag(estado["tag"], limite))
            elif estado["tipo"] == "busca":
                items.extend(bot.extrair_busca(estado["termo"], limite))
            else:
                raise RuntimeError(
                    "TikTok: para hashtag, informe #hashtag ou a URL tag/... "
                    "(ou um termo de busca livre)."
                )
    finally:
        _quit_driver(driver)

    return items


def _data_de(valor: Any) -> Optional[datetime]:

    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(float(valor), tz=timezone.utc).replace(tzinfo=None)
    texto = str(valor).strip()
    if texto.isdigit():
        return datetime.fromtimestamp(float(int(texto)), tz=timezone.utc).replace(tzinfo=None)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
        return datetime.strptime(texto, "%Y-%m-%d")
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None






def _item_video_youtube(video: Dict[str, Any]) -> Dict[str, Any]:
    publicado = video.get("publicado_em")
    return {
        "external_id": video.get("id"),
        "url": video.get("url"),
        "author": video.get("canal"),
        "content": video.get("titulo") or video.get("url") or "",
        "metadata": {
            "tipo_item": "post",
            "plataforma": "youtube",
            "titulo": video.get("titulo"),
            "descricao": video.get("descricao"),
            "imagem": video.get("thumb"),
            "duracao": video.get("duracao"),
            "curtidas": video.get("likes"),
            "comentarios": video.get("comentarios"),
            "visualizacoes": video.get("views"),
            "publicado_em": publicado,
        },
        "published_at": _data_de(publicado),
    }


def _item_canal_youtube(canal: Dict[str, Any]) -> Dict[str, Any]:
    criado = canal.get("criado_em")
    return {
        "external_id": canal.get("id"),
        "url": canal.get("url"),
        "author": canal.get("titulo"),
        "content": (
            f"Canal {canal.get('titulo')}: {canal.get('inscritos', 0):,} inscritos, "
            f"{canal.get('visualizacoes_totais', 0):,} visualizações totais, "
            f"{canal.get('videos', 0):,} vídeos."
        ).replace(",", "."),
        "metadata": {
            "tipo_item": "perfil",
            "plataforma": "youtube",
            "titulo": canal.get("titulo"),
            "descricao": canal.get("descricao"),
            "imagem": canal.get("thumb"),
            "pais": canal.get("pais"),
            "inscritos": canal.get("inscritos"),
            "visualizacoes_totais": canal.get("visualizacoes_totais"),
            "videos": canal.get("videos"),
            "publicado_em": criado,
        },
        "published_at": _data_de(criado),
    }


def extract_youtube(content_type: ContentType, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    from bi_analysis.youtube.youtube_bot import YouTubeBot

    alvo = params.get("alvo") or params.get("query") or params.get("termo") or params.get("url")
    estado = YouTubeBot.resolver_alvo(alvo)
    limite = _to_int(params.get("limite", params.get("num_videos")), 25)

    _garantir_sessao("youtube", "YouTube")

    headless = not _desktop_disponivel()
    if params.get("headless") is not None:
        headless = bool(params.get("headless"))

    items = []
    driver = _create_driver(headless=headless, user_data_dir=_perfil_dir("youtube"))
    try:
        bot = YouTubeBot(driver)

        if content_type == ContentType.VIDEO:
            if estado["tipo"] != "video":
                raise RuntimeError(
                    "YouTube: para analisar um vídeo, informe a URL dele "
                    "(youtu.be/... ou youtube.com/watch?v=...)."
                )
            video_url = f"https://www.youtube.com/watch?v={estado['id']}"
            video = bot.extrair_video(video_url)
            if not video:
                raise RuntimeError(f"YouTube: vídeo não encontrado ({estado['id']}).")
            items.append(_item_video_youtube(video))

        elif content_type == ContentType.CHANNEL:
            canal_ref = estado.get("id") or estado.get("canal") or estado["termo"]
            canal = bot.extrair_canal(canal_ref)
            if not canal:
                raise RuntimeError(f"YouTube: canal não encontrado ({alvo!r}).")
            items.append(_item_canal_youtube(canal))

        elif content_type == ContentType.SEARCH:
            if estado["tipo"] == "video":
                video_url = f"https://www.youtube.com/watch?v={estado['id']}"
                video = bot.extrair_video(video_url)
                if not video:
                    raise RuntimeError(f"YouTube: vídeo não encontrado ({estado['id']}).")
                items.append(_item_video_youtube(video))
            elif estado["tipo"] == "canal":
                canal_ref = estado.get("id") or estado.get("canal")
                canal = bot.extrair_canal(canal_ref)
                if not canal:
                    raise RuntimeError(f"YouTube: canal não encontrado ({alvo!r}).")
                videos = bot.videos_do_canal(canal["url"], limite)
                items.extend(_item_video_youtube(v) for v in videos)
            else:
                videos = bot.buscar_videos(estado["termo"], limite)
                items.extend(_item_video_youtube(v) for v in videos)
        else:
            raise ValueError(f"YouTube: tipo de conteúdo não suportado: {content_type.value}")
    finally:
        _quit_driver(driver)

    return items






def extract_reddit(content_type: ContentType, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    from bi_analysis.reddit.reddit_bot import RedditBot

    if content_type != ContentType.SUBMISSION:
        raise ValueError(f"Reddit: tipo de conteúdo não suportado: {content_type.value}")

    alvo = params.get("alvo") or params.get("query") or params.get("termo") or params.get("url")
    estado = RedditBot.resolver_alvo(alvo)
    limite = _to_int(params.get("limite"), 25)

    _garantir_sessao("reddit", "Reddit")

    headless = not _desktop_disponivel()
    if params.get("headless") is not None:
        headless = bool(params.get("headless"))

    driver = _create_driver(headless=headless, user_data_dir=_perfil_dir("reddit"))
    try:
        bot = RedditBot(driver)

        if estado["tipo"] == "postagem":
            url = f"https://www.reddit.com/r/{estado['subreddit']}/comments/{estado['id']}/"
            post = bot.extrair_postagem(url)
            if not post:
                raise RuntimeError(f"Reddit: postagem não encontrada ({estado['id']}).")
            return [post]

        if estado["tipo"] == "subreddit":
            return bot.extrair_subreddit(estado["nome"], limite)

        if estado["tipo"] == "usuario":
            return bot.extrair_usuario(estado["nome"], limite)

        return bot.extrair_busca(estado["termo"], limite)
    finally:
        _quit_driver(driver)






def extract_wikipedia(content_type: ContentType, params: Dict[str, Any]) -> List[Dict[str, Any]]:

    from bi_analysis.wikipedia.api import WikipediaAPI, WikipediaAPIError

    if content_type != ContentType.TOPIC:
        raise ValueError(f"Wikipédia: tipo de conteúdo não suportado: {content_type.value}")

    alvo = (
        params.get("alvo")
        or params.get("query")
        or params.get("termo")
        or params.get("titulo")
        or params.get("url")
    )
    estado = WikipediaAPI.resolver_alvo(alvo)
    api = WikipediaAPI(idioma=params.get("idioma") or estado["idioma"])
    dias = _to_int(params.get("dias"), 30)
    serie = api.pageviews(estado["titulo"], dias)
    if not serie:
        raise WikipediaAPIError(
            f"Wikipédia: sem dados de visualizações para '{estado['titulo']}'."
        )

    itens = []
    for ponto in serie:
        try:
            dia = datetime.strptime(str(ponto.get("timestamp"))[:8], "%Y%m%d").date()
        except ValueError:
            continue
        visualizacoes = ponto.get("views") or 0
        titulo = estado["titulo"]
        itens.append({
            "external_id": f"{titulo}-{dia:%Y%m%d}",
            "url": f"https://{api.idioma}.wikipedia.org/wiki/{titulo.replace(' ', '_')}",
            "author": "Wikipédia",
            "content": (
                f"{titulo}: {visualizacoes:,} visualizações em {dia:%d/%m/%Y}"
            ).replace(",", "."),
            "metadata": {
                "tipo_item": "serie_diaria",
                "plataforma": "wikipedia",
                "titulo": f"{titulo} ({dia:%d/%m/%Y})",
                "visualizacoes": visualizacoes,
                "publicado_em": dia.isoformat(),
                "data": dia.isoformat(),
            },
            "published_at": datetime(dia.year, dia.month, dia.day),
        })
    return itens


def store_items(
    db,
    job_id: int,
    source_type: SourceType,
    content_type: ContentType,
    items: List[Dict[str, Any]],
) -> int:
    stored = 0
    for item_data in items:
        if not item_data.get("content"):
            continue

        item = ExtractedItem(
            job_id=job_id,
            source_type=source_type,
            content_type=content_type,
            external_id=item_data.get("external_id"),
            url=item_data.get("url"),
            author=item_data.get("author"),
            author_id=item_data.get("author_id"),
            content=item_data.get("content"),
            extra_data=item_data.get("metadata"),
            published_at=item_data.get("published_at"),
        )
        db.add(item)
        stored += 1

    db.commit()
    return stored
