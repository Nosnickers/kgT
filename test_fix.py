#!/usr/bin/env python3
"""
测试Neo4j Cypher查询语法修复
"""

from src.neo4j_manager import Neo4jManager, Entity, Relationship
import os
from dotenv import load_dotenv

def test_neo4j_fix():
    # 加载环境变量
    load_dotenv()
    
    # 创建Neo4j管理器实例
    manager = Neo4jManager(
        uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        username=os.getenv('NEO4J_USERNAME', 'neo4j'),
        password=os.getenv('NEO4J_PASSWORD', '')
    )
    
    # 测试连接
    try:
        manager.connect()
        print('✅ Neo4j连接成功')
        
        # 测试单个实体创建
        test_entity = Entity(
            name='测试实体', 
            type='Organization', 
            properties={'description': '测试描述', 'chunk_id': [1]}
        )
        success = manager.create_entity(test_entity)
        print(f'✅ 实体创建测试: {"成功" if success else "失败"}')
        
        # 测试单个关系创建
        test_rel = Relationship(
            source='测试实体', 
            target='另一个实体', 
            type='RELATED_TO', 
            properties={'description': '测试关系', 'chunk_id': [1]}
        )
        success = manager.create_relationship(test_rel)
        print(f'✅ 关系创建测试: {"成功" if success else "失败"}')
        
        # 测试批量实体创建（修复的重点）
        batch_entities = [
            Entity(name='批量实体1', type='Product', properties={'chunk_id': [1, 2]}),
            Entity(name='批量实体2', type='Material', properties={'description': '批量测试', 'chunk_id': [1]})
        ]
        
        try:
            created_count = manager.batch_create_entities(batch_entities)
            print(f'✅ 批量实体创建测试: 成功创建 {created_count} 个实体')
        except Exception as e:
            print(f'❌ 批量实体创建失败: {e}')
            return False
        
        # 测试批量关系创建（修复的重点）
        batch_relationships = [
            Relationship(
                source='批量实体1', 
                target='批量实体2', 
                type='USES', 
                properties={'chunk_id': [1]}
            )
        ]
        
        try:
            created_count = manager.batch_create_relationships(batch_relationships)
            print(f'✅ 批量关系创建测试: 成功创建 {created_count} 个关系')
        except Exception as e:
            print(f'❌ 批量关系创建失败: {e}')
            return False
        
        # 获取统计信息
        stats = manager.get_statistics()
        print(f'✅ 数据库统计: {stats}')
        
        manager.close()
        print('✅ Neo4j连接已关闭')
        return True
        
    except Exception as e:
        print(f'❌ 测试失败: {e}')
        return False

if __name__ == "__main__":
    print("开始测试Neo4j Cypher查询语法修复...")
    success = test_neo4j_fix()
    if success:
        print("\n🎉 所有测试通过！Cypher查询语法修复成功！")
    else:
        print("\n❌ 测试失败，请检查Neo4j连接和配置")