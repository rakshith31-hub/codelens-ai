"""
Orchestrates RetrieverAgent -> GraphAnalystAgent -> ReviewerAgent as an explicit
LangGraph StateGraph. Retrieval and graph lookup are independent (both only need the
target function), so they could run in parallel; they're kept sequential here for
simplicity and easy debugging, and because the demo doesn't need the latency win.
"""
from langgraph.graph import END, StateGraph

from app.agents.graph_analyst_agent import graph_analyst_node
from app.agents.retriever_agent import retriever_node
from app.agents.reviewer_agent import reviewer_node
from app.core.state import PipelineState


def build_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("retriever", retriever_node)
    graph.add_node("graph_analyst", graph_analyst_node)
    graph.add_node("reviewer", reviewer_node)

    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "graph_analyst")
    graph.add_edge("graph_analyst", "reviewer")
    graph.add_edge("reviewer", END)

    return graph.compile()


pipeline = build_pipeline()
