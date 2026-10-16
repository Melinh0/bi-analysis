import json
import logging
import random
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from bi_analysis.browser.stealth import (
    clicar_humano as _clicar_humano_stealth,
    criar_driver,
    dispensar_banner_cookies,
    mover_mouse_humano,
    scroll_humano,
)
from bi_analysis.config.settings import get_project_root

logger = logging.getLogger(__name__)

LOGIN_TIMEOUT = 300
VALIDACAO_TIMEOUT = 15

PLATAFORMAS: Dict[str, Dict[str, Any]] = {
    "instagram": {
        "nome": "Instagram",
        "login_url": "https://www.instagram.com/accounts/login/",
        "home_url": "https://www.instagram.com/",
        "check_selector": 'a[href*="/direct/inbox"]',
        "check_url_bloqueada": ("accounts/login", "accounts/onetap", "/challenge"),
        "inicio_natural": True,
    },
    "tiktok": {
        "nome": "TikTok",
        "login_url": "https://www.tiktok.com/login",
        "home_url": "https://www.tiktok.com/",
        "url_entrada": "https://www.google.com/",
        "check_selector": [
            'header a[href^="/@"]',
            '#header-outer a[href^="/@"]',
            'a[data-e2e="profile-sidebar-avatar"]',
        ],
        "check_ausente": [
            '[data-e2e="login-username"]',
            '[data-e2e="login-qr-code"]',
            '[data-e2e="top-login-btn"]',
        ],
        "check_url_bloqueada": ("tiktok.com/login", "captcha"),
        "inicio_natural": True,
    },
    "reddit": {
        "nome": "Reddit",
        "login_url": "https://www.reddit.com/login/",
        "home_url": "https://www.reddit.com/",
        "check_selector": [
            "#USER_DROPDOWN_ID",
            'faceplate-tracker[noun="user_account"]',
            "shreddit-header-account",
            'header a[href^="/user/"]',
        ],
        "check_ausente": [
            'input[name="username"]',
            "#login-username",
        ],
        "check_url_bloqueada": ("reddit.com/login", "accounts.google", "reddit.com/account"),
        "inicio_natural": True,
    },
    "youtube": {
        "nome": "YouTube",
        "login_url": "https://accounts.google.com/ServiceLogin?service=youtube",
        "home_url": "https://www.youtube.com/",
        "check_selector": "ytd-masthead #avatar-btn",
        "check_url_bloqueada": ("accounts.google", "servicelogin"),
        "inicio_natural": False,
    },
}

_locks: Dict[str, threading.Lock] = {}
_locks_mutex = threading.Lock()


def _lock_de(fonte: str) -> threading.Lock:
    with _locks_mutex:
        if fonte not in _locks:
            _locks[fonte] = threading.Lock()
        return _locks[fonte]


def _dir_perfis() -> Path:
    return get_project_root() / "data" / "browser_profiles"


def _dir_sessoes() -> Path:
    return get_project_root() / "data" / "sessions"


def _arquivo_estado(fonte: str) -> Path:
    return _dir_sessoes() / f"{fonte}.json"


def _perfil_dir(fonte: str) -> Path:
    return _dir_perfis() / fonte


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _espera_humana(min_s: float = 0.5, max_s: float = 2.0) -> None:
    time.sleep(random.uniform(min_s, max_s))


def _ler_estado(fonte: str) -> Dict[str, Any]:
    padrao = {
        "fonte": fonte,
        "status": "disconnected",
        "last_login": None,
        "last_validated": None,
        "error": None,
    }
    arquivo = _arquivo_estado(fonte)
    try:
        if arquivo.is_file():
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            padrao.update(dados)
    except (OSError, json.JSONDecodeError):
        logger.warning("Estado de sessão ilegível para %s; reiniciando como disconnected", fonte)
    return padrao


def _gravar_estado(fonte: str, **campos: Any) -> Dict[str, Any]:
    estado = _ler_estado(fonte)
    estado.update(campos)
    arquivo = _arquivo_estado(fonte)
    try:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        tmp = arquivo.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(arquivo)
    except OSError:
        logger.warning("Falha ao gravar estado da sessão %s", fonte, exc_info=True)
    return estado


def status_todas() -> list[Dict[str, Any]]:
    return [_ler_estado(f) for f in PLATAFORMAS]


def status_de(fonte: str) -> Dict[str, Any]:
    if fonte not in PLATAFORMAS:
        raise ValueError(f"Plataforma desconhecida: {fonte}")
    return _ler_estado(fonte)


def sessao_conectada(fonte: str) -> bool:
    return _ler_estado(fonte).get("status") == "connected"


def _desktop_disponivel() -> bool:
    import os
    import platform

    if platform.system() == "Linux":
        return bool(os.environ.get("DISPLAY"))
    return True


def _criar_driver(headless: bool, perfil: Path):
    return criar_driver(headless=headless, perfil=perfil)


