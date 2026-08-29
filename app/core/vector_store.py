"""
Thin wrapper around ChromaDB for storing and retrieving function embeddings.
This is the "vector database / RAG" half of the system.
"""
import chromadb
from chromadb.utils import embedding_functions

from app.core.config import settings
from app.core.repo_indexer import FunctionRecord

_COLLECTION_NAME = "functions"


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        # Use Chroma's built-in default embedding function so the project runs
        # without requiring an embeddings API call for every demo run.
        self.embedder = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=_COLLECTION_NAME, embedding_function=self.embedder
        )

    def index_functions(self, records: list[FunctionRecord]) -> None:
        if not records:
            return
        self.collection.upsert(
            ids=[r.qualified_name for r in records],
            documents=[f"{r.docstring}\n\n{r.source}" for r in records],
            metadatas=[{"name": r.name, "qualified_name": r.qualified_name} for r in records],
        )

    def retrieve_similar(self, query_text: str, k: int = 3, exclude_id: str | None = None) -> list[dict]:
        results = self.collection.query(query_texts=[query_text], n_results=k + 1)
        hits = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            if exclude_id and meta.get("qualified_name") == exclude_id:
                continue
            hits.append({"content": doc, "meta": meta})
        return hits[:k]
