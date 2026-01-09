#!/usr/bin/env python3
"""
测试实体提取功能，验证实体名称是否正确提取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.entity_extractor import EntityExtractor
import json

def test_entity_extraction():
    # 创建实体提取器（使用默认配置）
    extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="mistral:7b-instruct-v0.3-q4_0",
        temperature=0.1,
        num_ctx=4096,
        deep_thought_mode=False
    )
    
    # 测试文本
    test_text = """
Apple is committed to achieving carbon neutrality by 2030. The company has implemented various initiatives 
like using recycled aluminum in MacBook Air and reducing water usage in its supply chain. Apple's 
Environmental Progress Report highlights the company's partnership with suppliers in China and Brazil.
"""
    
    print("测试文本:")
    print(test_text)
    print("\n开始提取实体和关系...")
    
    try:
        # 提取实体和关系
        result = extractor.extract(test_text)
        
        print(f"\n✅ 提取完成: 找到 {len(result.entities)} 个实体, {len(result.relationships)} 个关系")
        
        # 检查实体名称
        print("\n📋 提取的实体:")
        for i, entity in enumerate(result.entities, 1):
            print(f"  {i}. 名称: '{entity.name}'")
            print(f"     类型: {entity.type}")
            print(f"     描述: {entity.description}")
            
            # 检查实体名称是否包含占位符
            if "entity_name" in entity.name.lower() or "brief description" in entity.name.lower():
                print(f"     ❌ 警告: 实体名称可能包含占位符!")
            elif entity.name.strip() == "":
                print(f"     ❌ 警告: 实体名称为空!")
            else:
                print(f"     ✅ 实体名称正常")
        
        # 检查关系
        print("\n🔗 提取的关系:")
        for i, rel in enumerate(result.relationships, 1):
            print(f"  {i}. 源: '{rel.source}' -> 目标: '{rel.target}'")
            print(f"     类型: {rel.type}")
            print(f"     描述: {rel.description}")
            
            # 检查关系名称是否包含占位符
            if any(placeholder in rel.source.lower() or placeholder in rel.target.lower() 
                   for placeholder in ["source_entity_name", "target_entity_name", "brief description"]):
                print(f"     ❌ 警告: 关系实体名称可能包含占位符!")
            else:
                print(f"     ✅ 关系实体名称正常")
        
        # 验证提取结果
        if len(result.entities) > 0 and all(entity.name.strip() != "" for entity in result.entities):
            print(f"\n🎉 实体提取测试通过!")
            return True
        else:
            print(f"\n❌ 实体提取测试失败!")
            return False
            
    except Exception as e:
        print(f"❌ 提取过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试实体提取功能...")
    success = test_entity_extraction()
    if success:
        print("\n🎉 实体提取功能正常!")
    else:
        print("\n❌ 实体提取功能存在问题，需要进一步调试")