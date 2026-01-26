#!/usr/bin/env python3
"""
测试实体和关系数据的必填字段校验功能
"""

import sys
import os
import json
import logging

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from entity_extractor import EntityExtractor, ExtractionResult

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_validation_logic():
    """测试校验逻辑"""
    logging.info("=== 测试校验逻辑 ===")
    
    # 创建实体提取器实例
    extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="mistral:7b-instruct-v0.3-q4_0",
        temperature=0.1,
        num_ctx=4096
    )
    
    # 测试用例1: 有效的实体数据
    valid_entity = {
        "name": "Alex Mercer",
        "type": "Character",
        "description": "Rogue agent with a mysterious past"
    }
    
    # 测试用例2: 无效的实体数据（缺少name）
    invalid_entity_no_name = {
        "type": "Character",
        "description": "Rogue agent"
    }
    
    # 测试用例3: 无效的实体数据（name为占位符）
    invalid_entity_placeholder_name = {
        "name": "entity_name",
        "type": "Character",
        "description": "Rogue agent"
    }
    
    # 测试用例4: 有效的关係数据
    valid_relationship = {
        "source": "Alex Mercer",
        "target": "Paranormal Military Squad",
        "type": "WORKS_FOR",
        "description": "Alex works for the PMS"
    }
    
    # 测试用例5: 无效的关係数据（source和target相同）
    invalid_relationship_same_entities = {
        "source": "Alex Mercer",
        "target": "Alex Mercer",
        "type": "WORKS_FOR",
        "description": "Alex works for himself"
    }
    
    # 执行校验测试
    logging.info("测试有效实体数据:")
    result1 = extractor._validate_entity_data(valid_entity)
    logging.info(f"  结果: {result1} (期望: True)")
    
    logging.info("测试缺少name的实体数据:")
    result2 = extractor._validate_entity_data(invalid_entity_no_name)
    logging.info(f"  结果: {result2} (期望: False)")
    
    logging.info("测试name为占位符的实体数据:")
    result3 = extractor._validate_entity_data(invalid_entity_placeholder_name)
    logging.info(f"  结果: {result3} (期望: False)")
    
    logging.info("测试有效关係数据:")
    result4 = extractor._validate_relationship_data(valid_relationship)
    logging.info(f"  结果: {result4} (期望: True)")
    
    logging.info("测试source和target相同的关係数据:")
    result5 = extractor._validate_relationship_data(invalid_relationship_same_entities)
    logging.info(f"  结果: {result5} (期望: False)")
    
    # 验证测试结果
    assert result1 == True, "有效实体数据校验失败"
    assert result2 == False, "缺少name的实体数据校验失败"
    assert result3 == False, "name为占位符的实体数据校验失败"
    assert result4 == True, "有效关係数据校验失败"
    assert result5 == False, "source和target相同的关係数据校验失败"
    
    logging.info("✓ 所有校验逻辑测试通过")

