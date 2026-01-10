#!/usr/bin/env python3
"""
测试小说文本实体提取效果
测试新的提示模板对Dulce.json的实体提取效果
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from entity_extractor import EntityExtractor, ExtractionResult
from data_loader import DataLoader

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('fiction_extraction_test.log', encoding='utf-8')
        ]
    )

def load_dulce_json_sample() -> str:
    """加载Dulce.json的样本文本"""
    json_file = "data/Dulce.json"
    
    if not os.path.exists(json_file):
        logging.error(f"JSON文件不存在: {json_file}")
        return ""
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取前几个章节的文本作为样本
        sample_texts = []
        for i, item in enumerate(data[:3]):  # 取前3个章节
            text_content = item.get('text', '')
            if text_content:
                sample_texts.append(f"=== 章节 {i+1} ===\n{text_content}")
        
        return "\n\n".join(sample_texts)
        
    except Exception as e:
        logging.error(f"加载JSON文件失败: {e}")
        return ""

def test_entity_extraction():
    """测试实体提取功能"""
    logging.info("=== 开始测试小说文本实体提取 ===")
    
    # 加载样本文本
    sample_text = load_dulce_json_sample()
    if not sample_text:
        logging.error("无法加载样本文本")
        return
    
    logging.info(f"样本文本长度: {len(sample_text)} 字符")
    logging.info("样本文本预览:")
    logging.info(sample_text[:500] + "...")
    
    # 创建实体提取器
    try:
        extractor = EntityExtractor(
            base_url="http://localhost:11434",
            model="mistral:7b-instruct-v0.3-q4_0",
            temperature=0.1,
            num_ctx=4096,
            deep_thought_mode=True  # 启用深度思考模式
        )
        logging.info("实体提取器创建成功")
    except Exception as e:
        logging.error(f"创建实体提取器失败: {e}")
        return
    
    # 测试提取
    try:
        logging.info("开始实体提取...")
        result = extractor.extract(sample_text)
        
        # 输出提取结果
        logging.info("=== 实体提取结果 ===")
        logging.info(f"提取到 {len(result.entities)} 个实体:")
        
        for i, entity in enumerate(result.entities):
            logging.info(f"  {i+1}. {entity.name} ({entity.type}): {entity.description}")
        
        logging.info(f"提取到 {len(result.relationships)} 个关系:")
        
        for i, rel in enumerate(result.relationships):
            logging.info(f"  {i+1}. {rel.source} --[{rel.type}]--> {rel.target}: {rel.description}")
        
        # 按类型统计实体
        entity_types = {}
        for entity in result.entities:
            entity_types[entity.type] = entity_types.get(entity.type, 0) + 1
        
        logging.info("=== 实体类型统计 ===")
        for entity_type, count in entity_types.items():
            logging.info(f"  {entity_type}: {count}")
        
        # 按类型统计关系
        rel_types = {}
        for rel in result.relationships:
            rel_types[rel.type] = rel_types.get(rel.type, 0) + 1
        
        logging.info("=== 关系类型统计 ===")
        for rel_type, count in rel_types.items():
            logging.info(f"  {rel_type}: {count}")
        
        # 保存详细结果到文件
        with open('fiction_extraction_detailed.json', 'w', encoding='utf-8') as f:
            json.dump({
                'entities': [entity.dict() for entity in result.entities],
                'relationships': [rel.dict() for rel in result.relationships]
            }, f, ensure_ascii=False, indent=2)
        
        logging.info("详细结果已保存到 fiction_extraction_detailed.json")
        
    except Exception as e:
        logging.error(f"实体提取失败: {e}")
        import traceback
        traceback.print_exc()

def test_prompt_template():
    """测试提示模板内容"""
    logging.info("=== 测试提示模板 ===")
    
    extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="mistral:7b-instruct-v0.3-q4_0",
        temperature=0.1
    )
    
    prompt = extractor.create_extraction_prompt()
    
    # 检查提示模板的关键内容
    prompt_text = str(prompt)
    
    # 检查是否包含小说相关的实体类型
    fiction_entity_types = ["Character", "Organization", "Location", "Technology", "Concept", "Object", "Event"]
    fiction_rel_types = ["WORKS_FOR", "LOCATED_AT", "USES", "INTERACTS_WITH", "PART_OF", "INVOLVED_IN", "RELATED_TO", "LEADS", "OWNS", "PARTICIPATES_IN"]
    
    logging.info("=== 提示模板检查 ===")
    
    for entity_type in fiction_entity_types:
        if entity_type in prompt_text:
            logging.info(f"✓ 包含小说实体类型: {entity_type}")
        else:
            logging.warning(f"✗ 缺少小说实体类型: {entity_type}")
    
    for rel_type in fiction_rel_types:
        if rel_type in prompt_text:
            logging.info(f"✓ 包含小说关系类型: {rel_type}")
        else:
            logging.warning(f"✗ 缺少小说关系类型: {rel_type}")
    
    # 检查关键规则
    key_rules = [
        "fictional stories",
        "characters",
        "locations",
        "organizations",
        "NEVER invent or add information",
        "actual_entity_name_from_text"
    ]
    
    for rule in key_rules:
        if rule in prompt_text:
            logging.info(f"✓ 包含关键规则: {rule}")
        else:
            logging.warning(f"✗ 缺少关键规则: {rule}")

def main():
    """主函数"""
    setup_logging()
    
    logging.info("=== 小说文本实体提取测试开始 ===")
    
    # 测试提示模板
    test_prompt_template()
    
    # 测试实体提取
    test_entity_extraction()
    
    logging.info("=== 测试完成 ===")

if __name__ == "__main__":
    main()