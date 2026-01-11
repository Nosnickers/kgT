import logging
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path


class EmbeddingManager:
    """嵌入管理器，支持多种嵌入模型"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_embeddings: bool = True):
        """
        初始化嵌入管理器
        
        Args:
            model_name: 嵌入模型名称或本地路径
                - 'all-MiniLM-L6-v2': 轻量级英文模型（384维）
                - 'paraphrase-multilingual-MiniLM-L12-v2': 多语言模型（384维）
                - 'all-mpnet-base-v2': 更好的英文模型（768维）
                - 本地路径：'C:\\path\\to\\local\\model' 或 '/path/to/local/model'
            cache_embeddings: 是否缓存嵌入结果
        """
        self.model_name = model_name
        self.cache_embeddings = cache_embeddings
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载嵌入模型"""
        try:
            logging.info(f"正在加载嵌入模型: {self.model_name}")
            
            model_path = Path(self.model_name)
            
            if model_path.exists() or '\\' in self.model_name or '/' in self.model_name:
                logging.info(f"使用本地模型路径: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
            else:
                logging.info(f"从 Hugging Face Hub 下载模型: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
            
            logging.info(f"嵌入模型加载成功，向量维度: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            logging.error(f"加载嵌入模型失败: {e}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        将单个文本转换为向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量（numpy数组）
        """
        if self.cache_embeddings and text in self.embedding_cache:
            return self.embedding_cache[text]
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            if self.cache_embeddings:
                self.embedding_cache[text] = embedding
            return embedding
        except Exception as e:
            logging.error(f"嵌入文本失败: {e}")
            raise
    
    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        批量将多个文本转换为向量
        
        Args:
            texts: 输入文本列表
            batch_size: 批量大小
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_embeddings = self.model.encode(batch, convert_to_numpy=True)
                embeddings.extend(batch_embeddings)
                
                if self.cache_embeddings:
                    for text, embedding in zip(batch, batch_embeddings):
                        self.embedding_cache[text] = embedding
                        
            except Exception as e:
                logging.error(f"批量嵌入失败（批次 {i//batch_size}）: {e}")
                raise
        
        return embeddings
    
    def embed_entities(self, entities: List[Dict[str, Any]], text_field: str = 'text_description') -> List[Dict[str, Any]]:
        """
        为实体列表生成嵌入
        
        Args:
            entities: 实体列表
            text_field: 用于嵌入的文本字段名（默认为text_description）
            
        Returns:
            带嵌入向量的实体列表
        """
        texts = [entity.get(text_field, '') for entity in entities]
        embeddings = self.embed_texts(texts)
        
        for entity, embedding in zip(entities, embeddings):
            entity['embedding'] = embedding.tolist()
        
        return entities
    
    def embed_relationships(self, relationships: List[Dict[str, Any]], text_field: str = 'relationship_text') -> List[Dict[str, Any]]:
        """
        为关系列表生成嵌入
        
        Args:
            relationships: 关系列表
            text_field: 用于嵌入的文本字段名（默认为relationship_text）
            
        Returns:
            带嵌入向量的关系列表
        """
        texts = [relationship.get(text_field, '') for relationship in relationships]
        embeddings = self.embed_texts(texts)
        
        for relationship, embedding in zip(relationships, embeddings):
            relationship['embedding'] = embedding.tolist()
        
        return relationships
    
    def get_embedding_dimension(self) -> int:
        """
        获取嵌入向量的维度
        
        Returns:
            向量维度
        """
        if self.model:
            return self.model.get_sentence_embedding_dimension()
        return 0
    
    def clear_cache(self):
        """清空嵌入缓存"""
        self.embedding_cache.clear()
        logging.info("嵌入缓存已清空")
    
    def save_cache(self, cache_file: str = 'embedding_cache.npz'):
        """
        保存嵌入缓存到文件
        
        Args:
            cache_file: 缓存文件路径
        """
        try:
            np.savez(cache_file, **self.embedding_cache)
            logging.info(f"嵌入缓存已保存到: {cache_file}")
        except Exception as e:
            logging.error(f"保存嵌入缓存失败: {e}")
    
    def load_cache(self, cache_file: str = 'embedding_cache.npz'):
        """
        从文件加载嵌入缓存
        
        Args:
            cache_file: 缓存文件路径
        """
        try:
            if Path(cache_file).exists():
                cache_data = np.load(cache_file)
                self.embedding_cache = {k: v for k, v in cache_data.items()}
                logging.info(f"嵌入缓存已从 {cache_file} 加载，共 {len(self.embedding_cache)} 条")
        except Exception as e:
            logging.warning(f"加载嵌入缓存失败: {e}")


def main():
    """测试嵌入管理器"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        manager = EmbeddingManager(model_name='all-MiniLM-L6-v2')
        
        test_texts = [
            "Alex Mercer is a Character",
            "Jordan Hayes is a Character",
            "Paranormal Military Squad is an Organization"
        ]
        
        print("测试单个文本嵌入...")
        embedding = manager.embed_text("Alex Mercer is a Character")
        print(f"向量维度: {len(embedding)}")
        print(f"向量前5个值: {embedding[:5]}")
        
        print("\n测试批量文本嵌入...")
        embeddings = manager.embed_texts(test_texts)
        print(f"生成了 {len(embeddings)} 个向量")
        print(f"每个向量维度: {embeddings[0].shape}")
        
        print(f"\n嵌入向量维度: {manager.get_embedding_dimension()}")
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
