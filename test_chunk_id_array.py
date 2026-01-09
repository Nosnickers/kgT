#!/usr/bin/env python3
"""
测试实体和关系的chunk_id数组功能
"""

import os
import sys
from src.data_loader import DataLoader, DataChunk
from src.neo4j_manager import Neo4jManager, Entity, Relationship
from src.entity_extractor import EntityExtractor
from src.graph_builder import GraphBuilder
from config import Config


def test_chunk_id_array():
    """测试实体和关系的chunk_id数组功能"""
    print("测试实体和关系的chunk_id数组功能...")
    
    # 加载配置
    config = Config.from_env('.env')
    
    # 创建测试数据块
    test_chunks = [
        DataChunk(
            content="Apple is committed to carbon neutrality by 2030.",
            metadata={"title": "Test", "chunk_id": 1, "word_count": 8}
        ),
        DataChunk(
            content="Apple is committed to reducing its carbon footprint by 75% by 2030.",
            metadata={"title": "Test", "chunk_id": 2, "word_count": 12}
        ),
        DataChunk(
            content="Apple uses renewable energy for all its operations.",
            metadata={"title": "Test", "chunk_id": 3, "word_count": 8}
        )
    ]
    
    print(f"创建了 {len(test_chunks)} 个测试数据块")
    
    # 创建Neo4j管理器
    neo4j_manager = Neo4jManager(
        uri=config.neo4j.uri,
        username=config.neo4j.username,
        password=config.neo4j.password
    )
    
    # 连接到Neo4j
    neo4j_manager.connect()
    
    # 清空数据库
    neo4j_manager.clear_database()
    neo4j_manager.create_constraints()
    
    # 创建数据加载器
    data_loader = DataLoader(
        file_path=config.data.file_path,
        chunk_size=config.data.chunk_size,
        chunk_overlap=config.data.chunk_overlap
    )
    
    # 创建实体提取器
    entity_extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    # 创建图构建器
    graph_builder = GraphBuilder(
        data_loader=data_loader,
        neo4j_manager=neo4j_manager,
        entity_extractor=entity_extractor,
        max_retries=config.processing.max_retries,
        retry_delay=config.processing.retry_delay
    )
    
    # 构建图
    print("开始构建图...")
    stats = graph_builder.build_graph(
        chunks=test_chunks,
        show_progress=False,
        clear_database=False,
        batch_process_size=2
    )
    
    print(f"构建完成：处理了 {stats['chunks_processed']} 个数据块，创建了 {stats['entities_created']} 个实体和 {stats['relationships_created']} 个关系")
    
    # 验证实体的chunk_id数组
    print("\n验证实体的chunk_id数组：")
    with neo4j_manager.driver.session() as session:
        # 查询所有实体
        result = session.run("MATCH (e:Entity) RETURN e.name, e.type, e.chunk_id")
        entities = list(result)
        
        for record in entities:
            name = record["e.name"]
            type_ = record["e.type"]
            chunk_id = record["e.chunk_id"]
            
            print(f"实体: {name} ({type_}), chunk_id: {chunk_id}")
            
            # 验证chunk_id是数组类型
            if isinstance(chunk_id, list):
                print(f"  ✅ chunk_id是数组类型")
            else:
                print(f"  ❌ chunk_id不是数组类型")
                return False
    
    # 验证关系的chunk_id数组
    print("\n验证关系的chunk_id数组：")
    with neo4j_manager.driver.session() as session:
        # 查询所有关系
        result = session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN r")
        relationships = list(result)
        
        for record in relationships:
            rel = record["r"]
            type_ = rel["type"]
            chunk_id = rel.get("chunk_id", [])
            
            print(f"关系: {type_}, chunk_id: {chunk_id}")
            
            # 验证chunk_id是数组类型
            if isinstance(chunk_id, list):
                print(f"  ✅ chunk_id是数组类型")
            else:
                print(f"  ❌ chunk_id不是数组类型")
                return False
    
    # 关闭Neo4j连接
    neo4j_manager.close()
    
    print("\n✅ 所有测试通过！实体和关系的chunk_id数组功能正常工作")
    return True


if __name__ == "__main__":
    test_chunk_id_array()
