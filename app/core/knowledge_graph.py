"""
Thin wrapper around Neo4j for storing and querying the function call graph.
"""
from neo4j import GraphDatabase

from app.core.config import settings
from app.core.repo_indexer import FunctionRecord


class KnowledgeGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self):
        self.driver.close()

    def index_functions(self, records: list[FunctionRecord]) -> None:
        """Upsert functions and rebuild CALLS edges for the supplied functions."""
        if not records:
            return

        with self.driver.session() as session:
            names = [r.qualified_name for r in records]

            # Remove old edges first so repeated indexing cannot leave stale CALLS data.
            session.run(
                """
                MATCH (f:Function)
                WHERE f.qualified_name IN $names
                MATCH (f)-[r:CALLS]->()
                DELETE r
                """,
                names=names,
            )

            for r in records:
                session.run(
                    """
                    MERGE (f:Function {qualified_name: $qname})
                    SET f.name = $name
                    """,
                    qname=r.qualified_name,
                    name=r.name,
                )

            name_to_qname = {r.name: r.qualified_name for r in records}
            for r in records:
                for called_name in r.calls:
                    target_qname = name_to_qname.get(called_name)
                    if not target_qname or target_qname == r.qualified_name:
                        continue
                    session.run(
                        """
                        MATCH (a:Function {qualified_name: $src})
                        MATCH (b:Function {qualified_name: $dst})
                        MERGE (a)-[:CALLS]->(b)
                        """,
                        src=r.qualified_name,
                        dst=target_qname,
                    )

    def get_context(self, qualified_name: str) -> dict:
        with self.driver.session() as session:
            callers = session.run(
                """
                MATCH (caller:Function)-[:CALLS]->(f:Function {qualified_name: $qname})
                RETURN caller.qualified_name AS name
                """,
                qname=qualified_name,
            ).value()

            callees = session.run(
                """
                MATCH (f:Function {qualified_name: $qname})-[:CALLS]->(callee:Function)
                RETURN callee.qualified_name AS name
                """,
                qname=qualified_name,
            ).value()

        return {
            "callers": callers,
            "callees": callees,
            "fan_in": len(callers),
            "fan_out": len(callees),
        }
