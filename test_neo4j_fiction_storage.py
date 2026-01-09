#!/usr/bin/env python3
"""
测试小说实体提取结果在Neo4j中的存储情况
验证完整的知识图谱构建流程
"""

import os
import sys
import json
import logging
import time
from typing import List, Dict, Any

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import DataLoader
from entity_extractor import EntityExtractor
from neo4j_manager import Neo4jManager
from graph_builder import GraphBuilder

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('neo4j_fiction_storage_test.log', encoding='utf-8')
        ]
    )

def test_neo4j_connection():
    """测试Neo4j连接"""
    logging.info("=== 测试Neo4j连接 ===")
    
    try:
        # 从环境变量获取Neo4j连接信息
        import os
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        username = os.getenv('NEO4J_USERNAME', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', '')
        
        neo4j_manager = Neo4jManager(uri=uri, username=username, password=password)
        
        # 测试连接
        neo4j_manager.connect()
        logging.info("✓ Neo4j连接成功")
        
        # 获取数据库统计信息
        stats = neo4j_manager.get_statistics()
        logging.info(f"数据库统计信息: {stats}")
        
        return neo4j_manager
            
    except Exception as e:
        logging.error(f"Neo4j连接测试失败: {e}")
        return None

def test_fiction_entity_extraction_and_storage():
    """测试小说实体提取和Neo4j存储"""
    logging.info("=== 开始测试小说实体提取和Neo4j存储 ===")
    
    # 1. 测试Neo4j连接
    neo4j_manager = test_neo4j_connection()
    if not neo4j_manager:
        logging.error("Neo4j连接失败，无法继续测试")
        return False
    
    # 2. 创建数据加载器
    try:
        json_file = "data/Dulce.json"
        if not os.path.exists(json_file):
            logging.error(f"JSON文件不存在: {json_file}")
            return False
            
        data_loader = DataLoader(json_file, chunk_size=800, chunk_overlap=100)
        logging.info("数据加载器创建成功")
    except Exception as e:
        logging.error(f"创建数据加载器失败: {e}")
        return False
    
    # 3. 加载数据
    try:
        chunks = data_loader.load_and_chunk()
        logging.info(f"成功加载 {len(chunks)} 个数据块")
        
        # 显示前几个数据块的信息
        for i, chunk in enumerate(chunks[:3]):
            logging.info(f"数据块 {i}: ID={chunk.chunk_id}, 标题={chunk.title}, 长度={len(chunk.content)} 字符")
            logging.info(f"内容预览: {chunk.content[:200]}...")
            
    except Exception as e:
        logging.error(f"加载数据失败: {e}")
        return False
    
    # 4. 创建实体提取器
    try:
        extractor = EntityExtractor(
            base_url="http://localhost:11434",
            model="mistral:7b-instruct-v0.3-q4_0",
            temperature=0.1,
            num_ctx=4096,
            deep_thought_mode=True
        )
        logging.info("实体提取器创建成功")
    except Exception as e:
        logging.error(f"创建实体提取器失败: {e}")
        return False
    
    # 5. 创建知识图谱构建器
    try:
        graph_builder = GraphBuilder(
            neo4j_manager=neo4j_manager,
            entity_extractor=extractor
        )
        logging.info("知识图谱构建器创建成功")
    except Exception as e:
        logging.error(f"创建知识图谱构建器失败: {e}")
        return False
    
    # 6. 测试单个数据块的提取和存储
    logging.info("=== 测试单个数据块的提取和存储 ===")
    
    if len(chunks) > 0:
        test_chunk = chunks[0]
        logging.info(f"测试数据块: ID={test_chunk.chunk_id}, 标题={test_chunk.title}")
        
        try:
            # 提取实体和关系
            extraction_result = extractor.extract(test_chunk.content)
            logging.info(f"提取到 {len(extraction_result.entities)} 个实体和 {len(extraction_result.relationships)} 个关系")
            
            # 显示提取结果
            for i, entity in enumerate(extraction_result.entities[:5]):
                logging.info(f"  实体 {i+1}: {entity.name} ({entity.type}): {entity.description}")
            
            for i, rel in enumerate(extraction_result.relationships[:5]):
                logging.info(f"  关系 {i+1}: {rel.source} --[{rel.type}]--> {rel.target}")
            
            # 存储到Neo4j
            logging.info("开始存储到Neo4j...")
            
            # 先清空数据库（测试用）
            neo4j_manager.clear_database()
            logging.info("数据库已清空")
            
            # 导入Entity和Relationship模型
            from neo4j_manager import Entity, Relationship
            
            # 存储实体
            entity_count = 0
            for entity in extraction_result.entities:
                entity_obj = Entity(
                    name=entity.name,
                    type=entity.type,
                    properties={
                        'description': entity.description,
                        'chunk_id': test_chunk.chunk_id
                    }
                )
                success = neo4j_manager.create_entity(entity_obj)
                if success:
                    entity_count += 1
            
            logging.info(f"成功存储 {entity_count} 个实体")
            
            # 存储关系
            relationship_count = 0
            for rel in extraction_result.relationships:
                rel_obj = Relationship(
                    source=rel.source,
                    target=rel.target,
                    type=rel.type,
                    properties={
                        'description': rel.description,
                        'chunk_id': test_chunk.chunk_id
                    }
                )
                success = neo4j_manager.create_relationship(rel_obj)
                if success:
                    relationship_count += 1
            
            logging.info(f"成功存储 {relationship_count} 个关系")
            
            # 验证存储结果
            logging.info("=== 验证Neo4j存储结果 ===")
            
            # 查询实体数量
            entity_query = "MATCH (e) RETURN count(e) as entity_count"
            entity_result = neo4j_manager.execute_query(entity_query)
            if entity_result:
                logging.info(f"Neo4j中实体数量: {entity_result[0]['entity_count']}")
            
            # 查询关系数量
            rel_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
            rel_result = neo4j_manager.execute_query(rel_query)
            if rel_result:
                logging.info(f"Neo4j中关系数量: {rel_result[0]['rel_count']}")
            
            # 查询具体实体
            entities_query = "MATCH (e) RETURN e.name as name, e.type as type, e.description as description LIMIT 10"
            entities_result = neo4j_manager.execute_query(entities_query)
            
            if entities_result:
                logging.info("Neo4j中存储的实体:")
                for i, entity in enumerate(entities_result):
                    logging.info(f"  {i+1}. {entity['name']} ({entity['type']}): {entity['description']}")
            
            # 查询具体关系
            relationships_query = """
            MATCH (s)-[r]->(t) 
            RETURN s.name as source, r.type as type, t.name as target, r.description as description 
            LIMIT 10
            """
            relationships_result = neo4j_manager.execute_query(relationships_query)
            
            if relationships_result:
                logging.info("Neo4j中存储的关系:")
                for i, rel in enumerate(relationships_result):
                    logging.info(f"  {i+1}. {rel['source']} --[{rel['type']}]--> {rel['target']}: {rel['description']}")
            
            return True
            
        except Exception as e:
            logging.error(f"单个数据块提取和存储测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        logging.error("没有可用的数据块进行测试")
        return False

def test_full_graph_building():
    """测试完整的知识图谱构建"""
    logging.info("=== 测试完整的知识图谱构建 ===")
    
    # 1. 测试Neo4j连接
    neo4j_manager = test_neo4j_connection()
    if not neo4j_manager:
        logging.error("Neo4j连接失败，无法继续测试")
        return False
    
    # 2. 创建完整的构建器
    try:
        json_file = "data/Dulce.json"
        if not os.path.exists(json_file):
            logging.error(f"JSON文件不存在: {json_file}")
            return False
            
        data_loader = DataLoader(json_file, chunk_size=800, chunk_overlap=100)
        extractor = EntityExtractor(
            base_url="http://localhost:11434",
            model="mistral:7b-instruct-v0.3-q4_0",
            temperature=0.1
        )
        graph_builder = GraphBuilder(neo4j_manager, extractor)
        
        logging.info("完整构建器创建成功")
    except Exception as e:
        logging.error(f"创建完整构建器失败: {e}")
        return False
    
    # 3. 加载数据
    try:
        chunks = data_loader.load_and_chunk()
        logging.info(f"成功加载 {len(chunks)} 个数据块")
    except Exception as e:
        logging.error(f"加载数据失败: {e}")
        return False
    
    # 4. 构建知识图谱（只处理前几个数据块以节省时间）
    try:
        logging.info("开始构建知识图谱...")
        
        # 只处理前3个数据块进行测试
        test_chunks = chunks[:3]
        
        result_stats = graph_builder.build_graph(
            chunks=test_chunks,
            show_progress=True,
            clear_database=True,
            batch_process_size=2,
            csv_output_prefix="fiction_test"
        )
        
        logging.info("=== 知识图谱构建结果统计 ===")
        logging.info(f"处理的数据块数量: {result_stats['chunks_processed']}")
        logging.info(f"成功提取的数据块: {result_stats['chunks_successful']}")
        logging.info(f"提取失败的數據块: {result_stats['chunks_failed']}")
        logging.info(f"总实体数量: {result_stats['total_entities']}")
        logging.info(f"总关系数量: {result_stats['total_relationships']}")
        
        # 验证最终结果
        entity_query = "MATCH (e) RETURN count(e) as entity_count"
        entity_result = neo4j_manager.execute_query(entity_query)
        
        rel_query = "MATCH ()-[r]->() RETURN count(r) as rel_count"
        rel_result = neo4j_manager.execute_query(rel_query)
        
        if entity_result and rel_result:
            logging.info(f"最终验证 - 实体数量: {entity_result[0]['entity_count']}")
            logging.info(f"最终验证 - 关系数量: {rel_result[0]['rel_count']}")
            
            # 检查是否有重复实体
            duplicate_query = """
            MATCH (e)
            WITH e.name as name, count(*) as count
            WHERE count > 1
            RETURN name, count
            """
            duplicate_result = neo4j_manager.execute_query(duplicate_query)
            
            if duplicate_result:
                logging.warning(f"发现重复实体: {len(duplicate_result)} 个")
                for dup in duplicate_result:
                    logging.warning(f"  实体 '{dup['name']}' 出现 {dup['count']} 次")
            else:
                logging.info("✓ 没有发现重复实体")
        
        return True
        
    except Exception as e:
        logging.error(f"完整知识图谱构建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    setup_logging()
    
    logging.info("=== 小说实体提取和Neo4j存储测试开始 ===")
    
    # 测试单个数据块的提取和存储
    success1 = test_fiction_entity_extraction_and_storage()
    
    if success1:
        logging.info("✓ 单个数据块测试成功")
    else:
        logging.error("✗ 单个数据块测试失败")
    
    # 测试完整的知识图谱构建
    success2 = test_full_graph_building()
    
    if success2:
        logging.info("✓ 完整知识图谱构建测试成功")
    else:
        logging.error("✗ 完整知识图谱构建测试失败")
    
    if success1 and success2:
        logging.info("=== 所有测试通过 ===")
    else:
        logging.error("=== 部分测试失败 ===")

if __name__ == "__main__":
    main()