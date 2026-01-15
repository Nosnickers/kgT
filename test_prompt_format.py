#!/usr/bin/env python3
"""
测试提示词格式化功能
验证 {text} 占位符是否被正确替换
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.entity_extractor import EntityExtractor

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_prompt_formatting():
    """测试提示词格式化"""
    print("=== 测试提示词格式化 ===")
    
    # 创建一个 EntityExtractor 实例（使用模拟配置）
    # 参数: base_url, model, temperature=0.1, num_ctx=4096, deep_thought_mode=False
    extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="deepseek-r1:8b",
        temperature=0.1,
        num_ctx=4096,
        deep_thought_mode=False
    )
    
    # 创建提示模板
    print("\n1. 创建提示模板...")
    prompt_template = extractor.create_extraction_prompt()
    
    print(f"提示模板类型: {type(prompt_template)}")
    if hasattr(prompt_template, 'input_variables'):
        print(f"input_variables: {prompt_template.input_variables}")
    print(f"消息数量: {len(prompt_template.messages)}")
    
    # 检查消息内容
    for i, msg in enumerate(prompt_template.messages):
        print(f"\n消息 {i} 类型: {type(msg).__name__}")
        content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
        print(f"内容预览: {content_preview}")
        # 检查是否包含 {text} 占位符
        if "{text}" in msg.content:
            print("✓ 包含 {text} 占位符")
        else:
            print("✗ 不包含 {text} 占位符")
    
    # 测试格式化
    print("\n2. 测试提示词格式化...")
    test_text = "病历号：MK20231026018 姓名：林悦 性别：女 年龄：32岁 职业：外企项目经理 首次就诊：是"
    
    try:
        # 方法1: 使用 format_messages
        formatted_messages = prompt_template.format_messages(text=test_text)
        print(f"\nformat_messages 成功，返回 {len(formatted_messages)} 条消息")
        
        for i, msg in enumerate(formatted_messages):
            print(f"\n格式化后消息 {i} 类型: {type(msg).__name__}")
            content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            print(f"内容预览: {content_preview}")
            # 检查是否仍然包含 {text} 或 <text>
            if "{text}" in msg.content:
                print("⚠️  警告: 仍然包含 {text} 占位符")
            if "<text>" in msg.content:
                print("⚠️  警告: 包含 <text> 占位符")
            if test_text in msg.content:
                print("✓ 包含实际病历内容")
            else:
                print("✗ 不包含实际病历内容")
        
        # 方法2: 直接格式化用户提示词
        print("\n3. 测试直接字符串格式化...")
        if len(prompt_template.messages) > 1:
            human_prompt = prompt_template.messages[1].content
            try:
                direct_formatted = human_prompt.format(text=test_text)
                print(f"直接格式化成功")
                print(f"格式化后内容预览: {direct_formatted[:200]}...")
                if "{text}" in direct_formatted:
                    print("⚠️  警告: 直接格式化后仍然包含 {text} 占位符")
                if test_text in direct_formatted:
                    print("✓ 直接格式化包含实际病历内容")
                else:
                    print("✗ 直接格式化不包含实际病历内容")
            except Exception as e:
                print(f"直接格式化失败: {e}")
        
    except Exception as e:
        print(f"格式化失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_prompt_formatting()