def test_retry_mechanism():
    """测试重试机制"""
    logging.info("=== 测试重试机制 ===")
    
    # 创建实体提取器实例
    extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="mistral:7b-instruct-v0.3-q4_0",
        temperature=0.1,
        num_ctx=4096
    )
    
    # 测试文本
    test_text = """Alex Mercer works for the Paranormal Military Squad. He is located in New York City."""
    
    # 测试提取功能（包含重试机制）
    logging.info("测试实体提取功能（包含重试机制）...")
    result = extractor.extract(test_text, max_retries=2)
    
    # 检查结果
    logging.info(f"提取到 {len(result.entities)} 个实体")
    logging.info(f"提取到 {len(result.relationships)} 个关系")
    
    # 验证实体数据
    for i, entity in enumerate(result.entities):
        logging.info(f"实体 {i+1}: {entity.name} ({entity.type})")
        # 验证必填字段
        assert entity.name and entity.name.strip(), f"实体 {i+1} 缺少name字段"
        assert entity.type and entity.type.strip(), f"实体 {i+1} 缺少type字段"
        assert entity.name.lower() not in ['entity_name', 'actual_entity_name_from_text', 'name'], f"实体 {i+1} 的name为占位符"
        assert entity.type.lower() not in ['entity_type', 'appropriate_entity_type', 'type'], f"实体 {i+1} 的type为占位符"
    
    # 验证关系数据
    for i, rel in enumerate(result.relationships):
        logging.info(f"关系 {i+1}: {rel.source} --[{rel.type}]--> {rel.target}")
        # 验证必填字段
        assert rel.source and rel.source.strip(), f"关系 {i+1} 缺少source字段"
        assert rel.target and rel.target.strip(), f"关系 {i+1} 缺少target字段"
        assert rel.type and rel.type.strip(), f"关系 {i+1} 缺少type字段"
        assert rel.source.lower() not in ['source', 'actual_source_entity_name'], f"关系 {i+1} 的source为占位符"
        assert rel.target.lower() not in ['target', 'actual_target_entity_name'], f"关系 {i+1} 的target为占位符"
        assert rel.type.lower() not in ['type', 'appropriate_relationship_type'], f"关系 {i+1} 的type为占位符"
        assert rel.source != rel.target, f"关系 {i+1} 的source和target相同"
    
    logging.info("✓ 重试机制测试通过")

def test_invalid_data_handling():
    """测试无效数据处理"""
    logging.info("=== 测试无效数据处理 ===")
    
    # 创建实体提取器实例
    extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="mistral:7b-instruct-v0.3-q4_0",
        temperature=0.1,
        num_ctx=4096
    )
    
    # 模拟包含无效数据的JSON响应
    invalid_json_response = {
        "entities": [
            {
                "name": "",  # 空的name
                "type": "Character",
                "description": "Rogue agent"
            },
            {
                "name": "entity_name",  # 占位符name
                "type": "Character",
                "description": "Rogue agent"
            },
            {
                "name": "Alex Mercer",
                "type": "",  # 空的type
                "description": "Rogue agent"
            }
        ],
        "relationships": [
            {
                "source": "Alex Mercer",
                "target": "Alex Mercer",  # source和target相同
                "type": "WORKS_FOR",
                "description": "Alex works for himself"
            },
            {
                "source": "source",  # 占位符source
                "target": "Paranormal Military Squad",
                "type": "WORKS_FOR",
                "description": "Works for PMS"
            }
        ]
    }
    
    # 测试校验功能
    valid_entities = []
    valid_relationships = []
    
    for entity in invalid_json_response["entities"]:
        if extractor._validate_entity_data(entity):
            valid_entities.append(entity)
        else:
            logging.warning(f"跳过无效实体: {entity}")
    
    for rel in invalid_json_response["relationships"]:
        if extractor._validate_relationship_data(rel):
            valid_relationships.append(rel)
        else:
            logging.warning(f"跳过无效关系: {rel}")
    
    logging.info(f"原始数据: {len(invalid_json_response['entities'])} 个实体, {len(invalid_json_response['relationships'])} 个关系")
    logging.info(f"有效数据: {len(valid_entities)} 个实体, {len(valid_relationships)} 个关系")
    
    # 验证无效数据被正确过滤
    assert len(valid_entities) == 0, "无效实体数据未被正确过滤"
    assert len(valid_relationships) == 0, "无效关系数据未被正确过滤"
    
    logging.info("✓ 无效数据处理测试通过")

def main():
    """主函数"""
    setup_logging()
    
    logging.info("=== 开始测试必填字段校验功能 ===")
    
    try:
        # 测试校验逻辑
        test_validation_logic()
        
        # 测试重试机制
        test_retry_mechanism()
        
        # 测试无效数据处理
        test_invalid_data_handling()
        
        logging.info("=== 所有测试通过 ===")
        
    except Exception as e:
        logging.error(f"测试失败: {e}")
        raise

if __name__ == "__main__":
    main()