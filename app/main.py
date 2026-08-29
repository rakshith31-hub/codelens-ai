from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.core.knowledge_graph import KnowledgeGraph
from app.core.repo_indexer import index_repo
from app.core.vector_store import VectorStore
from app.graph_pipeline import pipeline

app = FastAPI(title="AutoDocs AI", version="1.1.0")

_vector_store = VectorStore()
_graph = KnowledgeGraph()


class IndexRequest(BaseModel):
    repo_path: str


class AnalyzeRequest(BaseModel):
    repo_path: str
    function_name: str | None = None


def _index(repo_path: str):
    records = index_repo(repo_path)
    if not records:
        raise HTTPException(
            status_code=400,
            detail="No Python functions were found in the supplied repository path.",
        )

    _vector_store.index_functions(records)
    _graph.index_functions(records)
    return records


@app.post("/index")
def index_repository(req: IndexRequest):
    """Parse a repo and refresh its vector + graph indexes."""
    records = _index(req.repo_path)
    return {"indexed_functions": len(records)}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    """Index the repo and run the multi-agent pipeline over one or all functions."""
    records = _index(req.repo_path)

    if req.function_name:
        records = [r for r in records if r.name == req.function_name]
        if not records:
            raise HTTPException(
                status_code=404,
                detail=f"Function '{req.function_name}' was not found in the repository.",
            )

    results = []
    for record in records:
        state = {
            "target_function": {
                "qualified_name": record.qualified_name,
                "name": record.name,
                "source": record.source,
                "docstring": record.docstring,
            }
        }
        final_state = pipeline.invoke(state)
        results.append(
            {
                "function": record.qualified_name,
                "review": final_state.get("review"),
                "graph_context": final_state.get("graph_context"),
                "similar_functions": final_state.get("similar_functions", []),
            }
        )

    return {"results": results}


@app.get("/health")
def health():
    return {"status": "ok"}
