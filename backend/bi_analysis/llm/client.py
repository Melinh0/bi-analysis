import ollama
import httpx
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
import json

from bi_analysis.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OllamaClient:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.api_key = settings.ollama_api_key
        self.model = settings.ollama_model
        self.embedding_model = settings.ollama_embedding_model
        self._client = None
        self._async_client = None

    @property
    def client(self):
        if self._client is None:
            self._client = ollama.Client(
                host=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            )
        return self._client

    @property
    def async_client(self):
        if self._async_client is None:
            self._async_client = ollama.AsyncClient(
                host=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
            )
        return self._async_client

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        model = model or self.model
        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature, **kwargs},
                stream=stream,
            )
            return response
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    async def chat_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        model = model or self.model
        try:
            response = await self.async_client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature, **kwargs},
                stream=stream,
            )
            return response
        except Exception as e:
            logger.error(f"Ollama async chat error: {e}")
            raise

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        model = model or self.model
        try:
            stream = self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature, **kwargs},
                stream=True,
            )
            for chunk in stream:
                yield chunk
        except Exception as e:
            logger.error(f"Ollama chat stream error: {e}")
            raise

    async def chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        model = model or self.model
        try:
            stream = await self.async_client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature, **kwargs},
                stream=True,
            )
            async for chunk in stream:
                yield chunk
        except Exception as e:
            logger.error(f"Ollama async chat stream error: {e}")
            raise

    def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        model = model or self.embedding_model
        try:
            response = self.client.embed(model=model, input=texts)
            return response["embeddings"]
        except Exception as e:
            logger.error(f"Ollama embed error: {e}")
            raise

    async def embed_async(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> List[List[float]]:
        model = model or self.embedding_model
        try:
            response = await self.async_client.embed(model=model, input=texts)
            return response["embeddings"]
        except Exception as e:
            logger.error(f"Ollama async embed error: {e}")
            raise

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        model = model or self.model
        try:
            response = self.client.generate(
                model=model,
                prompt=prompt,
                options={"temperature": temperature, **kwargs},
            )
            return response["response"]
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            raise

    def list_models(self) -> List[str]:
        




        try:
            response = self.client.list()
            raw_models = (
                response.get("models", [])
                if isinstance(response, dict)
                else getattr(response, "models", []) or []
            )
            names: List[str] = []
            for m in raw_models:
                if isinstance(m, dict):
                    name = m.get("name") or m.get("model")
                else:
                    name = getattr(m, "name", None) or getattr(m, "model", None)
                if name:
                    names.append(name)
            return names
        except Exception as e:
            logger.error(f"Ollama list models error: {e}")
            return []

    def pull_model(self, model: str) -> bool:
        try:
            self.client.pull(model)
            return True
        except Exception as e:
            logger.error(f"Ollama pull model error: {e}")
            return False


_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


def reset_ollama_client() -> None:

    global _ollama_client
    _ollama_client = None
