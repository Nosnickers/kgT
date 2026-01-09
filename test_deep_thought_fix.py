#!/usr/bin/env python3
"""
测试深度思考模式下的实体提取功能是否正常工作
"""

import logging
from src.entity_extractor import EntityExtractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_deep_thought_extraction():
    """测试深度思考模式下的实体提取"""
    print("\n测试深度思考模式下的实体提取功能...")
    
    # 创建实体提取器实例，启用深度思考模式
    entity_extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="deepseek-r1:8b",
        temperature=0.1,
        num_ctx=4096,
        deep_thought_mode=True
    )
    
    # 测试文本 - 来自Apple环境报告的一个片段
    test_text = "Apple is committed to carbon neutrality by 2030. This initiative includes reducing carbon emissions across its entire supply chain and using 100% renewable energy for all operations. The company has already made significant progress, reducing its carbon footprint by 35% since 2015."
    
    print(f"测试文本: {test_text}")
    print("\n正在使用深度思考模式提取实体和关系...")
    
    # 执行提取
    result = entity_extractor.extract(test_text)
    
    print("\n提取结果:")
    print(f"实体数量: {len(result.entities)}")
    print(f"关系数量: {len(result.relationships)}")
    
    print("\n实体列表:")
    for entity in result.entities:
        print(f"- {entity.name} ({entity.type}): {entity.description}")
    
    print("\n关系列表:")
    for rel in result.relationships:
        print(f"- {rel.source} -> {rel.target} ({rel.type}): {rel.description}")
    
    # 验证提取结果
    if len(result.entities) > 0 and len(result.relationships) > 0:
        print("\n✅ 测试通过！深度思考模式下实体提取功能正常工作。")
        return True
    else:
        print("\n❌ 测试失败！未提取到实体或关系。")
        return False

if __name__ == "__main__":
    test_deep_thought_extraction()
