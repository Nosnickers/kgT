from src.vector_store import VectorStore
from src.embedding_manager import EmbeddingManager
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)

vs = VectorStore('./chroma_db')
em = EmbeddingManager()

# 获取所有实体及其嵌入向量
all_entities = vs.entity_collection.get(include=['metadatas', 'documents', 'embeddings'])
print(f'Total entities: {len(all_entities["ids"])}')

# 生成查询向量
query_text = 'Alex Mercer'
query_emb = em.embed_text(query_text)
print(f'\nQuery: "{query_text}"')
print(f'Query embedding shape: {query_emb.shape}')

# 手动计算与所有实体的相似度
print('\nCalculating similarities with all entities:')
similarities = []
for i, entity_id in enumerate(all_entities['ids']):
    entity_name = all_entities['metadatas'][i]['name']
    entity_type = all_entities['metadatas'][i]['type']
    entity_emb = all_entities['embeddings'][i]
    
    if entity_emb is not None:
        # 计算余弦相似度
        dot_product = np.dot(entity_emb, query_emb)
        norm_entity = np.linalg.norm(entity_emb)
        norm_query = np.linalg.norm(query_emb)
        cosine_similarity = dot_product / (norm_entity * norm_query)
        
        similarities.append({
            'id': entity_id,
            'name': entity_name,
            'type': entity_type,
            'similarity': cosine_similarity
        })

# 按相似度排序
similarities.sort(key=lambda x: x['similarity'], reverse=True)

# 显示前10个最相似的实体
print('\nTop 10 most similar entities:')
for i, sim in enumerate(similarities[:10], 1):
    print(f'  {i}. {sim["name"]} ({sim["type"]}): {sim["similarity"]:.4f}')