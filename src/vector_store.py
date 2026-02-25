import logging
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
import numpy as np


class VectorStore:
    """向量存储管理器，使用ChromaDB"""
    
    def __init__(self, persist_directory: str = './chroma_db'):
        """
        初始化向量存储
        
        Args:
            persist_directory: ChromaDB持久化目录
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.entity_collection = None
        self.relationship_collection = None
        self._initialize_collections()
    
    def _initialize_collections(self):
        """初始化实体和关系集合"""
        try:
            self.entity_collection = self.client.get_or_create_collection(
                name="entities",
                metadata={
                    "description": "实体向量集合",
                    "entity_types": "Patient, PatientId, Demographics, ChiefComplaint, PresentIllness, PastHistory, FamilyHistory, SocialHistory, Symptom, Sign, Diagnosis, Medication, Procedure, LabTest, LabValue, Imaging, Allergies, Treatment, Vitals, Duration, TemporalExpression, Material"
                }
            )
            
            self.relationship_collection = self.client.get_or_create_collection(
                name="relationships",
                metadata={
                    "description": "关系向量集合",
                    "relationship_types": "HAS_DIAGNOSIS, DIAGNOSIS_HAS_SYMPTOM, SYMPTOM_OF, MEDICATION_TREAT_FOR, MEDICATION_HAS_DOSE, LABTEST_HAS_VALUE, PROCEDURE_PERFORMED_ON, ALLERGY_TO, FAMILY_HISTORY_OF, CHIEF_COMPLAINT, MEDICAL_ADVICE, PROCEDURE_USES_MATERIAL, MATERIAL_HAS_COMPONENT, PROCEDURE_PERFORMED_BY, PROCEDURE_AIMS_TO_ACHIEVE, PATIENT_HAS_OCCUPATION, PATIENT_IS_FIRST_VISIT"
                }
            )
            
            logging.info("向量集合初始化成功")
        except Exception as e:
            logging.error(f"初始化向量集合失败: {e}")
            raise
    
    def add_entities(self, entities: List[Dict[str, Any]]) -> int:
        """
        添加实体到向量存储
        
        Args:
            entities: 实体列表，每个实体包含：
                - id: 实体ID
                - name: 实体名称
                - type: 实体类型
                - text_description: 文本描述
                - context_text: 上下文文本
                - chunk_ids: chunk_id列表
                - embedding: 嵌入向量（可选）
            
        Returns:
            添加的实体数量
        """
        added_count = 0
        for entity in entities:
            try:
                entity_id = entity.get('id', '')
                entity_name = entity.get('name', '')
                entity_type = entity.get('type', '')
                text_description = entity.get('text_description', '')
                context_text = entity.get('context_text', '')
                chunk_ids = entity.get('chunk_ids', [])
                embedding = entity.get('embedding')
                
                if not text_description:
                    logging.warning(f"实体 {entity_name} 缺少text_description，跳过")
                    continue
                
                metadata = {
                    'name': entity_name,
                    'type': entity_type,
                    'chunk_ids': str(chunk_ids) if isinstance(chunk_ids, list) else str([chunk_ids]),
                    'has_context': bool(context_text)
                }
                
                if embedding is None:
                    logging.warning(f"实体 {entity_name} 缺少嵌入向量，跳过")
                    continue
                
                self.entity_collection.add(
                    ids=[entity_id],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[text_description]
                )
                
                added_count += 1
                
            except Exception as e:
                logging.error(f"添加实体 {entity.get('name', '')} 失败: {e}")
        
        logging.info(f"成功添加 {added_count}/{len(entities)} 个实体到向量存储")
        return added_count
    
    def add_relationships(self, relationships: List[Dict[str, Any]]) -> int:
        """
        添加关系到向量存储
        
        Args:
            relationships: 关系列表，每个关系包含：
                - id: 关系ID
                - source: 源实体名称
                - target: 目标实体名称
                - type: 关系类型
                - relationship_text: 关系文本描述
                - chunk_ids: chunk_id列表
                - embedding: 嵌入向量（可选）
            
        Returns:
            添加的关系数量
        """
        added_count = 0
        for relationship in relationships:
            try:
                rel_id = relationship.get('id', '')
                source = relationship.get('source', '')
                target = relationship.get('target', '')
                rel_type = relationship.get('type', '')
                relationship_text = relationship.get('relationship_text', '')
                chunk_ids = relationship.get('chunk_ids', [])
                embedding = relationship.get('embedding')
                
                if not relationship_text:
                    logging.warning(f"关系 {source}->{target} 缺少relationship_text，跳过")
                    continue
                
                metadata = {
                    'source': source,
                    'target': target,
                    'type': rel_type,
                    'chunk_ids': str(chunk_ids) if isinstance(chunk_ids, list) else str([chunk_ids])
                }
                
                if embedding is None:
                    logging.warning(f"关系 {source}->{target} 缺少嵌入向量，跳过")
                    continue
                
                self.relationship_collection.add(
                    ids=[rel_id],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[relationship_text]
                )
                
                added_count += 1
                
            except Exception as e:
                logging.error(f"添加关系 {relationship.get('source', '')}->{relationship.get('target', '')} 失败: {e}")
        
        logging.info(f"成功添加 {added_count}/{len(relationships)} 个关系到向量存储")
        return added_count
    
    def search_entities(self, query_embedding: Optional[np.ndarray] = None, query_text: str = None, top_k: int = 5, 
                     entity_types: Optional[List[str]] = None,
                     min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        搜索相似的实体
        
        Args:
            query_embedding: 查询向量（优先使用）
            query_text: 查询文本（如果query_embedding为None时使用）
            top_k: 返回的最相似结果数量
            entity_types: 过滤的实体类型列表
            min_similarity: 最小相似度阈值
            
        Returns:
            相似实体列表
        """
        try:
            where_clause = {}
            if entity_types:
                where_clause['type'] = {'$or': [{'type': et} for et in entity_types]}
            
            query_embeddings = None
            if query_embedding is not None:
                if isinstance(query_embedding, np.ndarray):
                    query_embeddings = [query_embedding.tolist()]
                elif isinstance(query_embedding, list):
                    query_embeddings = [query_embedding]
            
            results = self.entity_collection.query(
                query_embeddings=query_embeddings,
                query_texts=[query_text] if query_text is not None and query_embeddings is None else None,
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            filtered_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    if results['distances'][0][i] <= (1 - min_similarity):
                        filtered_results.append({
                            'id': results['ids'][0][i],
                            'name': results['metadatas'][0][i]['name'],
                            'type': results['metadatas'][0][i]['type'],
                            'text_description': results['documents'][0][i],
                            'similarity': 1 - results['distances'][0][i],
                            'chunk_ids': eval(results['metadatas'][0][i]['chunk_ids'])
                        })
            
            logging.info(f"实体搜索完成，查询: '{query_text or 'vector'}'，找到 {len(filtered_results)} 个结果")
            if filtered_results:
                logging.info(f"检索到的实体详情:")
                for i, entity in enumerate(filtered_results, 1):
                    logging.info(f"  {i}. {entity['name']} ({entity['type']}) - 相似度: {entity['similarity']:.3f}")
                    logging.info(f"     描述: {entity['text_description'][:100]}{'...' if len(entity['text_description']) > 100 else ''}")
            return filtered_results
            
        except Exception as e:
            logging.error(f"搜索实体失败: {e}")
            return []
    
    def search_relationships(self, query_embedding: Optional[np.ndarray] = None, query_text: str = None, top_k: int = 5,
                        relationship_types: Optional[List[str]] = None,
                        min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        搜索相似的关系
        
        Args:
            query_embedding: 查询向量（优先使用）
            query_text: 查询文本（如果query_embedding为None时使用）
            top_k: 返回的最相似结果数量
            relationship_types: 过滤的关系类型列表
            min_similarity: 最小相似度阈值
            
        Returns:
            相似关系列表
        """
        try:
            where_clause = {}
            if relationship_types:
                where_clause['type'] = {'$or': [{'type': rt} for rt in relationship_types]}
            
            query_embeddings = None
            if query_embedding is not None:
                if isinstance(query_embedding, np.ndarray):
                    query_embeddings = [query_embedding.tolist()]
                elif isinstance(query_embedding, list):
                    query_embeddings = [query_embedding]
            
            results = self.relationship_collection.query(
                query_embeddings=query_embeddings,
                query_texts=[query_text] if query_text is not None and query_embeddings is None else None,
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            filtered_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    if results['distances'][0][i] <= (1 - min_similarity):
                        filtered_results.append({
                            'id': results['ids'][0][i],
                            'source': results['metadatas'][0][i]['source'],
                            'target': results['metadatas'][0][i]['target'],
                            'type': results['metadatas'][0][i]['type'],
                            'relationship_text': results['documents'][0][i],
                            'similarity': 1 - results['distances'][0][i],
                            'chunk_ids': eval(results['metadatas'][0][i]['chunk_ids'])
                        })
            
            logging.info(f"关系搜索完成，查询: '{query_text or 'vector'}'，找到 {len(filtered_results)} 个结果")
            if filtered_results:
                logging.info(f"检索到的关系详情:")
                for i, rel in enumerate(filtered_results, 1):
                    logging.info(f"  {i}. {rel['source']} -> {rel['target']} ({rel['type']}) - 相似度: {rel['similarity']:.3f}")
                    logging.info(f"     描述: {rel['relationship_text'][:100]}{'...' if len(rel['relationship_text']) > 100 else ''}")
            return filtered_results
            
        except Exception as e:
            logging.error(f"搜索关系失败: {e}")
            return []
    
    def search_hybrid(self, query_embedding: Optional[np.ndarray] = None, query_text: str = None, top_k: int = 5,
                   entity_types: Optional[List[str]] = None,
                   relationship_types: Optional[List[str]] = None,
                   min_similarity: float = 0.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        混合搜索（同时搜索实体和关系）
        
        Args:
            query_embedding: 查询向量（优先使用）
            query_text: 查询文本（如果query_embedding为None时使用）
            top_k: 返回的最相似结果数量
            entity_types: 过滤的实体类型列表
            relationship_types: 过滤的关系类型列表
            min_similarity: 最小相似度阈值
            
        Returns:
            包含entities和relationships的字典
        """
        entity_results = self.search_entities(
            query_embedding=query_embedding,
            query_text=query_text,
            top_k=top_k,
            entity_types=entity_types,
            min_similarity=min_similarity
        )
        
        relationship_results = self.search_relationships(
            query_embedding=query_embedding,
            query_text=query_text,
            top_k=top_k,
            relationship_types=relationship_types,
            min_similarity=min_similarity
        )
        
        return {
            'entities': entity_results,
            'relationships': relationship_results
        }
    
    def get_entity_count(self) -> int:
        """获取实体总数"""
        try:
            return self.entity_collection.count()
        except Exception as e:
            logging.error(f"获取实体数量失败: {e}")
            return 0
    
    def get_relationship_count(self) -> int:
        """获取关系总数"""
        try:
            return self.relationship_collection.count()
        except Exception as e:
            logging.error(f"获取关系数量失败: {e}")
            return 0
    
    def clear_all(self):
        """清空所有向量数据"""
        try:
            self.client.delete_collection("entities")
            self.client.delete_collection("relationships")
            self._initialize_collections()
            logging.info("向量存储已清空")
        except Exception as e:
            logging.error(f"清空向量存储失败: {e}")
    
    def persist(self):
        """持久化向量数据到磁盘"""
        logging.info(f"持久化向量数据到: {self.persist_directory}")


def main():
    """测试向量存储功能"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        store = VectorStore(persist_directory='./test_chroma_db')
        
        test_entities = [
            {
                'id': 'entity_1',
                'name': 'Alex Mercer',
                'type': 'Character',
                'text_description': 'Alex Mercer is a Character. Agent in Paranormal Military Squad.',
                'context_text': 'Agent Alex Mercer, unfailingly determined on paper, seemed dwarfed by the enormity of the sterile briefing room where Paranormal Military Squad\'s elite convened.',
                'chunk_ids': [0, 1],
                'embedding': [0.1, 0.2, 0.3]
            },
            {
                'id': 'entity_2',
                'name': 'Jordan Hayes',
                'type': 'Character',
                'text_description': 'Jordan Hayes is a Character.',
                'context_text': 'Jordan Hayes, perched on the opposite side of the table, narrowed their eyes but offered a supportive nod.',
                'chunk_ids': [0],
                'embedding': [0.4, 0.5, 0.6]
            }
        ]
        
        print("测试添加实体...")
        store.add_entities(test_entities)
        
        print("\n测试搜索实体...")
        results = store.search_entities("Alex Mercer", top_k=2)
        for result in results:
            print(f"  - {result['name']} (相似度: {result['similarity']:.2f})")
        
        print(f"\n实体总数: {store.get_entity_count()}")
        print(f"关系总数: {store.get_relationship_count()}")
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
