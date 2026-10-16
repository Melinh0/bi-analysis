from typing import Any, Dict, Optional
import re
from dateutil.parser import parse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from bi_analysis.logger.log import Log
Comentario = Dict[str, Any]

Comentario_parcial = Optional[Dict[str, Any]]


class Coletor_de_comentario():
    
    
    
    def criar_novo_comentario(self)-> Comentario:
        return{
            'Usuário': None,
            'Texto': None,
            'Data': None,
            'Curtidas': None
        }
    
    def __init__(self, comentario_tag) -> None:
    
        self.comentario_tag = comentario_tag

    
    def extrair_usuario(self, container) -> Comentario_parcial:
            

            try:
                return {
                    'Usuário': container.find_element(By.XPATH, ".//div[1]/div[1]/div/div[1]/span[1]/div/div/a").get_attribute('text')
                }
            except NoSuchElementException as e:
                Log.ex('Exceção durante a execução de %s: %r'.format(self.extrair_usuario.__name__, e.msg))

                return{
                    'Usuário': None
                }    
    
    
    def extrair_texto(self, container) -> Comentario_parcial:
            

            try:
                return {
                    'Texto': container.find_element(By.XPATH, ".//div[1]/div[1]/div/div[2]/span").text
                }
            except NoSuchElementException as e:
                Log.ex('Exceção durante a execução de %s: %r'.format(self.extrair_texto.__name__, e.msg))

                return{
                    'Texto': None
                }  

    
    def extrair_data(self, container) -> Comentario_parcial:
            

            try:
                data = container.find_element(By.XPATH, ".//div[1]/div[1]/div/div[1]/span[2]/a/time").get_attribute('datetime')
            except NoSuchElementException as e:
                Log.ex('Exceção durante a execução de %s: %r'.format(self.extrair_data.__name__, e.msg))
                data = None
            
            if data is not None:
                data = parse(data)
                data = data.date().strftime("%d/%m/%y")
                
            return {
                    'Data': data
            }

    
    
    def extrair_curtidas(self, container) -> Comentario_parcial:
            

            try:
                curtidas = container.find_element(By.XPATH, ".//div[1]/div[2]/div[1]/span").text
                
            except NoSuchElementException as e:
                Log.ex('Exceção durante a execução de %s: %r'.format(self.extrair_curtidas.__name__, e.msg))
                curtidas = None

            if curtidas is not None:
                    curtidas = re.search(r"\d+", curtidas).group()

            return {
                    'Curtidas': curtidas
                }
            
    
    
    def extrair_respostas(self, container) -> Comentario_parcial:
            

            try:
                respostas = container.find_element(By.XPATH, ".//div/div/span").text
            except NoSuchElementException as e:
                Log.ex('Exceção durante a execução de %s: %r'.format(self.extrair_respostas.__name__, e.msg))
                respostas = None

            if respostas is not None:
                   respostas = re.search(r"\d+", respostas).group()
                   
            return {
                    'Respostas': respostas
                }
    

    @Log.log
    def extrair_comentario(self)-> Comentario:
        
        
        
        metodos = [
                self.extrair_usuario,
                self.extrair_texto,
                self.extrair_data,
                self.extrair_curtidas
               ]

        comment = self.criar_novo_comentario()

        for metodo in metodos:
            try:
                comentario_parcial = metodo(self.comentario_tag)
                if comentario_parcial is None:
                    Log.w('O método %s não retornou nada'.format(metodo.__name__))
                    continue
                
                comment.update(comentario_parcial)
            except Exception as e:
                Log.ex('Exceção durante a execução de %s: %r'.format(metodo.__name__, e))
                continue
        
        return comment
