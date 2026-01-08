import time
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from src.data_loader import DataLoader, DataChunk
from src.neo4j_manager import Neo4jManager, Entity, Relationship
from src.entity_extractor import EntityExtractor, ExtractionResult, ExtractedEntity, ExtractedRelationship


class GraphBuilder:
    def __init__(
        self,
        data_loader: DataLoader,
        neo4j_manager: Neo4jManager,
        entity_extractor: EntityExtractor,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        self.data_loader = data_loader
        self.neo4j_manager = neo4j_manager
        self.entity_extractor = entity_extractor
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def build_graph(
        self,
        chunks: Optional[List[DataChunk]] = None,
        show_progress: bool = True,
        clear_database: bool = True
    ) -> Dict[str, Any]:
        if clear_database:
            print("Clearing database...")
            self.neo4j_manager.clear_database()
            self.neo4j_manager.create_constraints()

        if chunks is None:
            print("Loading and chunking data...")
            chunks = self.data_loader.load_and_chunk()

        print(f"Processing {len(chunks)} chunks...")
        
        all_entities = {}
        all_relationships = []
        extraction_results = []
        
        chunks_iter = tqdm(chunks, desc="Extracting entities and relationships") if show_progress else chunks
        
        for chunk in chunks_iter:
            result = self._extract_with_retry(chunk)
            extraction_results.append(result)
            
            for entity in result.entities:
                entity_key = (entity.name, entity.type)
                if entity_key not in all_entities:
                    all_entities[entity_key] = Entity(
                        name=entity.name,
                        type=entity.type,
                        properties={"description": entity.description or ""}
                    )
            
            for rel in result.relationships:
                all_relationships.append(Relationship(
                    source=rel.source,
                    target=rel.target,
                    type=rel.type,
                    properties={"description": rel.description or ""}
                ))
        
        print(f"\nExtracted {len(all_entities)} unique entities and {len(all_relationships)} relationships")
        
        print("Storing entities in Neo4j...")
        entity_list = list(all_entities.values())
        entities_created = self._batch_create_with_retry(
            entity_list,
            self.neo4j_manager.batch_create_entities
        )
        
        print("Storing relationships in Neo4j...")
        relationships_created = self._batch_create_with_retry(
            all_relationships,
            self.neo4j_manager.batch_create_relationships
        )
        
        stats = {
            "chunks_processed": len(chunks),
            "entities_extracted": len(all_entities),
            "relationships_extracted": len(all_relationships),
            "entities_created": entities_created,
            "relationships_created": relationships_created,
            "extraction_stats": self.entity_extractor.get_extraction_stats(extraction_results)
        }
        
        return stats

    def _extract_with_retry(self, chunk: DataChunk) -> ExtractionResult:
        for attempt in range(self.max_retries):
            try:
                result = self.entity_extractor.extract(chunk.content)
                if result.entities or result.relationships:
                    return result
                else:
                    print(f"Warning: No entities/relationships extracted from chunk {chunk.metadata.get('chunk_id')}")
                    return result
            except Exception as e:
                if attempt < self.max_retries - 1:
                    print(f"Extraction failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Extraction failed after {self.max_retries} attempts: {e}")
                    return ExtractionResult(entities=[], relationships=[])

    def _batch_create_with_retry(
        self,
        items: List,
        create_func,
        batch_size: int = 100
    ) -> int:
        total_created = 0
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            for attempt in range(self.max_retries):
                try:
                    created = create_func(batch)
                    total_created += created
                    break
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        print(f"Batch creation failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                        time.sleep(self.retry_delay)
                    else:
                        print(f"Batch creation failed after {self.max_retries} attempts: {e}")
        return total_created

    def query_graph(self, query: str) -> List[Dict[str, Any]]:
        with self.neo4j_manager.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def get_entity_info(self, entity_name: str) -> Dict[str, Any]:
        relationships = self.neo4j_manager.get_entity_relationships(entity_name)
        
        return {
            "entity_name": entity_name,
            "total_relationships": len(relationships),
            "relationships": relationships
        }

    def find_connections(
        self,
        entity_name: str,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        with self.neo4j_manager.driver.session() as session:
            query = """
            MATCH (start:Entity {name: $name})-[r*1..$max_depth]-(end:Entity)
            RETURN start, r, end
            LIMIT 100
            """
            result = session.run(query, name=entity_name, max_depth=max_depth)
            return [record.data() for record in result]

    def get_graph_summary(self) -> Dict[str, Any]:
        stats = self.neo4j_manager.get_statistics()
        
        return {
            "total_entities": stats["total_entities"],
            "total_relationships": stats["total_relationships"],
            "entity_types": stats["entity_types"],
            "relationship_types": stats["relationship_types"]
        }

    def export_to_json(self, output_path: str) -> bool:
        try:
            summary = self.get_graph_summary()
            
            entities = []
            for entity_type in summary["entity_types"].keys():
                type_entities = self.neo4j_manager.get_entities_by_type(entity_type)
                entities.extend(type_entities)
            
            relationships = []
            for rel_type in summary["relationship_types"].keys():
                type_rels = self.neo4j_manager.get_relationships_by_type(rel_type)
                relationships.extend(type_rels)
            
            export_data = {
                "summary": summary,
                "entities": entities,
                "relationships": relationships
            }
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"Graph exported to {output_path}")
            return True
        except Exception as e:
            print(f"Export failed: {e}")
            return False

    def visualize_sample(self, entity_name: str, max_depth: int = 2) -> str:
        connections = self.find_connections(entity_name, max_depth)
        
        if not connections:
            return f"No connections found for entity: {entity_name}"
        
        viz_text = f"Knowledge Graph Sample (Center: {entity_name})\n"
        viz_text += "=" * 60 + "\n\n"
        
        for conn in connections[:20]:
            start = conn.get("start", {})
            end = conn.get("end", {})
            rels = conn.get("r", [])
            
            viz_text += f"{start.get('name', 'Unknown')} "
            for rel in rels:
                viz_text += f"-[{rel.get('type', 'UNKNOWN')}]-> "
            viz_text += f"{end.get('name', 'Unknown')}\n"
        
        return viz_text
