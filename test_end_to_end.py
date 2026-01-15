#!/usr/bin/env python3
"""端到端测试：验证深度思考模式和幻觉过滤"""
import sys
sys.path.append('src')
import logging
import json
from config import Config
from src.entity_extractor import EntityExtractor

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def load_first_chunk():
    """加载第一个病历片断"""
    with open('data/oralChunks.md', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 提取第一个病历片断内容（直到第二个病历片断开始）
    first_chunk_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            # 第一行是标题
            continue
        if line.startswith('病历片断 2：'):
            break
        first_chunk_lines.append(line)
    
    text = ''.join(first_chunk_lines).strip()
    return text

def test_extraction_without_hallucination():
    """测试提取，确保无幻觉实体"""
    print("=== 端到端测试：验证深度思考模式和幻觉过滤 ===")
    
    config = Config.from_env()
    print(f"配置: model={config.ollama.model}, deep_thought_mode={config.ollama.deep_thought_mode}")
    
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    text = load_first_chunk()
    print(f"\n测试文本（前200字符）: {text[:200]}...")
    
    print("\n正在调用LLM进行提取...（可能需要几分钟）")
    try:
        result = extractor.extract(text, max_retries=1)
        
        print(f"\n提取结果:")
        print(f"实体数量: {len(result.entities)}")
        print(f"关系数量: {len(result.relationships)}")
        
        # 检查是否有幻觉实体
        hallucination_keywords = ['李明', '张三', '李四', '牙痛', '龋齿', '青霉素过敏', '糖尿病史']
        hallucination_found = False
        
        print("\n提取的实体:")
        for entity in result.entities:
            print(f"  - {entity.name} ({entity.type}): {entity.description}")
            for keyword in hallucination_keywords:
                if keyword in entity.name:
                    print(f"    ⚠️  警告: 实体包含幻觉关键词 '{keyword}'!")
                    hallucination_found = True
        
        print("\n提取的关系:")
        for rel in result.relationships:
            print(f"  - {rel.source} --[{rel.type}]--> {rel.target}")
        
        if hallucination_found:
            print("\n❌ 测试失败: 检测到幻觉实体")
            return False
        else:
            print("\n✅ 测试通过: 未检测到幻觉实体")
            
            # 验证是否提取了正确的实体
            expected_entities = ['林悦', 'MK20231026018', '女', '32岁', '外企项目经理', '是']
            found_expected = 0
            for expected in expected_entities:
                for entity in result.entities:
                    if expected in entity.name:
                        found_expected += 1
                        break
            
            print(f"\n预期实体匹配: {found_expected}/{len(expected_entities)}")
            if found_expected >= len(expected_entities) // 2:
                print("✅ 提取了大部分预期实体")
            else:
                print("⚠️  部分预期实体未提取")
            
            return True
            
    except Exception as e:
        print(f"\n❌ 提取过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deep_thought_mode():
    """测试深度思考模式是否生效"""
    print("\n=== 测试深度思考模式 ===")
    
    # 检查配置
    config = Config.from_env()
    print(f"OLLAMA_DEEP_THOUGHT_MODE: {config.ollama.deep_thought_mode}")
    
    # 创建提取器
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    # 检查LLM配置
    llm = extractor.llm
    print(f"LLM类型: {type(llm)}")
    
    # 检查是否有stop参数
    if hasattr(llm, 'stop'):
        print(f"LLM stop参数: {llm.stop}")
        if config.ollama.deep_thought_mode == False and llm.stop == ['<think>', '</think>']:
            print("✅ 深度思考模式已正确禁用")
        else:
            print("⚠️  深度思考模式配置可能有问题")
    else:
        print("⚠️  LLM没有stop参数")
    
    # 检查提示词
    prompt = extractor.create_extraction_prompt()
    messages = prompt.format_messages(text="测试")
    system_content = messages[0].content
    
    if "NO THINKING OUTPUT" in system_content:
        print("✅ 提示词包含禁止思考输出的指令")
    else:
        print("⚠️  提示词缺少禁止思考输出的指令")
    
    if "DO NOT output any thinking process" in system_content:
        print("✅ 提示词包含禁止思考过程输出的具体指令")
    else:
        print("⚠️  提示词缺少禁止思考过程输出的具体指令")
    
    return True

if __name__ == '__main__':
    print("开始端到端测试")
    print("=" * 60)
    print("注意: 此测试需要Ollama服务运行在 http://localhost:11434")
    print("如果服务未运行，提取测试将失败")
    print("=" * 60)
    
    # 测试深度思考模式配置
    deep_thought_test = test_deep_thought_mode()
    
    print("\n" + "=" * 60)
    print("开始实体提取测试...")
    print("=" * 60)
    
    # 测试提取
    extraction_test = test_extraction_without_hallucination()
    
    print("\n" + "=" * 60)
    if extraction_test:
        print("总体结果: ✅ 测试通过")
    else:
        print("总体结果: ❌ 测试失败")
    print("=" * 60)