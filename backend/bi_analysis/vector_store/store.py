import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import uuid
import logging

from bi_analysis.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.vector_store_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self._get_or_create_collection()
        self.embedding_function = self._create_embedding_function()

    def _get_or_create_collection(self):
        return self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _create_embedding_function(self):
        return embedding_functions.OllamaEmbeddingFunction(
            url=f"{settings.ollama_base_url}/api/embeddings",
            model_name=settings.ollama_embedding_model,
        )

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Added {len(documents)} documents to vector store")
        return ids

    def add_embeddings(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Added {len(documents)} embeddings to vector store")
        return ids

    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
        )

    def query_by_embedding(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
        )

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        return self.collection.get(ids=ids)

    def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} documents from vector store")

    def update_metadata(self, ids: List[str], metadatas: List[Dict[str, Any]]) -> None:
        self.collection.update(ids=ids, metadatas=metadatas)

    def count(self) -> int:
        return self.collection.count()

    def peek(self, limit: int = 10) -> Dict[str, Any]:
        return self.collection.peek(limit=limit)


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
