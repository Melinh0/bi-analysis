from pathlib import Path
from time import time
from typing import Callable, Optional
import logging

import requests

from playwright.sync_api import sync_playwright, TimeoutError

from bi_analysis.logger.log import Log
from bi_analysis.instagram.utils import (remover_none, obter_request_comentarios, extrair_comentario, extrair_post,
                                           obter_response_comentarios, obter_request_feed, obter_response_feed )

logger = logging.getLogger(__name__)


class APIBot():
    
    def __init__(
        self,
        usuario: Optional[str] = None,
        senha: Optional[str] = None,
        perfil: Optional[str] = None,
        manual_login: bool = False,
        headless: bool = True,
        login_timeout: int = 300,
    ) -> None:
        self.__usuario = usuario
        self.__senha = senha
        self.__perfil = perfil
        self.__manual_login = manual_login
        self.__headless = headless
        self.__login_timeout = login_timeout

    def _parede_login(self, page) -> bool:

        try:
            url = (page.url or "").lower()
            if "accounts/login" in url or "accounts/onetap" in url:
                return True
            return page.query_selector('input[name="password"]') is not None
        except Exception:
            return False

    def _sessao_logada(self, page) -> bool:

        try:
            return page.query_selector('a[href*="/direct/inbox"]') is not None
        except Exception:
            return False

    def _estado_sessao(self, page) -> str:

        prazo = time() + 8
        while time() < prazo:
            if self._sessao_logada(page):
                return "logado"
            if self._parede_login(page):
                return "parede"
            page.wait_for_timeout(1000)
        return "indefinido"

    def _aguardar_login_manual(self, page) -> None:
        if self.__headless:
            raise RuntimeError(
                "Instagram: a sessão não está logada e não há interface gráfica (DISPLAY) "
                "para o login manual. Execute com área de trabalho disponível ou "
                "configure credenciais em Configurações."
            )

        logger.info(
            "Instagram (API): aguardando o login manual na janela aberta (até %ss)...",
            self.__login_timeout,
        )
        try:
            page.goto('https://www.instagram.com/accounts/login/')
        except Exception:
            pass

        prazo = time() + self.__login_timeout
        while time() < prazo:
            if not self._parede_login(page):
                logger.info("Instagram (API): login manual concluído; a sessão será reaproveitada.")
                return
            page.wait_for_timeout(2000)

        raise RuntimeError(
            f"Instagram: tempo esgotado ({self.__login_timeout}s) aguardando o login manual. "
            "Execute a extração novamente e conclua o login na janela do navegador."
        )

    def _assegurar_login(self, page) -> None:

        estado = self._estado_sessao(page)
        if estado == "logado":
            return

        if self.__manual_login:

            self._aguardar_login_manual(page)
            return

        if estado == "indefinido":

            return


        if self.__usuario and self.__senha:
            try:
                page.fill('input[name="username"]', self.__usuario)
                page.fill('input[name="password"]', self.__senha)
                page.click('button[type=submit]')
                page.wait_for_timeout(6000)
                for rotulo in ('Agora não', 'Not now'):
                    try:
                        page.get_by_text(rotulo, exact=True).click(timeout=3000)
                        break
                    except Exception:
                        pass
                if self._estado_sessao(page) != "parede":
                    return
            except Exception:
                logger.warning(
                    "Instagram (API): login automático falhou; seguindo para o login manual.",
                    exc_info=True,
                )
        else:
            logger.info("Instagram (API): sem credenciais configuradas; será solicitado o login manual.")

        self._aguardar_login_manual(page)
    

    @Log.log
    def obter_api_endpoint(self, link: str, filtro_request: Callable, filtro_response: Callable) -> tuple[list]:
        
            pw = sync_playwright().start()
            browser = None
            context = None
            try:



                if self.__perfil:
                    try:
                        Path(self.__perfil).mkdir(parents=True, exist_ok=True)
                        context = pw.chromium.launch_persistent_context(
                            self.__perfil,
                            headless=self.__headless,
                            channel="chrome",
                            ignore_default_args=[
                                '--disable-extensions', 
                                '--disable-default-apps', 
                                '--disable-component-extensions-with-background-pages'
                                ]
                            )
                    except Exception:
                        logger.warning(
                            "Instagram (API): perfil persistente indisponível; "
                            "seguindo sem sessão salva nesta execução.",
                            exc_info=True,
                        )
                        context = None

                if context is None:
                    browser = pw.chromium.launch(
                        headless=self.__headless,
                        ignore_default_args=[
                            '--disable-extensions', 
                            '--disable-default-apps', 
                            '--disable-component-extensions-with-background-pages'
                            ]
                        )
                    context = browser.new_context()

                page = context.pages[0] if context.pages else context.new_page()

                
                dados_request = []
                dados_response = []

                def capturar_request(request):
                    try:
                        dados_request.append(filtro_request(request))
                    except Exception:
                        pass

                def capturar_response(response):
                    try:
                        dados_response.append(filtro_response(response))
                    except Exception:
                        pass


                page.on("request", capturar_request)
                page.on("response", capturar_response)

                page.goto('https://www.instagram.com/')
                page.wait_for_timeout(4000)


                self._assegurar_login(page)

                page.goto(link)
                
                page.wait_for_selector('main[role=main]')
                
                if filtro_request.__name__ == 'obter_request_feed':
                    page.mouse.wheel(0, 1200)
                
                else:
                    page.reload()
                page.wait_for_timeout(5000)

                return (remover_none(dados_request), remover_none(dados_response))
            except TimeoutError as e:
                raise RuntimeError(
                    f"Instagram: a página não carregou dentro do tempo limite ({e})"
                ) from e
            finally:
                if context is not None:
                    try:
                        context.close()
                    except Exception:
                        pass
                if browser is not None:
                    try:
                        browser.close()
                    except Exception:
                        pass
                try:
                    pw.stop()
                except Exception:
                    pass
    
    @Log.log
    def extrair_comentarios_instagram_api(self, link: str) -> list[dict] | str:
        
        request, response = self.obter_api_endpoint(link=link, filtro_request= obter_request_comentarios,
                                                    filtro_response= obter_response_comentarios)
        
        try:
            url = request[0].get('url')
        except IndexError as e:
            Log.ex(e)
            return 'request api não encontrada — a sessão pode estar deslogada; repita a extração com login manual na primeira execução!'
        
        headers = {key.replace(':', ""): value for (key,value) in request[0].get('headers').items()}
        
        try:
            comentarios = [extrair_comentario(comentario) for comentario in response[0].get('comments')]
        except TypeError as e:
                Log.ex(e)
                return 'request api não encontrada — a sessão pode estar deslogada; repita a extração com login manual na primeira execução!'
        
        num_comentarios = response[0].get('comment_count') or 0
        
        payload ={
        'can_support_threading': 'true',
        'min_id': response[0].get('next_min_id')
        }
        
        if num_comentarios > 1200:
            num_comentarios = round(0.7 * num_comentarios)
        
        while len(comentarios) < num_comentarios:
            res = requests.get(url, headers=headers, params=payload)

            data = res.json() or {}
            novos = data.get('comments') or []
            if not novos:
                break
            comentarios.extend([extrair_comentario(comentario) for comentario in novos if comentario])

            if not data.get('next_min_id'):
                break
            payload ={
                        'can_support_threading': 'true',
                        'min_id': data.get('next_min_id')
                        }
            
        return comentarios
    
    @Log.log
    def extrair_posts_instagram_api(self, link: str, num_posts: int) -> list[dict] | str:

        request, _ = self.obter_api_endpoint(link=link, filtro_request= obter_request_feed,
                                             filtro_response= obter_response_feed)
        
        try:
            url = request[0].get('url')
        except IndexError as e:
            Log.ex(e)
            return 'request api não encontrada — a sessão pode estar deslogada; repita a extração com login manual na primeira execução!'
        
        url = url.split('?')[0]
        headers = {key.replace(':', ""): value for (key,value) in request[0].get('headers').items()}
        
        posts = []
        payload ={
            'count': 12, 
            'can_support_threading': 'true'
        }
        
        lote = round(num_posts/10)
        
        while len(posts) < num_posts:
            res = requests.get(url, headers=headers, params=payload)

            data = res.json() or {}
            novos = data.get('items') or []
            if not novos:
                break
            posts.extend([extrair_post(item) for item in novos if item])

            if not data.get('next_max_id'):
                break
            payload ={
                    'count': lote,
                    'max_id': data.get('next_max_id')
                    }
            
        return posts
