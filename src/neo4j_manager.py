from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from pydantic import BaseModel


class Entity(BaseModel):
    name: str
    type: str
    properties: Dict[str, Any] = {}


class Relationship(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}


class Neo4jManager:
    def __init__(self, uri: str, username: str, password: str):
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None

    def connect(self):
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        self.driver.verify_connectivity()
        print(f"Connected to Neo4j at {self.uri}")

    def close(self):
        if self.driver:
            self.driver.close()
            print("Neo4j connection closed")

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared")

    def create_constraints(self):
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE",
                "CREATE CONSTRAINT entity_type IF NOT EXISTS FOR (n:Entity) REQUIRE n.type IS NOT NULL"
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Constraint creation warning: {e}")

    def create_entity(self, entity: Entity) -> bool:
        with self.driver.session() as session:
            query = """
            MERGE (e:Entity {name: $name, type: $type})
            SET e += $properties
            RETURN e
            """
            result = session.run(
                query,
                name=entity.name,
                type=entity.type,
                properties=entity.properties
            )
            return result.single() is not None

    def create_relationship(self, relationship: Relationship) -> bool:
        with self.driver.session() as session:
            query = """
            MATCH (source:Entity {name: $source})
            MATCH (target:Entity {name: $target})
            MERGE (source)-[r:RELATIONSHIP {type: $type}]->(target)
            SET r += $properties
            RETURN r
            """
            result = session.run(
                query,
                source=relationship.source,
                target=relationship.target,
                type=relationship.type,
                properties=relationship.properties
            )
            return result.single() is not None

    def batch_create_entities(self, entities: List[Entity]) -> int:
        created = 0
        with self.driver.session() as session:
            for entity in entities:
                query = """
                MERGE (e:Entity {name: $name, type: $type})
                SET e += $properties
                """
                session.run(
                    query,
                    name=entity.name,
                    type=entity.type,
                    properties=entity.properties
                )
                created += 1
        return created

    def batch_create_relationships(self, relationships: List[Relationship]) -> int:
        created = 0
        with self.driver.session() as session:
            for rel in relationships:
                query = """
                MATCH (source:Entity {name: $source})
                MATCH (target:Entity {name: $target})
                MERGE (source)-[r:RELATIONSHIP {type: $type}]->(target)
                SET r += $properties
                """
                session.run(
                    query,
                    source=rel.source,
                    target=rel.target,
                    type=rel.type,
                    properties=rel.properties
                )
                created += 1
        return created

    def get_entity_count(self) -> int:
        with self.driver.session() as session:
            result = session.run("MATCH (n:Entity) RETURN count(n) as count")
            return result.single()["count"]

    def get_relationship_count(self) -> int:
        with self.driver.session() as session:
            result = session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN count(r) as count")
            return result.single()["count"]

    def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (e:Entity {type: $type}) RETURN e",
                type=entity_type
            )
            return [record["e"] for record in result]

    def get_relationships_by_type(self, rel_type: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (source:Entity)-[r:RELATIONSHIP {type: $type}]->(target:Entity)
                RETURN source, r, target
                """,
                type=rel_type
            )
            return [record.data() for record in result]

    def get_entity_relationships(self, entity_name: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity {name: $name})-[r:RELATIONSHIP]->(other:Entity)
                RETURN e, r, other
                UNION
                MATCH (other:Entity)-[r:RELATIONSHIP]->(e:Entity {name: $name})
                RETURN other, r, e
                """,
                name=entity_name
            )
            return [record.data() for record in result]

    def find_path(self, source_name: str, target_name: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = shortestPath(
                    (source:Entity {name: $source})-[*1..$max_depth]-(target:Entity {name: $target})
                )
                RETURN path
                """,
                source=source_name,
                target=target_name,
                max_depth=max_depth
            )
            return [record["path"] for record in result]

    def get_statistics(self) -> Dict[str, Any]:
        with self.driver.session() as session:
            entity_types = session.run("""
                MATCH (e:Entity)
                RETURN e.type as type, count(e) as count
                ORDER BY count DESC
            """)
            
            relationship_types = session.run("""
                MATCH ()-[r:RELATIONSHIP]->()
                RETURN r.type as type, count(r) as count
                ORDER BY count DESC
            """)
            
            return {
                "total_entities": self.get_entity_count(),
                "total_relationships": self.get_relationship_count(),
                "entity_types": {record["type"]: record["count"] for record in entity_types},
                "relationship_types": {record["type"]: record["count"] for record in relationship_types}
            }
