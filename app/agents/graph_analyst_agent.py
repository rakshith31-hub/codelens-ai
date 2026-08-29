from app.core.knowledge_graph import KnowledgeGraph
from app.core.state import PipelineState

_graph = KnowledgeGraph()


def graph_analyst_node(state: PipelineState) -> PipelineState:
    """Queries the code dependency graph for structural context: who calls this
    function, what it calls, and its fan-in/fan-out (a simple autonomous-QA risk signal:
    high fan-in means many callers depend on this function's behavior staying stable)."""
    target = state["target_function"]
    context = _graph.get_context(target["qualified_name"])
    return {"graph_context": context}
