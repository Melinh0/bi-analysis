import logging
import random
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_ANTI_DETECT_JS = """
(() => {
    const origFunctionToString = Function.prototype.toString;
    const spoofedFns = new Set();
    Function.prototype.toString = function() {
        if (spoofedFns.has(this)) {
            return 'function ' + (this.name || '') + '() { [native code] }';
        }
        return origFunctionToString.call(this);
    };

    const defineNative = (obj, prop, get) => {
        Object.defineProperty(obj, prop, { get, configurable: true });
        const desc = Object.getOwnPropertyDescriptor(obj, prop);
        if (desc && desc.get) spoofedFns.add(desc.get);
    };

    const newProto = navigator.__proto__;
    delete newProto.webdriver;

    defineNative(navigator, 'webdriver', () => undefined);

    defineNative(navigator, 'languages', () => ['pt-BR', 'pt', 'en-US', 'en']);
    defineNative(navigator, 'language', () => 'pt-BR');

    defineNative(navigator, 'plugins', () => {
        const arr = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
        ];
        arr.item = (i) => arr[i] || null;
        arr.namedItem = (n) => arr.find(p => p.name === n) || null;
        arr.refresh = () => {};
        return arr;
    });

    defineNative(navigator, 'hardwareConcurrency', () => 8);
    defineNative(navigator, 'deviceMemory', () => 8);
    defineNative(navigator, 'maxTouchPoints', () => 0);
    defineNative(navigator, 'pdfViewerEnabled', () => true);

    if (!window.chrome) {
        window.chrome = {};
    }
    window.chrome.runtime = {
        connect: () => {},
        sendMessage: () => {},
        id: undefined,
    };
    window.chrome.csi = () => ({
        onloadT: Date.now(),
        pageT: Date.now(),
        startE: Date.now(),
        tran: 15,
    });
    window.chrome.loadTimes = () => ({
        requestTime: Date.now() / 1000,
        startLoadTime: Date.now() / 1000,
        commitLoadTime: Date.now() / 1000,
        finishDocumentLoadTime: Date.now() / 1000,
        finishLoadTime: Date.now() / 1000,
        firstPaintTime: Date.now() / 1000,
        firstPaintAfterLoadTime: 0,
        navigationType: 'Other',
        wasFetchedViaSpdy: false,
        wasNpnNegotiated: false,
        npnNegotiatedProtocol: 'unknown',
        wasAlternateProtocolAvailable: false,
        connectionInfo: 'http/1.1',
    });
    spoofedFns.add(window.chrome.csi);
    spoofedFns.add(window.chrome.loadTimes);

    const originalQuery = window.navigator.permissions.query;
    const patchedQuery = (parameters) => {
        if (parameters && parameters.name === 'notifications') {
            return Promise.resolve({ state: 'prompt', status: 'prompt' });
        }
        return originalQuery(parameters);
    };
    spoofedFns.add(patchedQuery);
    window.navigator.permissions.query = patchedQuery;

    const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
    const patchedGetParameter = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return originalGetParameter.call(this, parameter);
    };
    spoofedFns.add(patchedGetParameter);
    WebGLRenderingContext.prototype.getParameter = patchedGetParameter;

    const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
    const patchedGetParameter2 = function(parameter) {
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel Iris OpenGL Engine';
        return originalGetParameter2.call(this, parameter);
    };
    spoofedFns.add(patchedGetParameter2);
    WebGL2RenderingContext.prototype.getParameter = patchedGetParameter2;

    const origCanvasToDataURL = HTMLCanvasElement.prototype.toDataURL;
    const patchedToDataURL = function(type) {
        if (type === 'image/png' && this.width === 16 && this.height === 16) {
            const ctx = this.getContext('2d');
            if (ctx) {
                const origFill = ctx.fillStyle;
                ctx.fillStyle = 'rgba(100, 100, 100, 0.8)';
                ctx.fillRect(0, 0, 16, 16);
                ctx.fillStyle = origFill;
            }
        }
        return origCanvasToDataURL.call(this, type);
    };
    spoofedFns.add(patchedToDataURL);
    HTMLCanvasElement.prototype.toDataURL = patchedToDataURL;

    defineNative(screen, 'colorDepth', () => 24);
    defineNative(screen, 'pixelDepth', () => 24);

    if (typeof Notification !== 'undefined') {
        defineNative(Notification, 'permission', () => 'default');
    }
})();
"""