def _encerrar_driver(driver) -> None:
    if driver is None:
        return
    try:
        driver.quit()
    except Exception:
        logger.debug("Não foi possível encerrar o WebDriver", exc_info=True)


def _scroll_humano(driver, vezes: int = 2) -> None:
    scroll_humano(driver, vezes=vezes)


def _clicar_humano(driver, elemento) -> None:
    _clicar_humano_stealth(driver, elemento)


def _digitar_humano(driver, elemento, texto: str) -> None:
    from selenium.webdriver.common.action_chains import ActionChains

    _clicar_humano(driver, elemento)
    _espera_humana(0.3, 0.7)

    for char in texto:
        elemento.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))
        if char == " " and random.random() < 0.1:
            time.sleep(random.uniform(0.2, 0.4))

    _espera_humana(0.2, 0.5)


def _ja_logado(driver, fonte: str) -> bool:
    from selenium.webdriver.common.by import By

    config = PLATAFORMAS[fonte]
    url = (driver.current_url or "").lower()
    for bloqueada in config["check_url_bloqueada"]:
        if bloqueada.lower() in url:
            return False

    ausente = config.get("check_ausente")
    if ausente:
        for seletor in ausente:
            try:
                if driver.find_elements(By.CSS_SELECTOR, seletor):
                    return False
            except Exception:
                continue

    seletores = config["check_selector"]
    if isinstance(seletores, str):
        seletores = [seletores]
    for seletor in seletores:
        try:
            if driver.find_elements(By.CSS_SELECTOR, seletor):
                return True
        except Exception:
            continue
    return False


def _navegar_natural(driver, fonte: str) -> None:
    config = PLATAFORMAS[fonte]

    entrada = config.get("url_entrada")
    if entrada:
        driver.get(entrada)
        _espera_humana(2.0, 4.0)

        try:
            dispensar_banner_cookies(driver)
        except Exception:
            pass

        mover_mouse_humano(driver)
        _scroll_humano(driver, vezes=1)
        return

    driver.get(config["home_url"])
    _espera_humana(2.0, 4.0)

    try:
        dispensar_banner_cookies(driver)
    except Exception:
        pass

    mover_mouse_humano(driver)
    _scroll_humano(driver, vezes=random.randint(1, 2))

    if not _ja_logado(driver, fonte):
        driver.get(config["login_url"])
        _espera_humana(2.5, 4.0)
        mover_mouse_humano(driver)


def login_manual(fonte: str, timeout: int = LOGIN_TIMEOUT) -> Dict[str, Any]:
    if fonte not in PLATAFORMAS:
        raise ValueError(f"Plataforma desconhecida: {fonte}")
    if not _desktop_disponivel():
        _gravar_estado(
            fonte,
            status="failed",
            error="Sem interface gráfica (DISPLAY) para o login manual.",
        )
        return _ler_estado(fonte)

    lock = _lock_de(fonte)
    if not lock.acquire(blocking=False):
        _gravar_estado(fonte, status="logging_in", error=None)
        return _ler_estado(fonte)

    driver = None
    logs_navegador: list[str] = []
    try:
        _gravar_estado(fonte, status="logging_in", error=None)
        config = PLATAFORMAS[fonte]
        driver = _criar_driver(headless=False, perfil=_perfil_dir(fonte))

        _ativar_captura_logs(driver, logs_navegador)

        if config.get("inicio_natural"):
            _navegar_natural(driver, fonte)
        else:
            driver.get(config["login_url"])
            _espera_humana(2.5, 4.0)

        prazo = time.time() + timeout
        estaveis = 0
        ultima_interacao = time.time()
        ultimo_estado_url = ""

        while time.time() < prazo:
            url_atual = driver.current_url or ""

            if _ja_logado(driver, fonte):
                estaveis += 1
                if estaveis >= 2:
                    _scroll_humano(driver, vezes=1)
                    _espera_humana(0.5, 1.0)
                    estado = _gravar_estado(
                        fonte,
                        status="connected",
                        last_login=_agora_iso(),
                        last_validated=_agora_iso(),
                        error=None,
                    )
                    logger.info("%s: login manual concluído.", config["nome"])
                    return estado
            else:
                estaveis = 0

            if url_atual != ultimo_estado_url:
                logger.info("%s: URL atual: %s", config["nome"], url_atual)
                ultimo_estado_url = url_atual

            agora = time.time()
            if agora - ultima_interacao > 12:
                try:
                    _scroll_humano(driver, vezes=1)
                except Exception:
                    pass
                ultima_interacao = agora

            try:
                novos = driver.execute_script("return window.__bi_logs ? window.__bi_logs.splice(0, window.__bi_logs.length) : [];")
                if novos:
                    logs_navegador.extend(novos)
            except Exception:
                pass

            time.sleep(random.uniform(1.5, 2.5))

        erros_recentes = [l for l in logs_navegador[-20:] if "error" in l.lower() or "block" in l.lower() or "denied" in l.lower()]
        detalhe = ""
        if erros_recentes:
            detalhe = " Erros do navegador: " + "; ".join(erros_recentes[:3])

        try:
            for entry in driver.get_log("browser"):
                msg = entry.get("message", "")
                if any(p in msg.lower() for p in ("error", "block", "denied", "failed", "reject")):
                    logs_navegador.append(msg[:300])
        except Exception:
            pass

        estado = _gravar_estado(
            fonte,
            status="failed",
            error=f"Tempo esgotado ({timeout}s) aguardando o login manual.{detalhe}",
        )
        logger.warning("%s: login manual expirou após %ss.", config["nome"], timeout)
        if logs_navegador:
            logger.info("%s: últimos logs do navegador:\n%s", config["nome"], "\n".join(logs_navegador[-30:]))
        return estado
    except Exception as exc:
        logger.exception("%s: falha no login manual", fonte)
        estado = _gravar_estado(fonte, status="failed", error=str(exc) or exc.__class__.__name__)
        return estado
    finally:
        _encerrar_driver(driver)
        lock.release()


