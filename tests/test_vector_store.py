from app.core.repo_indexer import FunctionRecord
from app.core.vector_store import VectorStore


def test_vector_store_indexes_and_retrieves(tmp_path, monkeypatch):
    monkeypatch.setattr("app.core.vector_store.settings.chroma_persist_dir", str(tmp_path))
    store = VectorStore()
    records = [
        FunctionRecord("a.py::add", "add", "def add(a, b): return a + b", "add numbers", []),
        FunctionRecord("b.py::sum_values", "sum_values", "def sum_values(a, b): return a + b", "sum numbers", []),
    ]

    store.index_functions(records)
    hits = store.retrieve_similar("add two numbers", k=1, exclude_id="a.py::add")

    assert len(hits) == 1
    assert hits[0]["meta"]["qualified_name"] == "b.py::sum_values"
