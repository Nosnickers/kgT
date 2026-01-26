#!/usr/bin/env python3
"""
测试clean_json_response方法对包含<think>标签的响应处理
"""

from src.entity_extractor import EntityExtractor


def test_clean_json_response():
    """测试clean_json_response方法"""
    print("测试clean_json_response方法对包含<think>标签的响应处理...")
    
    # 创建实体提取器实例
    entity_extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="deepseek-r1:8b",
        deep_thought_mode=True
    )
    
    # 测试用例1: 包含<think>标签的响应，末尾有无效内容
    test_case_1 = '''{<think>
Okay, so I need to extract entities and relationships from a given text. The user provided an example where they had a sample text about Apple's environmental initiatives, and they extracted specific entities and relationships. Now, my task is to do the same for whatever text comes next.

Wait, but in this case, the user hasn't provided the actual text yet. They just instructed me on how to extract. So maybe I should prompt them for the text? Or perhaps I'm supposed to handle it when they provide it. Hmm.

I think the best approach is to wait for the user to supply the text so I can process it accordingly. Without the text, I can't perform any extraction. So I'll let them know that once they provide the text, I can proceed with the extraction using their specified rules and entity types.

I should make sure my response is clear and polite, asking them to provide the necessary text for me to work on. That way, everything stays organized and efficient.
</think>

Please provide the text you'd like me to extract entities and relationships from. Once I have it, I'll perform the extraction using the specified rules and entity types.}"'''
    
    # 测试用例2: 正常的JSON响应
    test_case_2 = '''```json
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
```"'''
    
    # 测试用例3: 包含<think>标签和有效JSON的响应
    test_case_3 = '''{<think>
Okay, let's analyze this text. The main entity is Apple, which is an organization. They have a goal of carbon neutrality by 2030. Let me extract the entities and relationships properly.
</think>

```json
{
  "entities": [
    {
      "name": "Apple",
      "type": "Organization",
      "description": "A major technology company"
    },
    {
      "name": "carbon neutrality by 2030",
      "type": "Goal",
      "description": "Apple's environmental target"
    }
  ],
  "relationships": [
    {
      "source": "Apple",
      "target": "carbon neutrality by 2030",
      "type": "ACHIEVES",
      "description": "Apple is committed to achieving carbon neutrality by 2030"
    }
  ]
}
```"'''
    
    # 运行测试用例
    test_cases = [
        ("测试用例1: 包含<think>标签的无效响应", test_case_1),
        ("测试用例2: 正常JSON响应", test_case_2),
        ("测试用例3: 包含<think>标签的有效JSON响应", test_case_3)
    ]
    
    for test_name, test_content in test_cases:
        print(f"\n{test_name}:")
        print(f"原始响应长度: {len(test_content)}")
        
        # 调用clean_json_response方法
        cleaned = entity_extractor.clean_json_response(test_content)
        print(f"清理后长度: {len(cleaned)}")
        print(f"清理后内容: {cleaned}")
        
        # 验证是否为有效的JSON
        try:
            import json
            json.loads(cleaned)
            print("✅ 有效JSON")
        except json.JSONDecodeError:
            print("❌ 无效JSON")
    
    print("\n所有测试用例执行完成！")


if __name__ == "__main__":
    test_clean_json_response()