def _ativar_captura_logs(driver, logs: list) -> None:
    try:
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

        cap = DesiredCapabilities.CHROME
        cap["goog:loggingPrefs"] = {"browser": "ALL"}
    except Exception:
        pass

    try:
        _coletor_script = """
(function() {
    const origError = console.error;
    const origWarn = console.warn;
    const origLog = console.log;
    console.error = function(...args) {
        origError.apply(console, args);
        window.__bi_logs = window.__bi_logs || [];
        window.__bi_logs.push('ERROR: ' + args.join(' '));
    };
    console.warn = function(...args) {
        origWarn.apply(console, args);
        window.__bi_logs = window.__bi_logs || [];
        window.__bi_logs.push('WARN: ' + args.join(' '));
    };
    window.addEventListener('error', function(e) {
        window.__bi_logs = window.__bi_logs || [];
        window.__bi_logs.push('JS_ERROR: ' + (e.message || '') + ' @ ' + (e.filename || ''));
    });
    window.addEventListener('unhandledrejection', function(e) {
        window.__bi_logs = window.__bi_logs || [];
        window.__bi_logs.push('PROMISE_REJECT: ' + String(e.reason || ''));
    });
})();
"""
        driver.execute_script(_coletor_script)
    except Exception:
        logger.debug("Falha ao injetar coletor de logs", exc_info=True)


def _validar_com_driver(fonte: str, headless: bool, timeout: int) -> bool:
    config = PLATAFORMAS[fonte]
    driver = _criar_driver(headless=headless, perfil=_perfil_dir(fonte))
    try:
        driver.get(config["home_url"])
        _espera_humana(1.0, 2.0)

        try:
            dispensar_banner_cookies(driver)
        except Exception:
            pass

        prazo = time.time() + timeout
        while time.time() < prazo:
            if _ja_logado(driver, fonte):
                return True
            time.sleep(2)
        return False
    finally:
        _encerrar_driver(driver)


def validar(fonte: str, timeout: int = VALIDACAO_TIMEOUT) -> bool:
    if fonte not in PLATAFORMAS:
        raise ValueError(f"Plataforma desconhecida: {fonte}")

    estado = _ler_estado(fonte)
    if estado.get("status") == "logging_in":
        return False

    lock = _lock_de(fonte)
    if not lock.acquire(blocking=False):
        return estado.get("status") == "connected"

    try:
        conectado = _validar_com_driver(fonte, headless=True, timeout=timeout)

        if not conectado and _desktop_disponivel():
            logger.info("%s: validação em segundo plano não confirmou; tentando com janela visível.", PLATAFORMAS[fonte]["nome"])
            conectado = _validar_com_driver(fonte, headless=False, timeout=timeout)

        if conectado:
            _gravar_estado(fonte, last_validated=_agora_iso(), error=None)
            return True

        _gravar_estado(
            fonte,
            status="disconnected",
            error="Sessão expirada ou inválida. Conecte novamente na aba Conexões.",
        )
        return False
    except Exception as exc:
        logger.warning("%s: erro ao validar sessão: %s", fonte, exc)
        return estado.get("status") == "connected"
    finally:
        lock.release()


def logout(fonte: str) -> Dict[str, Any]:
    if fonte not in PLATAFORMAS:
        raise ValueError(f"Plataforma desconhecida: {fonte}")

    lock = _lock_de(fonte)
    with lock:
        perfil = _perfil_dir(fonte)
        try:
            if perfil.is_dir():
                shutil.rmtree(perfil, ignore_errors=True)
        except OSError:
            logger.warning("Falha ao remover perfil do navegador %s", fonte, exc_info=True)
        estado = _gravar_estado(
            fonte,
            status="disconnected",
            last_login=None,
            last_validated=None,
            error=None,
        )
        logger.info("%s: sessão desconectada.", PLATAFORMAS[fonte]["nome"])
        return estado
