import functools
import inspect
import logging
import logging.config
from typing import Any

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Log():

    __instance = None

    def __init__(self) -> None:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(threadName)s - %(message)s",
            handlers=[
                logging.StreamHandler()
            ])

        self.logger = logging.getLogger(__name__ + '.logger')
    

    @staticmethod
    def __get_instance():

        if Log.__instance is None:
            Log.__instance = Log()

        return Log.__instance


    @staticmethod
    def __get_class() -> str:
        
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 1)

        f_locals = inspect.stack()[2][0].f_locals
        if 'self' in f_locals:
            class_name = f_locals['self'].__class__.__name__
            func_name = f'.{calframe[2][3]}()'
        else:
            class_name = f'<{inspect.stack()[2][1].split("/")[-1]}>'
            func_name = f'.{inspect.stack()[2][3]}()'

        return f'{class_name + func_name: <56s} '

    @staticmethod
    def i(mensagem: Any) -> None:
        
        for msg in str(mensagem).split('\n'):
            Log.__get_instance().logger.info(Log.__get_class() + str(msg))

    @staticmethod
    def d(mensagem: Any) -> None:
        
        for msg in str(mensagem).split('\n'):
             Log.__get_instance().logger.debug(Log.__get_class() + str(msg))

    @staticmethod
    def w(mensagem: Any) -> None:
        
        for msg in str(mensagem).split('\n'):
             Log.__get_instance().logger.warning(Log.__get_class() + str(msg))

    @staticmethod
    def e(mensagem: Any) -> None:
        
        for msg in str(mensagem).split('\n'):
             Log.__get_instance().logger.error(Log.__get_class() + str(msg))

    @staticmethod
    def ex(mensagem: Any) -> None:
        
        for msg in str(mensagem).split('\n'):
             Log.__get_instance().logger.exception(Log.__get_class() + str(msg))

    @staticmethod
    def log(function):
        

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            class_name = f'{str(function).split(" ")[1]}()'
            Log.__get_instance().logger.debug(f'{class_name:.<56s}')
            return function(*args, **kwargs)

        return wrapper
    
    @staticmethod
    def __get_call_info():
        stack = inspect.stack()


        fn = stack[2][1]
        ln = stack[2][2]
        func = stack[2][3]
        
        return fn, func, ln
    

    @staticmethod
    def info(message, *args):
        message = "{} - {} at line {}: {}".format(*Log.__get_instance().__get_call_info(), message)
        Log.__get_instance().logger.info(message, *args)