def criar_driver(headless: bool, perfil: Path):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    options = webdriver.ChromeOptions()

    options.add_argument("--start-maximized")
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=pt-BR,pt")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")

    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)

    perfil = Path(perfil)
    perfil.mkdir(parents=True, exist_ok=True)
    options.add_argument(f"--user-data-dir={perfil}")

    driver = webdriver.Chrome(service=Service(), options=options)

    injetar_anti_detectacao(driver)

    return driver


def injetar_anti_detectacao(driver) -> None:
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": _ANTI_DETECT_JS},
        )
    except Exception:
        logger.debug("Falha ao injetar script anti-detecção via CDP", exc_info=True)

    try:
        identidade = driver.execute_script(
            "return {ua: navigator.userAgent, plataforma: navigator.platform};"
        ) or {}
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": identidade.get("ua", ""),
                "acceptLanguage": "pt-BR,pt,en-US,en",
                "platform": identidade.get("plataforma", "Win32"),
            },
        )
    except Exception:
        logger.debug("Falha ao alinhar User-Agent via CDP", exc_info=True)

    try:
        driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "America/Sao_Paulo"})
    except Exception:
        pass

    try:
        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 1920,
                "height": 1080,
                "deviceScaleFactor": 1,
                "mobile": False,
                "screenWidth": 1920,
                "screenHeight": 1080,
            },
        )
    except Exception:
        pass


def esperar_carregamento(driver, timeout: float = 20.0) -> None:
    try:
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
    except Exception:
        time.sleep(random.uniform(1.5, 3.0))


def dispensar_banner_cookies(driver) -> None:
    from selenium.webdriver.common.by import By

    for seletor in (
        "#onetrust-accept-btn-handler",
        "#onetrust-reject-all-handler",
        '[data-e2e="cookie-banner-accept"]',
    ):
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
            if elementos:
                clicar_humano(driver, elementos[0])
                time.sleep(random.uniform(0.4, 0.8))
                return
        except Exception:
            continue

    for xpath in (
        "//button[contains(., 'Accept all')]",
        "//button[contains(., 'Accept All')]",
        "//button[contains(., 'Aceitar')]",
    ):
        try:
            elementos = driver.find_elements(By.XPATH, xpath)
            if elementos:
                clicar_humano(driver, elementos[0])
                time.sleep(random.uniform(0.4, 0.8))
                return
        except Exception:
            continue


def scroll_humano(driver, vezes: int = 2) -> None:
    from selenium.webdriver.common.action_chains import ActionChains

    for _ in range(vezes):
        delta = random.randint(120, 480)
        try:
            ActionChains(driver).scroll_by_amount(delta).perform()
        except Exception:
            driver.execute_script(f"window.scrollBy({{top: {delta}, behavior: 'smooth'}})")
        time.sleep(random.uniform(0.4, 1.0))


def mover_mouse_humano(driver, target_x: int = None, target_y: int = None) -> None:
    from selenium.webdriver.common.action_chains import ActionChains

    try:
        w = driver.execute_script("return window.innerWidth") or 1920
        h = driver.execute_script("return window.innerHeight") or 1080

        if target_x is None:
            target_x = random.randint(w // 4, 3 * w // 4)
        if target_y is None:
            target_y = random.randint(h // 4, 3 * h // 4)

        chain = ActionChains(driver)
        chain.move_by_offset(10, 10)
        chain.pause(random.uniform(0.1, 0.3))

        steps = random.randint(5, 10)
        for _ in range(steps):
            dx = random.randint(-20, 20)
            dy = random.randint(-20, 20)
            chain.move_by_offset(dx, dy)
            chain.pause(random.uniform(0.03, 0.1))

        chain.perform()
    except Exception:
        pass


def clicar_humano(driver, elemento) -> None:
    from selenium.webdriver.common.action_chains import ActionChains

    try:
        ActionChains(driver).move_to_element(elemento).pause(random.uniform(0.1, 0.3)).click().perform()
    except Exception:
        elemento.click()
