from app.core.config import settings
from app.core.review_schema import ReviewOutput
from app.core.state import PipelineState

_SYSTEM_PROMPT = """You are an autonomous code review agent. You are given:
1. A target function's source code.
2. Semantically similar functions from a vector search (RAG context).
3. Structural graph context: which functions call it, and which functions it calls.

Return a structured review with:
- suggested_docstring: a concise, accurate docstring for the target function
- review_comments: 2-4 short, specific review points (bugs, edge cases, style)
- risk_flag: high if fan_in + fan_out > 4, otherwise low
- risk_reason: one sentence explaining the risk flag from the graph context

Be concise and concrete. Do not invent behavior not present in the code."""


def _get_llm():
    """Return the configured LLM provider."""
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
        )

    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
    )


def reviewer_node(state: PipelineState) -> PipelineState:
    target = state["target_function"]
    similar = state.get("similar_functions", [])
    graph_ctx = state.get("graph_context", {})

    similar_text = "\n---\n".join(s["content"] for s in similar) or "(none found)"

    user_prompt = f"""Target function ({target['qualified_name']}):
```python
{target['source']}
```

Similar functions found via RAG:
{similar_text}

Graph context:
- Called by: {graph_ctx.get('callers') or 'none'}
- Calls: {graph_ctx.get('callees') or 'none'}
- fan_in={graph_ctx.get('fan_in', 0)}, fan_out={graph_ctx.get('fan_out', 0)}

Return only the structured review."""

    llm = _get_llm()
    structured_llm = llm.with_structured_output(ReviewOutput)
    review = structured_llm.invoke(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    )

    if isinstance(review, ReviewOutput):
        data = review.model_dump()
    else:
        data = ReviewOutput.model_validate(review).model_dump()

    return {"review": data}
