from typing import List, Dict, Any, Optional, Generator
import logging
from dataclasses import dataclass

from bi_analysis.vector_store.store import get_vector_store
from bi_analysis.llm.client import get_ollama_client
from bi_analysis.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RetrievedDocument:
    content: str
    metadata: Dict[str, Any]
    distance: float
    id: str


@dataclass
class RAGResponse:
    answer: str
    sources: List[RetrievedDocument]
    model: str
    tokens_used: Optional[int] = None


class RAGPipeline:
    def __init__(
        self,
        top_k: int = None,
        model: str = None,
        temperature: float = 0.7,
    ):
        self.top_k = top_k or settings.top_k_retrieval
        self.model = model or settings.ollama_model
        self.temperature = temperature
        self.vector_store = get_vector_store()
        self.llm = get_ollama_client()

    def retrieve(
        self,
        query: str,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        results = self.vector_store.query(
            query_texts=[query],
            n_results=self.top_k,
            where=where,
        )

        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append(
                    RetrievedDocument(
                        content=doc,
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        distance=results["distances"][0][i] if results["distances"] else 0.0,
                        id=results["ids"][0][i] if results["ids"] else "",
                    )
                )
        return documents

    def retrieve_by_embedding(
        self,
        query_embedding: List[float],
        where: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievedDocument]:
        results = self.vector_store.query_by_embedding(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            where=where,
        )

        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append(
                    RetrievedDocument(
                        content=doc,
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        distance=results["distances"][0][i] if results["distances"] else 0.0,
                        id=results["ids"][0][i] if results["ids"] else "",
                    )
                )
        return documents

    def build_context(self, documents: List[RetrievedDocument]) -> str:
        context_parts = []
        for i, doc in enumerate(documents, 1):
            meta = doc.metadata
            source_info = f"[Fonte {i}] "
            if meta.get("source_type"):
                source_info += f"Tipo: {meta['source_type']} | "
            if meta.get("author"):
                source_info += f"Autor: {meta['author']} | "
            if meta.get("published_at"):
                source_info += f"Data: {meta['published_at']} | "
            if meta.get("url"):
                source_info += f"URL: {meta['url']} | "
            context_parts.append(f"{source_info}\nConteúdo: {doc.content}\n")
        return "\n".join(context_parts)

    def build_prompt(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        default_system = """Você é um assistente de Business Intelligence especializado em análise de dados de redes sociais, notícias e relatórios.
Use APENAS o contexto fornecido para responder. Se a informação não estiver no contexto, diga que não sabe.
Cite as fontes usando o formato [Fonte X] ao final de cada afirmação.
Responda em português do Brasil."""
        
        system = system_prompt or default_system
        
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Contexto:\n{context}\n\nPergunta: {query}"},
        ]

    def generate(
        self,
        query: str,
        documents: List[RetrievedDocument],
        system_prompt: Optional[str] = None,
    ) -> RAGResponse:
        context = self.build_context(documents)
        messages = self.build_prompt(query, context, system_prompt)
        
        response = self.llm.chat(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        )
        
        return RAGResponse(
            answer=response["message"]["content"],
            sources=documents,
            model=self.model,
            tokens_used=response.get("eval_count"),
        )

    def generate_stream(
        self,
        query: str,
        documents: List[RetrievedDocument],
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        context = self.build_context(documents)
        messages = self.build_prompt(query, context, system_prompt)
        
        for chunk in self.llm.chat_stream(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
        ):
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

    def query(
        self,
        query: str,
        where: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> RAGResponse:
        documents = self.retrieve(query, where)
        return self.generate(query, documents, system_prompt)

    def query_stream(
        self,
        query: str,
        where: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
    ) -> Generator[str, None, None]:
        documents = self.retrieve(query, where)
        yield from self.generate_stream(query, documents, system_prompt)


def create_rag_pipeline(
    top_k: int = None,
    model: str = None,
    temperature: float = 0.7,
) -> RAGPipeline:
    return RAGPipeline(top_k=top_k, model=model, temperature=temperature)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAG Pipeline CLI")
    parser.add_argument("query", help="Query to search")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--model", default=None, help="Model to use")
    args = parser.parse_args()

    pipeline = create_rag_pipeline(top_k=args.top_k, model=args.model)
    result = pipeline.query(args.query)
    print(f"Answer: {result.answer}")
    print(f"\nSources ({len(result.sources)}):")
    for i, src in enumerate(result.sources, 1):
        print(f"  [{i}] {src.content[:100]}... (dist: {src.distance:.3f})")


if __name__ == "__main__":
    main()
