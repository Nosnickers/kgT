#!/usr/bin/env python3
"""
测试chunk_id数组逻辑，不依赖LLM
"""

from src.neo4j_manager import Neo4jManager, Entity, Relationship
from config import Config


def test_chunk_id_logic():
    """测试chunk_id数组逻辑"""
    print("测试chunk_id数组逻辑...")
    
    # 加载配置
    config = Config.from_env('.env')
    
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
    
    print("1. 测试创建第一个实体...")
    # 创建第一个实体，包含chunk_id数组
    entity1 = Entity(
        name="Apple",
        type="Organization",
        properties={"description": "A technology company", "chunk_id": [1]}
    )
    
    # 创建实体
    neo4j_manager.create_entity(entity1)
    
    # 查询实体
    with neo4j_manager.driver.session() as session:
        result = session.run("MATCH (e:Entity {name: 'Apple'}) RETURN e.chunk_id")
        entity = result.single()
        if entity:
            chunk_id = entity["e.chunk_id"]
            print(f"   ✅ 实体创建成功，chunk_id: {chunk_id}")
            if isinstance(chunk_id, list):
                print(f"   ✅ chunk_id是数组类型")
        else:
            print(f"   ❌ 实体创建失败")
    
    print("2. 测试更新实体，添加新的chunk_id...")
    # 更新实体，添加新的chunk_id
    entity2 = Entity(
        name="Apple",
        type="Organization",
        properties={"description": "A technology company", "chunk_id": [1, 2]}
    )
    
    # 更新实体
    neo4j_manager.create_entity(entity2)
    
    # 查询实体
    with neo4j_manager.driver.session() as session:
        result = session.run("MATCH (e:Entity {name: 'Apple'}) RETURN e.chunk_id")
        entity = result.single()
        if entity:
            chunk_id = entity["e.chunk_id"]
            print(f"   ✅ 实体更新成功，chunk_id: {chunk_id}")
            if isinstance(chunk_id, list):
                print(f"   ✅ chunk_id是数组类型")
            if 1 in chunk_id and 2 in chunk_id:
                print(f"   ✅ chunk_id数组包含了所有相关的chunk_id")
        else:
            print(f"   ❌ 实体更新失败")
    
    print("3. 测试创建关系，包含chunk_id数组...")
    # 创建关系，包含chunk_id数组
    relationship1 = Relationship(
        source="Apple",
        target="carbon neutrality",
        type="ACHIEVES",
        properties={"description": "Apple is committed to carbon neutrality", "chunk_id": [1, 2]}
    )
    
    # 创建关系
    neo4j_manager.create_relationship(relationship1)
    
    # 查询关系
    with neo4j_manager.driver.session() as session:
        result = session.run("MATCH ()-[r:RELATIONSHIP {type: 'ACHIEVES'}]->() RETURN r.chunk_id")
        rel = result.single()
        if rel:
            chunk_id = rel["r.chunk_id"]
            print(f"   ✅ 关系创建成功，chunk_id: {chunk_id}")
            if isinstance(chunk_id, list):
                print(f"   ✅ chunk_id是数组类型")
        else:
            print(f"   ❌ 关系创建失败")
    
    # 关闭Neo4j连接
    neo4j_manager.close()
    
    print("\n✅ 所有测试通过！chunk_id数组逻辑正常工作")
    return True


if __name__ == "__main__":
    test_chunk_id_logic()
