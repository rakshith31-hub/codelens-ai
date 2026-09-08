# CodeLens AI (AutoDocs AI) — Autonomous Multi-Agent Code Documentation & Review System
AutoDocs AI is a small agentic system that reviews a Python codebase and generates documentation + review comments. It combines **RAG**, a **Neo4j code dependency graph**, and a **LangGraph multi-agent workflow** to ground an LLM reviewer in both semantic and structural context.

## What it demonstrates

| Capability | Implementation |
|---|---|
| Agentic / multi-agent AI | `app/graph_pipeline.py` — Retriever → Graph Analyst → Reviewer |
| RAG / vector search | `app/core/vector_store.py` — ChromaDB embeddings + similarity retrieval |
| Knowledge graph | `app/core/knowledge_graph.py` — Neo4j `CALLS` graph |
| Static code analysis | `app/core/repo_indexer.py` — Python `ast` parsing |
| AI code review | `app/agents/reviewer_agent.py` — structured LLM output |
| API layer | `app/main.py` — FastAPI `/index`, `/analyze`, `/health` |
| Containerized setup | `Dockerfile` + `docker-compose.yml` |
| Automated testing | `tests/` — indexer, API, schema and vector-store coverage |

## Architecture

```text
                    ┌─────────────────────┐
 repo path ────────►│  FastAPI /analyze   │
                    └──────────┬──────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │       LangGraph            │
                 │ Retriever → Graph → Review │
                 └───────┬───────────┬────────┘
                         │           │
              ┌──────────▼───┐  ┌────▼──────────┐
              │ ChromaDB RAG │  │ Neo4j Graph   │
              │ semantic     │  │ callers/callees│
              │ retrieval    │  │ fan-in/fan-out │
              └──────────────┘  └───────────────┘
                         \           /
                          \         /
                           ▼       ▼
                        ┌─────────────┐
                        │ LLM Reviewer│
                        │ structured  │
                        │ JSON output │
                        └─────────────┘
```

## End-to-end flow

1. **Indexing** — `repo_indexer.py` walks the target repository and uses Python's `ast` module to extract functions, source, docstrings and direct function calls.
2. **RAG retrieval** — functions are embedded into ChromaDB. For each target function, the RetrieverAgent finds semantically similar functions while excluding the target itself.
3. **Graph analysis** — the GraphAnalystAgent queries Neo4j for callers, callees, fan-in and fan-out.
4. **Review synthesis** — the ReviewerAgent combines the target code, RAG context and graph context. The LLM response is validated with the Pydantic `ReviewOutput` schema rather than being stored as an unparsed string.
5. **Result** — `/analyze` returns the structured review together with graph and retrieval context.

## Important fixes in this version

- `/analyze` now **indexes both ChromaDB and Neo4j before running the pipeline**, so the documented one-shot workflow works without manually calling `/index` first.
- Re-indexing a function now removes its old `CALLS` edges before rebuilding them, preventing stale graph relationships.
- LLM responses are validated through `ReviewOutput` with structured output instead of returning `raw_llm_output`.
- `/analyze` returns a clear `404` when a requested function does not exist.
- `/analyze` and `/index` return a clear `400` when no Python functions are found.
- Added API, schema and vector-store tests alongside the existing AST indexer tests.
- Added `pytest` and `httpx` to the development dependencies.
- Added `.dockerignore` so local secrets, caches and virtual environments are not copied into the Docker build context.
- Documentation now accurately describes ChromaDB as an embedded/persistent component of the app rather than a separate container.

## Running locally with Docker

```bash
cp .env.example .env
# Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env

docker compose up --build
```

Then run the complete analysis in one request:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/data/sample_repo"}'
```

To analyze one function only:

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "/data/sample_repo", "function_name": "checkout"}'
```

The sample repository contains intentionally interdependent functions so the complete RAG + graph workflow can be demonstrated without another codebase.

## API

### `GET /health`

Returns:

```json
{"status": "ok"}
```

### `POST /index`

Request:

```json
{"repo_path": "/data/sample_repo"}
```

Response:

```json
{"indexed_functions": 5}
```

### `POST /analyze`

Request:

```json
{
  "repo_path": "/data/sample_repo",
  "function_name": "checkout"
}
```

`function_name` is optional. If omitted, every discovered function is analyzed.

The response contains the structured review, graph context and retrieved similar functions for each target function.

## Environment variables

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
LLM_MODEL=gpt-4o-mini

NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=autodocs_pw

CHROMA_PERSIST_DIR=/data/chroma
```

## Testing

Install dependencies and run:

```bash
pip install -r requirements.txt
pytest -q
```

The test suite covers:

- Python function and call extraction
- API health and analysis behavior
- missing-function handling
- review schema validation
- vector indexing/retrieval behavior

## Design choices

The project intentionally avoids unnecessary infrastructure. The goal is to demonstrate a clear AI-engineering architecture that is easy to explain in an interview:

- one LLM call site
- one Neo4j relationship type (`CALLS`)
- one ChromaDB collection
- three explicit LangGraph nodes
- Pydantic validation at the LLM boundary
- Docker Compose for reproducible local setup

## Future extensions

- Add a TestGeneratorAgent that generates pytest cases from the review.
- Run generated tests and feed failures back into the graph for a validation loop.
- Expand AST analysis to imports, classes and more precise cross-module call resolution.
- Add repository-scoped indexing/deletion so multiple codebases can safely share one vector/graph backend.
