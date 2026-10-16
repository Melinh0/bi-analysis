import time
from itertools import zip_longest
from dateutil.parser import parse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.common.exceptions import *

from bi_analysis.instagram.comentario import Coletor_de_comentario, Comentario
from bi_analysis.logger.log import Log


class instagram_bot():
    

    def __init__(self, driver: webdriver) -> None:
        
        self.driver = driver
    
    @Log.log
    def login(self, usuario: str, senha: str) -> None:
        
        try:
            usuario_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='username']")
            
            senha_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")

            usuario_input.clear()
            senha_input.clear()

            usuario_input.send_keys(usuario)
            senha_input.send_keys(senha)
            
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            

        except (NoSuchElementException, ElementClickInterceptedException)  as e:
            Log.ex('Exceção durante a execução de %s: %r'.format(self.login.__name__, e.msg))
            raise RuntimeError(f"Instagram: falha ao entrar na conta ({e.msg})") from e
    
    @Log.log
    def passar_notificacao(self)-> None:
        
        try:
            agora_nao = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Agora não')]")
            agora_nao.click()
            
        except (NoSuchElementException, ElementClickInterceptedException)  as e:
            Log.ex('Exceção durante a execução de %s: %r'.format(self.passar_notificacao.__name__, e.msg))
            raise RuntimeError(f"Instagram: falha ao dispensar notificação ({e.msg})") from e
    
    @Log.log
    def ir_para_post(self, link:str) -> None:
        Log.i(f'navegando para: {link}')
        self.driver.get(link)
    

    @Log.log
    def carregar_mais_comentarios(self, limit: int) -> None:
        
       
        i = 0
        try:
              container = self.driver.find_element(By.CLASS_NAME, "x5yr21d.xw2csxc.x1odjw0f.x1n2onr6")
              scroll_origin = ScrollOrigin.from_element(container)
              i = 0
              scrolling = True
              while scrolling:
                i+=1
                ActionChains(self.driver).scroll_from_origin(scroll_origin, 0, 10000).perform()
                time.sleep(3)
                last_position = self.driver.execute_script()
                if not last_position or i > limit :
                    scrolling = False

        except (NoSuchElementException, StaleElementReferenceException, TimeoutException, WebDriverException) as e:
              Log.ex('Exceção durante a execução de %s: %r'.format(self.carregar_mais_comentarios.__name__, e.msg))
    
    
    @Log.log
    def extrair_comentarios(self) -> Comentario:
        
        try:
            lista_de_tags_comentario = self.driver.find_elements(By.CLASS_NAME, "x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.x1uhb9sk.x1plvlek.xryxfnj.x1iyjqo2.x2lwn1j.xeuugli.x1q0g3np.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1")
        except NoSuchElementException as e:
            Log.ex('Exceção durante a execução de %s: %r'.format(self.extrair_comentarios.__name__, e.msg))
            raise RuntimeError(f"Instagram: falha ao localizar os comentários ({e.msg})") from e

        for tag in lista_de_tags_comentario:
            yield Coletor_de_comentario(tag).extrair_comentario()
    

    @Log.log
    def close(self) -> None:

            
            try:
                self.driver.find_element(By.CLASS_NAME, "xl5mz7h.xhuyl8g").click()

                time.sleep(2)
                
                menu_items = self.driver.find_element(By.CLASS_NAME, "xu96u03.xm80bdy.x10l6tqk.x13vifvy")
                menu_items.find_element(By.XPATH, "//span[contains(text(), 'Sair')]").click()
                
                self.driver.quit()
            except( NoSuchElementException, ElementClickInterceptedException) as e:
                Log.ex('Exceção durante a execução de %s: %r'.format(self.close.__name__, e.msg))
                self.driver.quit()


    
    @Log.log
    def scroll_fotos(self, limit: int):
        
        posts =[]
        post_ids = set()

        

        last_position =  self.driver.execute_script('return window.pageYOffset;')
        scrolling = True
        while scrolling:
            try: 
                  post_cards = self.driver.find_elements(By.CSS_SELECTOR, "div._aabd._aa8k._al3l")
                  print(len(post_cards))
            except NoSuchElementException as e:
                  Log.ex('Exceção durante a execução de %s: %r', self.close.__name__, e.msg)
                  self.driver.quit()
            
            for card in post_cards[-150:]:
                try:
                    card.find_element(By.CSS_SELECTOR, "svg[aria-label='Clipe']")
                    continue
                except (NoSuchElementException, StaleElementReferenceException):
                    pass

                try:
                    actions = ActionChains(self.driver) 
                    actions.move_to_element(card)
                    actions.perform()
                    
                    time.sleep(0.5)
                    post = self.extrair_metricas_fotos(card)
                    
                except StaleElementReferenceException as e:
                    Log.ex('Exceção durante a execução de %s: %r', self.scroll_fotos.__name__, e.msg)
                    continue
                if not post:
                    continue

                post_id = ''.join(post[0].split('/')[4])
                if post_id not in post_ids:
                    post_ids.add(post)
                    posts.append(post)
                        
            scroll_attempt = 0
            while True:
                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(1)
                current_position =  self.driver.execute_script('return window.pageYOffset;')
                if last_position == current_position:
                    scroll_attempt += 1
                    if scroll_attempt > 3:
                        scrolling = False
                        break
                    else:
                        time.sleep(2)
                else:
                    last_position = current_position
                    break
            
            if len(posts) > limit:
                break
        return posts
    

    @Log.log
    def extrair_metricas_fotos(self, post_container) -> tuple:
         
        link = post_container.find_element(By.TAG_NAME, 'a').get_attribute('href')

        try:
            elem_hover = post_container.find_element(By.CLASS_NAME, '_ac2d')
            
            likes = elem_hover.find_element(By.XPATH, './/ul/li[1]/div/span').text
            
            comments = elem_hover.find_element(By.XPATH, './/ul/li[2]/div/span').text
        except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
            Log.ex('Exceção durante a execução de %s: %r', self.extrair_metricas_fotos.__name__, e.msg)
            likes = "0"
            comments = "0"
            pass

        post = (link, likes, comments)
        return post
    
    @Log.log
    def extrair_texto_e_data(self, link: str) -> tuple:

        self.driver.get(link)
        time.sleep(5)
        
        try:
            container = self.driver.find_element(By.CLASS_NAME, "_ae2s._ae3v._ae3w")
            texto = container.find_element(By.TAG_NAME, 'h1').text

            data_div = container.find_element(By.CLASS_NAME, "_ae5u._ae5v._ae5w")

            link = data_div.find_element(By.XPATH, ".//div/div/a").get_attribute('href')

            data = data_div.find_element(By.XPATH, ".//div/div/a/div/time").get_attribute('datetime')

            data = parse(data)
            data = data.date().strftime("%d/%m/%y")
        except NoSuchElementException as e:
            Log.ex('Exceção durante a execução de %s: %r', self.extrair_texto_e_data.__name__, e.msg)
            
            link = ""
            texto = ""
            data = ""
            pass

        return (link, texto, data)
    

    @Log.log
    def scroll_reels(self, limit: int):
        
        posts =[]
        post_ids = set()

        
        last_position =  self.driver.execute_script('return window.pageYOffset;')
        scrolling = True
        while scrolling:
            try:
                post_cards = self.driver.find_elements(By.CLASS_NAME, "_aajw")
            except NoSuchElementException as e:
                Log.ex('Exceção durante a execução de %s: %r', self.scroll_reels.__name__, e.msg)
                break
            for card in post_cards[-150:]:

                try:
                    post = self.extrair_metricas_reels(card)
                    
                except StaleElementReferenceException:
                    continue
                if not post:
                    continue

                post_id = ''.join(post)
                if post_id not in post_ids:
                    post_ids.add(post_id)
                    posts.append(post)
                        
            scroll_attempt = 0
            while True:
                self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(1)
                current_position =  self.driver.execute_script('return window.pageYOffset;')
                if last_position == current_position:
                    scroll_attempt += 1
                    if scroll_attempt > 3:
                        scrolling = False
                        break
                    else:
                        time.sleep(2)
                else:
                    last_position = current_position
                    break
            
            if len(posts) > limit:
                break
        return posts
    
    
    @Log.log
    def extrair_metricas_reels(self, post_container) -> tuple:
        try:
            link = post_container.find_element(By.TAG_NAME, 'a').get_attribute('href')
            views = post_container.find_element(By.CLASS_NAME, '_aacl._aacp._aacw._aad3._aad6').text

            actions = ActionChains(self.driver)
            actions.move_to_element(post_container)
            actions.perform()
                    
            time.sleep(0.5)

            metricas_div = post_container.find_element(By.CLASS_NAME, '_ac2d')
            curtidas = metricas_div.find_element(By.XPATH, './/ul/li[1]/div/span').text
            
            comentarios = metricas_div.find_element(By.XPATH, './/ul/li[2]/div/span').text

        except NoSuchElementException as e:
            Log.ex('Exceção durante a execução de %s: %r', self.extrair_metricas_reels.__name__, e.msg)
            link = ""
            curtidas = ""
            comentarios = ""
            views = ""
            pass

        post = (link, curtidas, comentarios, views)
        return post
