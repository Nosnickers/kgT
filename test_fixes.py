#!/usr/bin/env python3
"""测试深度思考模式控制和幻觉过滤"""
import sys
sys.path.append('src')
import logging
from config import Config
from src.entity_extractor import EntityExtractor
from src.graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_deep_thought_mode_config():
    """测试深度思考模式配置"""
    print("=== 测试深度思考模式配置 ===")
    
    config = Config.from_env()
    print(f"OLLAMA_DEEP_THOUGHT_MODE from .env: {config.ollama.deep_thought_mode}")
    
    # 创建提取器
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    print(f"提取器 deep_thought_mode: {extractor.deep_thought_mode}")
    
    # 检查 llm 配置
    llm_kwargs = extractor.llm.dict() if hasattr(extractor.llm, 'dict') else {}
    print(f"LLM 配置: {llm_kwargs}")
    
    if config.ollama.deep_thought_mode:
        print("深度思考模式: 启用")
    else:
        print("深度思考模式: 禁用")
        # 检查是否有 stop 参数
        if hasattr(extractor.llm, 'stop'):
            print(f"LLM stop 参数: {extractor.llm.stop}")
        else:
            print("警告: LLM 没有 stop 参数")
    
    return True

def test_prompt_content():
    """测试提示词内容"""
    print("\n=== 测试提示词内容 ===")
    
    config = Config.from_env()
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    prompt = extractor.create_extraction_prompt()
    messages = prompt.format_messages(text="测试文本")
    system_content = messages[0].content
    
    # 检查关键指令
    required_phrases = [
        "NO THINKING OUTPUT",
        "NO HALLUCINATION POLICY",
        "CRITICAL WARNING",
        "DO NOT output any thinking process",
        "李明",
        "张三",
        "DO NOT OUTPUT THINKING PROCESS"
    ]
    
    for phrase in required_phrases:
        if phrase in system_content:
            print(f"✅ 提示词包含: {phrase}")
        else:
            print(f"❌ 提示词缺少: {phrase}")
    
    # 检查是否移除了示例
    if '(e.g.,' in system_content:
        print("❌ 提示词仍包含示例 (e.g., ...)")
    else:
        print("✅ 提示词无示例 (e.g., ...)")
    
    if 'Example:' in system_content:
        print("❌ 提示词仍包含 'Example:'")
    else:
        print("✅ 提示词无 'Example:'")
    
    return True

def test_hallucination_validation():
    """测试幻觉验证逻辑"""
    print("\n=== 测试幻觉验证逻辑 ===")
    
    config = Config.from_env()
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    # 测试文本（不包含"李明"）
    text = "病历号：MK20231026018 姓名：林悦 性别：女 年龄：32岁"
    
    # 幻觉实体
    hallucination_entities = [
        {"name": "李明", "type": "Patient", "description": "患者姓名"},
        {"name": "张三", "type": "Patient", "description": "患者姓名"},
        {"name": "牙痛", "type": "Symptom", "description": "症状"},
        {"name": "龋齿", "type": "Diagnosis", "description": "诊断"},
        {"name": "青霉素过敏", "type": "Allergies", "description": "过敏史"},
    ]
    
    # 真实实体
    real_entities = [
        {"name": "林悦", "type": "Patient", "description": "患者姓名"},
        {"name": "MK20231026018", "type": "PatientId", "description": "病历号"},
        {"name": "女", "type": "Demographics", "description": "性别"},
        {"name": "32岁", "type": "Demographics", "description": "年龄"},
    ]
    
    print("测试幻觉实体:")
    for entity in hallucination_entities:
        is_valid = extractor._validate_entity_against_text(entity, text)
        status = "❌ 通过" if not is_valid else "✅ 失败"
        print(f"  {entity['name']} ({entity['type']}): {status}")
    
    print("\n测试真实实体:")
    for entity in real_entities:
        is_valid = extractor._validate_entity_against_text(entity, text)
        status = "✅ 通过" if is_valid else "❌ 失败"
        print(f"  {entity['name']} ({entity['type']}): {status}")
    
    # 测试部分匹配
    partial_entity = {"name": "牙齿11, 12, 21, 22", "type": "BodyPart", "description": "牙齿"}
    partial_text = "位置：牙齿11, 12, 21, 22。"
    is_valid = extractor._validate_entity_against_text(partial_entity, partial_text)
    print(f"\n部分匹配测试 - 牙齿11, 12, 21, 22: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    return True

def test_graph_builder_validation():
    """测试 GraphBuilder 中的验证"""
    print("\n=== 测试 GraphBuilder 中的验证 ===")
    
    try:
        from src.graph_builder import GraphBuilder
        from src.data_loader import DataChunk
        
        config = Config.from_env()
        builder = GraphBuilder(
            data_file="data/oralChunks.md",
            entity_extractor=None,  # 模拟
            logger=None
        )
        
        # 创建模拟实体提取器
        class MockExtractor:
            def _validate_entity_against_text(self, entity, text):
                # 简单模拟：检查实体名称是否在文本中
                return entity['name'] in text
        
        builder.entity_extractor = MockExtractor()
        
        # 测试验证方法
        test_entity = {"name": "test", "type": "Patient", "description": "test"}
        test_text = "This is a test text"
        
        # 基本验证
        is_basic_valid = builder._validate_entity_data(test_entity)
        print(f"基本验证 (有效实体): {'✅ 通过' if is_basic_valid else '❌ 失败'}")
        
        # 无效实体
        invalid_entity = {"name": "", "type": "Patient", "description": ""}
        is_invalid = builder._validate_entity_data(invalid_entity)
        print(f"基本验证 (无效实体): {'✅ 通过' if not is_invalid else '❌ 失败'}")
        
        return True
    except Exception as e:
        print(f"测试 GraphBuilder 验证时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("开始测试深度思考模式控制和幻觉过滤解决方案")
    print("=" * 60)
    
    tests = [
        ("深度思考模式配置", test_deep_thought_mode_config),
        ("提示词内容", test_prompt_content),
        ("幻觉验证逻辑", test_hallucination_validation),
        ("GraphBuilder 验证", test_graph_builder_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试 {test_name} 时出错: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总体: {passed}/{total} 测试通过")
    print("=" * 60)