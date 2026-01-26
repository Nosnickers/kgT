import json
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path


class TextGenerator:
    """从Neo4j知识图谱和原始数据生成文本描述的类"""
    
    def __init__(self, neo4j_manager, csv_file_path: str):
        """
        初始化文本生成器
        
        Args:
            neo4j_manager: Neo4j管理器实例
            csv_file_path: CSV文件路径，包含原始文本数据
        """
        self.neo4j_manager = neo4j_manager
        self.csv_file_path = csv_file_path
        self.chunk_data = self._load_chunk_data()
    
    def _load_chunk_data(self) -> Dict[int, str]:
        """从CSV文件加载chunk数据"""
        chunk_data = {}
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chunk_id = int(row.get('chunk_id', -1))
                    content = row.get('content', '')
                    chunk_data[chunk_id] = content
            logging.info(f"成功加载 {len(chunk_data)} 个chunk数据")
        except Exception as e:
            logging.error(f"加载CSV文件失败: {e}")
            return {}
        
        return chunk_data
    
    def generate_text_for_entity(self, entity: Dict[str, Any], chunk_ids: List[int]) -> Dict[str, str]:
        """
        为实体生成文本描述和上下文文本
        
        Args:
            entity: 实体数据字典，包含name, type, description, chunk_id
            chunk_ids: 实体关联的chunk_id列表
            
        Returns:
            包含text_description和context_text的字典
        """
        entity_name = entity.get('name', '')
        entity_type = entity.get('type', '')
        entity_description = entity.get('description', '')
        
        text_description = f"{entity_name} is a {entity_type}"
        if entity_description:
            text_description += f". {entity_description}"
        
        context_text = self._generate_context_text(chunk_ids, entity_name)
        
        return {
            'text_description': text_description,
            'context_text': context_text
        }
    
    def generate_text_for_relationship(self, relationship: Dict[str, Any], chunk_ids: List[int]) -> Dict[str, str]:
        """
        为关系生成文本描述
        
        Args:
            relationship: 关系数据字典，包含source, target, type, description, chunk_id
            chunk_ids: 关系关联的chunk_id列表
            
        Returns:
            包含relationship_text的字典
        """
        source = relationship.get('source', '')
        target = relationship.get('target', '')
        rel_type = relationship.get('type', '')
        rel_description = relationship.get('description', '')
        
        relationship_text = f"{source} {rel_type} {target}"
        if rel_description:
            relationship_text += f". {rel_description}"
        
        return {
            'relationship_text': relationship_text
        }
    
    def _generate_context_text(self, chunk_ids: List[int], entity_name: str, context_window: int = 200) -> str:
        """
        生成包含实体周围上下文的文本
        
        Args:
            chunk_ids: chunk_id列表
            entity_name: 实体名称
            context_window: 上下文窗口大小（字符数）
            
        Returns:
            上下文文本
        """
        context_parts = []
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_data:
                text = self.chunk_data[chunk_id]
                if entity_name in text:
                    entity_pos = text.find(entity_name)
                    if entity_pos != -1:
                        start = max(0, entity_pos - context_window)
                        end = min(len(text), entity_pos + len(entity_name) + context_window)
                        context_part = text[start:end]
                        context_parts.append(context_part)
        
        return ' '.join(context_parts)
    
    def generate_all_texts(self, output_file: str = 'oral_kg_index.json') -> bool:
        """
        为所有实体和关系生成文本描述并保存到JSON文件
        
        Args:
            output_file: 输出JSON文件路径
            
        Returns:
            是否成功
        """
        logging.info("开始生成文本描述...")
        
        entities = self._get_all_entities()
        relationships = self._get_all_relationships()
        
        enhanced_entities = []
        enhanced_relationships = []
        
        for entity in entities:
            chunk_ids = entity.get('chunk_id', [])
            if not isinstance(chunk_ids, list):
                chunk_ids = [chunk_ids]
            
            texts = self.generate_text_for_entity(entity, chunk_ids)
            enhanced_entity = {
                'id': f"entity_{entity.get('name', '').replace(' ', '_').lower()}",
                'name': entity.get('name', ''),
                'type': entity.get('type', ''),
                'description': entity.get('description', ''),
                'text_description': texts['text_description'],
                'context_text': texts['context_text'],
                'chunk_ids': chunk_ids
            }
            enhanced_entities.append(enhanced_entity)
        
        for relationship in relationships:
            chunk_ids = relationship.get('chunk_id', [])
            if not isinstance(chunk_ids, list):
                chunk_ids = [chunk_ids]
            
            texts = self.generate_text_for_relationship(relationship, chunk_ids)
            enhanced_relationship = {
                'id': f"rel_{relationship.get('source', '').replace(' ', '_').lower()}_{relationship.get('target', '').replace(' ', '_').lower()}_{relationship.get('type', '')}",
                'source': relationship.get('source', ''),
                'target': relationship.get('target', ''),
                'type': relationship.get('type', ''),
                'description': relationship.get('description', ''),
                'relationship_text': texts['relationship_text'],
                'chunk_ids': chunk_ids
            }
            enhanced_relationships.append(enhanced_relationship)
        
        output_data = {
            'entities': enhanced_entities,
            'relationships': enhanced_relationships,
            'metadata': {
                'total_entities': len(enhanced_entities),
                'total_relationships': len(enhanced_relationships),
                'source_csv': self.csv_file_path
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logging.info(f"成功生成文本描述并保存到: {output_file}")
            logging.info(f"生成 {len(enhanced_entities)} 个实体文本描述")
            logging.info(f"生成 {len(enhanced_relationships)} 个关系文本描述")
            return True
        except Exception as e:
            logging.error(f"保存文本描述失败: {e}")
            return False
    
    def _get_all_entities(self) -> List[Dict[str, Any]]:
        """从Neo4j获取所有实体"""
        entities = []
        try:
            with self.neo4j_manager.driver.session() as session:
                result = session.run("MATCH (e:Entity) RETURN e")
                for record in result:
                    entity_dict = {
                        'name': record['e']['name'],
                        'type': record['e']['type'],
                        'description': record['e'].get('description', ''),
                        'chunk_id': record['e'].get('chunk_id', [])
                    }
                    entities.append(entity_dict)
            logging.info(f"从Neo4j获取到 {len(entities)} 个实体")
        except Exception as e:
            logging.error(f"获取实体失败: {e}")
        
        return entities
    
    def _get_all_relationships(self) -> List[Dict[str, Any]]:
        """从Neo4j获取所有关系"""
        relationships = []
        try:
            with self.neo4j_manager.driver.session() as session:
                result = session.run("""
                    MATCH (source:Entity)-[r:RELATIONSHIP]->(target:Entity)
                    RETURN source, r, target
                """)
                for record in result:
                    rel_dict = {
                        'source': record['source']['name'],
                        'target': record['target']['name'],
                        'type': record['r']['type'],
                        'description': record['r'].get('description', ''),
                        'chunk_id': record['r'].get('chunk_id', [])
                    }
                    relationships.append(rel_dict)
            logging.info(f"从Neo4j获取到 {len(relationships)} 个关系")
        except Exception as e:
            logging.error(f"获取关系失败: {e}")
        
        return relationships


def main():
    """测试文本生成功能"""
    import sys
    sys.path.append(str(Path(__file__).parent))
    
    from config import Config
    from src.neo4j_manager import Neo4jManager
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        config = Config.from_env()
        neo4j_manager = Neo4jManager(
            uri=config.neo4j.uri,
            username=config.neo4j.username,
            password=config.neo4j.password
        )
        neo4j_manager.connect()
        
        csv_file = config.data.file_path.replace('.json', '.csv')
        if not Path(csv_file).exists():
            logging.error(f"CSV文件不存在: {csv_file}")
            return
        
        text_generator = TextGenerator(neo4j_manager, csv_file)
        success = text_generator.generate_all_texts()
        
        if success:
            print("文本描述生成成功！")
        else:
            print("文本描述生成失败！")
        
        neo4j_manager.close()
        
    except Exception as e:
        logging.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
