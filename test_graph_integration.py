#!/usr/bin/env python
"""
测试图数据库检索集成
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from config import Config
from src.neo4j_manager import Neo4jManager
from src.embedding_manager import EmbeddingManager
from src.vector_store import VectorStore
from src.retriever import Retriever
from src.qa_engine import QAEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_neo4j_connection():
    """测试Neo4j连接"""
    try:
        config = Config.from_env()
        neo4j_manager = Neo4jManager(
            uri=config.neo4j.uri,
            username=config.neo4j.username,
            password=config.neo4j.password
        )
        neo4j_manager.connect()
        logger.info("Neo4j连接成功")
        
        # 测试查询
        with neo4j_manager.driver.session() as session:
            result = session.run("MATCH (e:Entity) RETURN count(e) as count")
            count = result.single()["count"]
            logger.info(f"图数据库中有 {count} 个实体")
        
        neo4j_manager.close()
        return True
    except Exception as e:
        logger.error(f"Neo4j连接失败: {e}")
        return False

def test_qa_engine_with_neo4j():
    """测试带有图检索的问答引擎"""
    try:
        config = Config.from_env()
        
        # 初始化组件
        embedding_manager = EmbeddingManager(
            model_name=config.embedding.model_name,
            cache_embeddings=True
        )
        
        # 向量数据库路径
        vector_db_path = getattr(config, 'vector_db', None)
        if vector_db_path and hasattr(vector_db_path, 'path'):
            persist_dir = vector_db_path.path
        else:
            persist_dir = "data/vector_db"
        
        vector_store = VectorStore(persist_directory=persist_dir)
        retriever = Retriever(vector_store, embedding_manager)
        
        # 初始化图数据库管理器
        neo4j_manager = None
        try:
            neo4j_manager = Neo4jManager(
                uri=config.neo4j.uri,
                username=config.neo4j.username,
                password=config.neo4j.password
            )
            neo4j_manager.connect()
            logger.info("图数据库连接成功")
        except Exception as e:
            logger.warning(f"图数据库连接失败: {e}")
            neo4j_manager = None
        
        # 初始化问答引擎
        qa_engine = QAEngine(
            retriever=retriever,
            llm_base_url=config.ollama.base_url,
            llm_model=config.ollama.model,
            llm_temperature=config.ollama.temperature,
            llm_num_ctx=config.ollama.num_ctx,
            deep_thought_mode=config.ollama.deep_thought_mode,
            neo4j_manager=neo4j_manager
        )
        
        logger.info("问答引擎初始化成功")
        
        # 测试患者ID查询
        test_queries = [
            "患者MK20231026018的病例",
            "病历号MK20231026018",
            "林悦的诊断是什么",
            "黄染牙的患者有哪些",
        ]
        
        for query in test_queries:
            logger.info(f"\n测试查询: '{query}'")
            try:
                result = qa_engine.answer(
                    query=query,
                    retrieval_mode="hybrid",
                    top_k=3,
                    use_conversation=False
                )
                
                logger.info(f"答案: {result.get('answer', '无答案')}")
                if result.get('sources'):
                    logger.info(f"来源数: {len(result['sources'])}")
                    for source in result['sources']:
                        source_type = source.get('source_type', 'unknown')
                        if source['type'] == 'entity':
                            logger.info(f"  - 实体: {source.get('name')} ({source.get('entity_type')}) [来源: {source_type}]")
                        else:
                            logger.info(f"  - 关系: {source.get('source')} -> {source.get('target')} ({source.get('rel_type')}) [来源: {source_type}]")
                else:
                    logger.info("无来源信息")
                    
            except Exception as e:
                logger.error(f"查询失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("开始测试图数据库集成...")
    
    # 测试Neo4j连接
    if not test_neo4j_connection():
        logger.warning("Neo4j连接失败，继续测试问答引擎（无图检索）")
    
    # 测试问答引擎
    success = test_qa_engine_with_neo4j()
    
    if success:
        logger.info("测试成功完成")
    else:
        logger.error("测试失败")
        sys.exit(1)