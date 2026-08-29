from typing import TypedDict


class PipelineState(TypedDict, total=False):
    target_function: dict          # {"qualified_name", "name", "source", "docstring"}
    similar_functions: list[dict]  # from RetrieverAgent (RAG)
    graph_context: dict            # from GraphAnalystAgent (Neo4j)
    review: dict                   # from ReviewerAgent (final output)
