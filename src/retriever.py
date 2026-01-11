import logging
from typing import List, Dict, Any, Optional, Tuple
from src.vector_store import VectorStore
from src.embedding_manager import EmbeddingManager


class Retriever:
    """检索器，基于向量存储进行相似度搜索"""
    
    def __init__(self, vector_store: VectorStore, embedding_manager: EmbeddingManager):
        """
        初始化检索器
        
        Args:
            vector_store: 向量存储实例
            embedding_manager: 嵌入管理器实例
        """
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
    
    def retrieve_entities(self, query: str, top_k: int = 5,
                         entity_types: Optional[List[str]] = None,
                         min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        检索相似的实体
        
        Args:
            query: 查询文本
            top_k: 返回的最相似结果数量
            entity_types: 过滤的实体类型列表
            min_similarity: 最小相似度阈值（0-1之间）
            
        Returns:
            相似实体列表
        """
        logging.info(f"开始实体检索，查询: '{query}'")
        
        query_embedding = self.embedding_manager.embed_text(query)
        results = self.vector_store.search_entities(
            query_text=query,
            top_k=top_k,
            entity_types=entity_types,
            min_similarity=min_similarity
        )
        
        logging.info(f"实体检索完成，找到 {len(results)} 个结果")
        return results
    
    def retrieve_relationships(self, query: str, top_k: int = 5,
                             relationship_types: Optional[List[str]] = None,
                             min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """
        检索相似的关系
        
        Args:
            query: 查询文本
            top_k: 返回的最相似结果数量
            relationship_types: 过滤的关系类型列表
            min_similarity: 最小相似度阈值（0-1之间）
            
        Returns:
            相似关系列表
        """
        logging.info(f"开始关系检索，查询: '{query}'")
        
        query_embedding = self.embedding_manager.embed_text(query)
        results = self.vector_store.search_relationships(
            query_text=query,
            top_k=top_k,
            relationship_types=relationship_types,
            min_similarity=min_similarity
        )
        
        logging.info(f"关系检索完成，找到 {len(results)} 个结果")
        return results
    
    def retrieve_hybrid(self, query: str, top_k: int = 5,
                       entity_types: Optional[List[str]] = None,
                       relationship_types: Optional[List[str]] = None,
                       min_similarity: float = 0.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        混合检索（同时搜索实体和关系）
        
        Args:
            query: 查询文本
            top_k: 返回的最相似结果数量
            entity_types: 过滤的实体类型列表
            relationship_types: 过滤的关系类型列表
            min_similarity: 最小相似度阈值（0-1之间）
            
        Returns:
            包含entities和relationships的字典
        """
        logging.info(f"开始混合检索，查询: '{query}'")
        
        query_embedding = self.embedding_manager.embed_text(query)
        results = self.vector_store.search_hybrid(
            query_text=query,
            top_k=top_k,
            entity_types=entity_types,
            relationship_types=relationship_types,
            min_similarity=min_similarity
        )
        
        logging.info(f"混合检索完成，找到 {len(results['entities'])} 个实体，{len(results['relationships'])} 个关系")
        return results
    
    def retrieve_contextual(self, query: str, entity_name: str, 
                           context_window: int = 200, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        上下文增强检索：基于特定实体检索其周围的上下文
        
        Args:
            query: 查询文本
            entity_name: 目标实体名称
            context_window: 上下文窗口大小（字符数）
            top_k: 返回的最相似结果数量
            
        Returns:
            上下文相关的实体列表
        """
        logging.info(f"开始上下文检索，查询: '{query}'，目标实体: '{entity_name}'")
        
        query_embedding = self.embedding_manager.embed_text(query)
        results = self.vector_store.search_entities(
            query_text=query,
            top_k=top_k * 2,
            min_similarity=0.0
        )
        
        filtered_results = []
        for result in results:
            result_name = result.get('name', '')
            if entity_name.lower() in result_name.lower():
                filtered_results.append(result)
            
            if len(filtered_results) >= top_k:
                break
        
        logging.info(f"上下文检索完成，找到 {len(filtered_results)} 个结果")
        return filtered_results
    
    def format_retrieval_results(self, results: List[Dict[str, Any]], 
                                result_type: str = 'entity') -> str:
        """
        格式化检索结果为可读文本
        
        Args:
            results: 检索结果列表
            result_type: 结果类型（'entity' 或 'relationship'）
            
        Returns:
            格式化的文本
        """
        if not results:
            return f"未找到相关的{result_type}。"
        
        formatted_lines = [f"找到 {len(results)} 个相关的{result_type}：\n"]
        
        for i, result in enumerate(results, 1):
            if result_type == 'entity':
                formatted_lines.append(
                    f"{i}. {result.get('name', '')} ({result.get('type', '')})\n"
                    f"   描述: {result.get('text_description', '')}\n"
                    f"   相似度: {result.get('similarity', 0):.2f}\n"
                )
            else:
                formatted_lines.append(
                    f"{i}. {result.get('source', '')} {result.get('type', '')} {result.get('target', '')}\n"
                    f"   描述: {result.get('relationship_text', '')}\n"
                    f"   相似度: {result.get('similarity', 0):.2f}\n"
                )
        
        return '\n'.join(formatted_lines)


def main():
    """测试检索器功能"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        from src.embedding_manager import EmbeddingManager
        from src.vector_store import VectorStore
        
        embedding_manager = EmbeddingManager(model_name='all-MiniLM-L6-v2')
        vector_store = VectorStore(persist_directory='./test_chroma_db')
        
        retriever = Retriever(vector_store, embedding_manager)
        
        print("测试实体检索...")
        results = retriever.retrieve_entities("Alex Mercer", top_k=3)
        print(retriever.format_retrieval_results(results, 'entity'))
        
        print("\n测试关系检索...")
        results = retriever.retrieve_relationships("PART_OF", top_k=3)
        print(retriever.format_retrieval_results(results, 'relationship'))
        
        print("\n测试混合检索...")
        results = retriever.retrieve_hybrid("team", top_k=3)
        print(f"实体: {len(results['entities'])} 个")
        print(f"关系: {len(results['relationships'])} 个")
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
