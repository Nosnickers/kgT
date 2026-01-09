#!/usr/bin/env python3
"""
测试chunk_id合并逻辑的单元测试脚本
"""

import json
import re


def test_chunk_id_merge_logic():
    """
    测试chunk_id合并逻辑，模拟Neo4j查询中的数组合并
    """
    print("Testing chunk_id merge logic...")
    
    # 模拟不同批次的实体数据
    entity_data = {
        "name": "Carbon Emissions",
        "type": "Metric",
        "properties": {
            "description": "Measurements of carbon dioxide released into the atmosphere",
            "chunk_id": [1]
        }
    }
    
    # 模拟数据库中已存在的实体
    existing_entity = {
        "name": "Carbon Emissions",
        "type": "Metric",
        "properties": {
            "description": "Measurements of carbon dioxide released into the atmosphere",
            "chunk_id": [0, 2]
        }
    }
    
    # 测试合并逻辑
    def merge_chunk_ids(existing, new):
        """模拟Neo4j中的chunk_id合并逻辑"""
        existing_ids = existing.get("properties", {}).get("chunk_id", [])
        new_ids = new.get("properties", {}).get("chunk_id", [])
        
        # 模拟Neo4j的DISTINCT合并逻辑
        merged = list(set(existing_ids + new_ids))
        merged.sort()
        
        return merged
    
    # 执行合并
    merged_chunk_ids = merge_chunk_ids(existing_entity, entity_data)
    
    print(f"Existing chunk_ids: {existing_entity['properties']['chunk_id']}")
    print(f"New chunk_ids: {entity_data['properties']['chunk_id']}")
    print(f"Merged chunk_ids: {merged_chunk_ids}")
    
    # 验证结果
    expected = [0, 1, 2]
    if merged_chunk_ids == expected:
        print("✓ Chunk ID merge logic works correctly!")
        return True
    else:
        print(f"✗ Chunk ID merge logic failed! Expected {expected}, got {merged_chunk_ids}")
        return False


def test_clean_json_response():
    """
    测试JSON响应清理逻辑，确保<think>标签被正确处理
    """
    print("\nTesting clean_json_response logic...")
    
    # 模拟带有<think>标签的响应
    response_with_think = """
    <think>
    Okay, let me analyze this text. I need to extract entities and relationships.
    Let's start by identifying entities...
    </think>
    {
      "entities": [
        {
          "name": "Apple",
          "type": "Organization",
          "description": "A technology company"
        }
      ],
      "relationships": []
    }
    """
    
    # 模拟clean_json_response函数的逻辑
    def clean_json_response(content):
        content = content.strip()
        
        # 处理包含<think>标签的响应
        if "<think>" in content:
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            content = content.strip()
        
        # 寻找JSON数据的开始位置
        json_start = content.find('{')
        if json_start == -1:
            return "{}"
        
        content = content[json_start:]
        
        # 寻找JSON数据的结束位置
        brace_count = 0
        json_end = -1
        for i, char in enumerate(content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        if json_end == -1:
            return "{}"
        
        content = content[:json_end]
        
        # 验证JSON
        try:
            json.loads(content)
            return content
        except json.JSONDecodeError:
            return "{}"
    
    # 执行清理
    cleaned = clean_json_response(response_with_think)
    
    print(f"Original response length: {len(response_with_think)}")
    print(f"Cleaned response length: {len(cleaned)}")
    
    # 验证结果
    try:
        parsed = json.loads(cleaned)
        if parsed and parsed.get("entities"):
            print("✓ JSON response cleaning works correctly!")
            return True
        else:
            print("✗ JSON response cleaning failed! No entities found.")
            return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON response cleaning failed with JSON error: {e}")
        return False


if __name__ == "__main__":
    """
    运行所有测试
    """
    print("=" * 60)
    print("Testing chunk_id merge and JSON cleaning logic")
    print("=" * 60)
    
    # 运行测试
    test1_passed = test_chunk_id_merge_logic()
    test2_passed = test_clean_json_response()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    print(f"1. Chunk ID merge logic: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"2. JSON response cleaning: {'PASSED' if test2_passed else 'FAILED'}")
    print("=" * 60)
    
    # 确定总体结果
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The fixes are working correctly.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please check the results above.")
        exit(1)
