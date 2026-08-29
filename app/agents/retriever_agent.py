from app.core.state import PipelineState
from app.core.vector_store import VectorStore

_vector_store = VectorStore()


def retriever_node(state: PipelineState) -> PipelineState:
    """RAG step: find semantically similar functions already indexed in the vector DB."""
    target = state["target_function"]
    query = f"{target['docstring']}\n\n{target['source']}"

    similar = _vector_store.retrieve_similar(
        query_text=query, k=3, exclude_id=target["qualified_name"]
    )
    return {"similar_functions": similar}
