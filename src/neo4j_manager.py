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
        import logging
        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        self.driver.verify_connectivity()
        logging.info(f"Connected to Neo4j at {self.uri}")

    def close(self):
        import logging
        if self.driver:
            self.driver.close()
            logging.info("Neo4j connection closed")

    def clear_database(self):
        import logging
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logging.info("Database cleared")

    def create_constraints(self):
        import logging
        with self.driver.session() as session:
            # 删除旧的唯一约束（只基于name的约束）
            try:
                # 先检查约束是否存在，然后删除
                result = session.run("SHOW CONSTRAINTS")
                constraints = [record["name"] for record in result]
                if "entity_name" in constraints:
                    session.run("DROP CONSTRAINT entity_name")
            except Exception as e:
                logging.warning(f"Constraint drop warning: {e}")
            
            # 创建新的复合唯一约束（基于name和type）
            constraints = [
                "CREATE CONSTRAINT entity_name_type IF NOT EXISTS FOR (n:Entity) REQUIRE (n.name, n.type) IS UNIQUE",
                "CREATE CONSTRAINT entity_type IF NOT EXISTS FOR (n:Entity) REQUIRE n.type IS NOT NULL"
            ]
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logging.warning(f"Constraint creation warning: {e}")

    def create_entity(self, entity: Entity) -> bool:
        with self.driver.session() as session:
            # 清理实体数据，去除两端的引号
            entity_name = entity.name.strip('"\'')
            entity_type = entity.type.strip('"\'')
            entity_properties = entity.properties.copy()
            if 'description' in entity_properties and entity_properties['description']:
                entity_properties['description'] = entity_properties['description'].strip('"\'')
            
            query = """
            MERGE (e:Entity {name: $name, type: $type})
            SET e += $properties
            RETURN e
            """
            result = session.run(
                query,
                name=entity_name,
                type=entity_type,
                properties=entity_properties
            )
            return result.single() is not None

    def create_relationship(self, relationship: Relationship) -> bool:
        with self.driver.session() as session:
            # 清理关系数据，去除两端的引号
            rel_source = relationship.source.strip('"\'')
            rel_target = relationship.target.strip('"\'')
            rel_type = relationship.type.strip('"\'')
            rel_properties = relationship.properties.copy()
            if 'description' in rel_properties and rel_properties['description']:
                rel_properties['description'] = rel_properties['description'].strip('"\'')
            
            query = """
            MATCH (source:Entity {name: $source})
            MATCH (target:Entity {name: $target})
            MERGE (source)-[r:RELATIONSHIP {type: $type}]->(target)
            SET r += $properties
            RETURN r
            """
            result = session.run(
                query,
                source=rel_source,
                target=rel_target,
                type=rel_type,
                properties=rel_properties
            )
            return result.single() is not None

    def batch_create_entities(self, entities: List[Entity]) -> int:
        created = 0
        with self.driver.session() as session:
            for entity in entities:
                # 清理实体数据，去除两端的引号
                entity_name = entity.name.strip('"\'')
                entity_type = entity.type.strip('"\'')
                entity_properties = entity.properties.copy()
                if 'description' in entity_properties and entity_properties['description']:
                    entity_properties['description'] = entity_properties['description'].strip('"\'')
                
                # 处理chunk_id数组
                chunk_id = entity_properties.get('chunk_id', [])
                if not isinstance(chunk_id, list):
                    chunk_id = [chunk_id]
                entity_properties['chunk_id'] = chunk_id
                
                query = """
                MERGE (e:Entity {name: $name, type: $type})
                ON CREATE SET e += $properties
                ON MATCH SET 
                    e.description = COALESCE($properties.description, e.description),
                    e.chunk_id = $properties.chunk_id
                """
                session.run(
                    query,
                    name=entity_name,
                    type=entity_type,
                    properties=entity_properties
                )
                created += 1
        return created

    def batch_create_relationships(self, relationships: List[Relationship]) -> int:
        created = 0
        with self.driver.session() as session:
            for rel in relationships:
                # 清理关系数据，去除两端的引号
                rel_source = rel.source.strip('"\'')
                rel_target = rel.target.strip('"\'')
                rel_type = rel.type.strip('"\'')
                rel_properties = rel.properties.copy()
                if 'description' in rel_properties and rel_properties['description']:
                    rel_properties['description'] = rel_properties['description'].strip('"\'')
                
                # 处理chunk_id数组
                chunk_id = rel_properties.get('chunk_id', [])
                if not isinstance(chunk_id, list):
                    chunk_id = [chunk_id]
                rel_properties['chunk_id'] = chunk_id
                
                query = """
                MATCH (source:Entity {name: $source})
                MATCH (target:Entity {name: $target})
                MERGE (source)-[r:RELATIONSHIP {type: $type}]->(target)
                ON CREATE SET r += $properties
                ON MATCH SET 
                    r.description = COALESCE($properties.description, r.description),
                    r.chunk_id = $properties.chunk_id
                """
                session.run(
                    query,
                    source=rel_source,
                    target=rel_target,
                    type=rel_type,
                    properties=rel_properties
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
