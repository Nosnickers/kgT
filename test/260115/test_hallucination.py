#!/usr/bin/env python3
"""测试LLM幻觉问题是否已解决"""
import sys
sys.path.append('src')
import logging
from config import Config
from src.entity_extractor import EntityExtractor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_first_chunk():
    """测试第一个病历片断"""
    print("=== 测试第一个病历片断（患者林悦）===")
    
    # 读取第一个病历片断
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
    print(f"测试文本:\n{text}\n")
    
    # 创建配置和提取器
    config = Config.from_env()
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    print(f"使用模型: {config.ollama.model}")
    print(f"温度: {config.ollama.temperature}")
    print(f"深度思考模式: {config.ollama.deep_thought_mode}")
    print()
    
    try:
        # 提取实体和关系
        print("正在调用LLM进行提取...")
        result = extractor.extract(text, max_retries=1)
        
        # 检查结果
        print(f"\n提取结果:")
        print(f"实体数量: {len(result.entities)}")
        print(f"关系数量: {len(result.relationships)}")
        
        # 检查是否有幻觉实体
        hallucination_keywords = ['李明', 'PID123456', '牙痛', '牙龈出血', '牙周炎', '青霉素过敏', '糖尿病史']
        hallucination_found = False
        
        print("\n提取的实体:")
        for entity in result.entities:
            print(f"  - {entity.name} ({entity.type}): {entity.description}")
            # 检查是否包含幻觉关键词
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

def test_prompt_generation():
    """测试提示词生成"""
    print("\n=== 测试提示词生成 ===")
    
    config = Config.from_env()
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    prompt = extractor.create_extraction_prompt()
    test_text = "测试文本"
    messages = prompt.format_messages(text=test_text)
    
    print(f"系统提示词长度: {len(messages[0].content)} 字符")
    print(f"用户提示词长度: {len(messages[1].content)} 字符")
    
    # 检查系统提示词是否包含示例
    system_content = messages[0].content
    if '(e.g.,' in system_content:
        print("⚠️  系统提示词中仍包含示例 (e.g., ...)")
    else:
        print("✅ 系统提示词中无示例")
    
    if 'Example:' in system_content:
        print("⚠️  系统提示词中仍包含 'Example:'")
    else:
        print("✅ 系统提示词中无 'Example:'")
    
    if 'NO HALLUCINATION POLICY' in system_content:
        print("✅ 系统提示词包含抗幻觉策略")
    else:
        print("⚠️  系统提示词缺少抗幻觉策略")
    
    return True

if __name__ == '__main__':
    print("开始测试LLM幻觉问题解决方案")
    print("=" * 60)
    
    prompt_test = test_prompt_generation()
    
    print("\n" + "=" * 60)
    print("注意: 以下测试需要Ollama服务运行在 http://localhost:11434")
    print("如果服务未运行，提取测试将失败")
    print("=" * 60 + "\n")
    
    extraction_test = test_first_chunk()
    
    print("\n" + "=" * 60)
    if extraction_test:
        print("总体结果: ✅ 测试通过")
    else:
        print("总体结果: ❌ 测试失败")
    print("=" * 60)