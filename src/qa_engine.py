import logging
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from src.retriever import Retriever


class QAEngine:
    """问答引擎，结合向量检索和LLM生成答案"""
    
    def __init__(self, retriever: Retriever, 
                 llm_base_url: str = "http://localhost:11434",
                 llm_model: str = "deepseek-r1:8b",
                 llm_temperature: float = 0.7):
        """
        初始化问答引擎
        
        Args:
            retriever: 检索器实例
            llm_base_url: LLM基础URL
            llm_model: LLM模型名称
            llm_temperature: LLM温度参数
        """
        self.retriever = retriever
        self.llm = ChatOllama(
            base_url=llm_base_url,
            model=llm_model,
            temperature=llm_temperature
        )
        self.conversation_history: List[Dict[str, Any]] = []
    
    def _build_context_prompt(self, query: str, retrieval_results: Dict[str, Any]) -> str:
        """
        构建包含检索知识的提示词
        
        Args:
            query: 用户问题
            retrieval_results: 检索结果
            
        Returns:
            提示词字符串
        """
        entities = retrieval_results.get('entities', [])
        relationships = retrieval_results.get('relationships', [])
        
        context_parts = []
        
        if entities:
            context_parts.append("相关实体：")
            for entity in entities[:3]:
                context_parts.append(
                    f"- {entity.get('name', '')} ({entity.get('type', '')}): "
                    f"{entity.get('text_description', '')}"
                )
        
        if relationships:
            context_parts.append("\n相关关系：")
            for rel in relationships[:3]:
                context_parts.append(
                    f"- {rel.get('source', '')} {rel.get('type', '')} {rel.get('target', '')}: "
                    f"{rel.get('relationship_text', '')}"
                )
        
        context = '\n'.join(context_parts)
        
        return f"""基于以下知识回答问题：

{context}

问题：{query}

请基于上述知识提供准确、详细的答案。如果知识中没有相关信息，请明确说明。"""
    
    def _build_conversational_prompt(self, query: str) -> str:
        """
        构建对话式提示词（包含历史记录）
        
        Args:
            query: 用户问题
            
        Returns:
            提示词字符串
        """
        if not self.conversation_history:
            return f"问题：{query}"
        
        history_parts = []
        for i, turn in enumerate(self.conversation_history[-5:]):
            history_parts.append(f"用户：{turn.get('user', '')}")
            history_parts.append(f"助手：{turn.get('assistant', '')}")
        
        history_text = '\n'.join(history_parts)
        return f"""对话历史：
{history_text}

当前问题：{query}

请基于对话历史和当前问题提供准确、连贯的答案。"""
    
    def answer(self, query: str, retrieval_mode: str = 'hybrid',
               top_k: int = 5, entity_types: Optional[List[str]] = None,
               relationship_types: Optional[List[str]] = None,
               min_similarity: float = 0.0,
               use_conversation: bool = False) -> Dict[str, Any]:
        """
        回答用户问题
        
        Args:
            query: 用户问题
            retrieval_mode: 检索模式（'entity', 'relationship', 'hybrid', 'contextual'）
            top_k: 返回的最相似结果数量
            entity_types: 过滤的实体类型列表
            relationship_types: 过滤的关系类型列表
            min_similarity: 最小相似度阈值
            use_conversation: 是否使用对话历史
            
        Returns:
            包含答案和来源的字典
        """
        logging.info(f"开始回答问题：{query}，检索模式：{retrieval_mode}")
        
        retrieval_results = None
        
        if retrieval_mode == 'entity':
            retrieval_results = {
                'entities': self.retriever.retrieve_entities(
                    query=query,
                    top_k=top_k,
                    entity_types=entity_types,
                    min_similarity=min_similarity
                ),
                'relationships': []
            }
        elif retrieval_mode == 'relationship':
            retrieval_results = {
                'entities': [],
                'relationships': self.retriever.retrieve_relationships(
                    query=query,
                    top_k=top_k,
                    relationship_types=relationship_types,
                    min_similarity=min_similarity
                )
            }
        elif retrieval_mode == 'hybrid':
            retrieval_results = self.retriever.retrieve_hybrid(
                query=query,
                top_k=top_k,
                entity_types=entity_types,
                relationship_types=relationship_types,
                min_similarity=min_similarity
            )
        elif retrieval_mode == 'contextual':
            entities = self.retriever.retrieve_contextual(
                query=query,
                context_window=200,
                top_k=top_k
            )
            retrieval_results = {
                'entities': entities,
                'relationships': []
            }
        
        if use_conversation:
            prompt = self._build_conversational_prompt(query)
        else:
            prompt = self._build_context_prompt(query, retrieval_results)
        
        try:
            response = self.llm.invoke(prompt)
            answer = response.content
            
            sources = []
            if retrieval_results and retrieval_results.get('entities'):
                for entity in retrieval_results['entities'][:3]:
                    sources.append({
                        'type': 'entity',
                        'name': entity.get('name', ''),
                        'similarity': entity.get('similarity', 0)
                    })
            if retrieval_results and retrieval_results.get('relationships'):
                for rel in retrieval_results['relationships'][:3]:
                    sources.append({
                        'type': 'relationship',
                        'source': rel.get('source', ''),
                        'target': rel.get('target', ''),
                        'similarity': rel.get('similarity', 0)
                    })
            
            result = {
                'query': query,
                'answer': answer,
                'sources': sources,
                'retrieval_mode': retrieval_mode,
                'retrieval_count': len(sources)
            }
            
            if use_conversation:
                self.conversation_history.append({
                    'user': query,
                    'assistant': answer
                })
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
            
            logging.info(f"回答完成，答案长度：{len(answer)}，检索到 {len(sources)} 个来源")
            return result
            
        except Exception as e:
            logging.error(f"回答失败: {e}")
            return {
                'query': query,
                'answer': f"抱歉，回答您的问题时出错了：{str(e)}",
                'sources': [],
                'error': str(e)
            }
    
    def clear_conversation(self):
        """清空对话历史"""
        self.conversation_history = []
        logging.info("对话历史已清空")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.conversation_history


def main():
    """测试问答引擎"""
    logging.basicConfig(level=logging.INFO)
    
    try:
        from src.embedding_manager import EmbeddingManager
        from src.vector_store import VectorStore
        from src.retriever import Retriever
        
        embedding_manager = EmbeddingManager(model_name='all-MiniLM-L6-v2')
        vector_store = VectorStore(persist_directory='./test_chroma_db')
        retriever = Retriever(vector_store, embedding_manager)
        
        qa_engine = QAEngine(retriever)
        
        print("测试问答引擎...")
        
        questions = [
            "Who is Alex Mercer?",
            "What organization does Alex Mercer work for?",
            "What is the Paranormal Military Squad?",
            "Describe the briefing room"
        ]
        
        for question in questions:
            print(f"\n{'='*60}")
            print(f"问题：{question}")
            result = qa_engine.answer(question, retrieval_mode='hybrid', top_k=3)
            print(f"答案：{result['answer']}")
            print(f"来源数量：{result['retrieval_count']}")
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
