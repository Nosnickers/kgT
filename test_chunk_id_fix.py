#!/usr/bin/env python3
"""
测试chunk_id生成逻辑修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import DataLoader

def test_chunk_id_generation():
    """测试chunk_id生成逻辑"""
    print("测试chunk_id生成逻辑...")
    
    # 创建一个临时的DataLoader实例（不需要实际文件）
    loader = DataLoader("dummy.md", chunk_size=100, chunk_overlap=20)
    
    # 测试1: 短文本（应该生成一个chunk）
    print("\n测试1: 短文本（应该生成一个chunk）")
    short_text = "这是一个很短的文本，用于测试chunk_id生成。"
    chunks, next_id = loader.chunk_text(short_text, "短文本测试", 0)
    
    print(f"生成的chunks数量: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"chunk {i}: chunk_id={chunk.metadata.get('chunk_id')}, 内容长度={len(chunk.content)}")
    print(f"下一个chunk_id: {next_id}")
    
    # 测试2: 中等长度文本（应该生成多个chunk）
    print("\n测试2: 中等长度文本（应该生成多个chunk）")
    medium_text = " "
    for i in range(50):
        medium_text += f"这是第{i}个句子，用于测试chunk分割和chunk_id生成。 "
    
    chunks, next_id = loader.chunk_text(medium_text, "中等文本测试", 0)
    
    print(f"生成的chunks数量: {len(chunks)}")
    chunk_ids = [chunk.metadata.get('chunk_id') for chunk in chunks]
    print(f"chunk_id序列: {chunk_ids}")
    print(f"下一个chunk_id: {next_id}")
    
    # 验证chunk_id序列是否连续
    expected_ids = list(range(len(chunks)))
    if chunk_ids == expected_ids:
        print("✅ chunk_id序列连续正确")
    else:
        print(f"❌ chunk_id序列不连续，期望: {expected_ids}, 实际: {chunk_ids}")
    
    # 测试3: 多个section的处理
    print("\n测试3: 模拟多个section的处理")
    
    # 第一个section
    section1_text = "这是第一个section的内容，比较短。"
    chunks1, next_id1 = loader.chunk_text(section1_text, "Section 1", 0)
    print(f"Section 1: 生成{len(chunks1)}个chunks, 下一个chunk_id={next_id1}")
    
    # 第二个section（使用第一个section返回的next_id）
    section2_text = "这是第二个section的内容，也比较短。"
    chunks2, next_id2 = loader.chunk_text(section2_text, "Section 2", next_id1)
    print(f"Section 2: 生成{len(chunks2)}个chunks, 下一个chunk_id={next_id2}")
    
    # 合并所有chunks
    all_chunks = chunks1 + chunks2
    all_chunk_ids = [chunk.metadata.get('chunk_id') for chunk in all_chunks]
    print(f"所有chunk_id: {all_chunk_ids}")
    
    # 验证chunk_id是否全局连续
    expected_global_ids = list(range(len(all_chunks)))
    if all_chunk_ids == expected_global_ids:
        print("✅ 全局chunk_id序列连续正确")
    else:
        print(f"❌ 全局chunk_id序列不连续，期望: {expected_global_ids}, 实际: {all_chunk_ids}")
    
    # 测试4: 空文本处理
    print("\n测试4: 空文本处理")
    empty_text = ""
    chunks_empty, next_id_empty = loader.chunk_text(empty_text, "空文本", 5)
    print(f"空文本: 生成{len(chunks_empty)}个chunks, 下一个chunk_id={next_id_empty}")
    if len(chunks_empty) == 0 and next_id_empty == 5:
        print("✅ 空文本处理正确")
    else:
        print("❌ 空文本处理错误")

def test_load_and_chunk():
    """测试load_and_chunk方法的chunk_id处理"""
    print("\n\n测试load_and_chunk方法...")
    
    # 创建一个简单的markdown文件用于测试
    test_content = """# 标题1
这是第一个section的内容。

## 标题2
这是第二个section的内容，稍微长一些，用于测试chunk分割。

### 标题3
这是第三个section的内容。"""
    
    # 写入临时文件
    test_file = "test_chunk_id.md"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        loader = DataLoader(test_file, chunk_size=50, chunk_overlap=10)
        chunks = loader.load_and_chunk()
        
        print(f"总chunks数量: {len(chunks)}")
        
        # 检查chunk_id序列
        chunk_ids = [chunk.metadata.get('chunk_id') for chunk in chunks]
        print(f"chunk_id序列: {chunk_ids}")
        
        # 验证是否从0开始且连续
        expected_ids = list(range(len(chunks)))
        if chunk_ids == expected_ids:
            print("✅ load_and_chunk方法chunk_id序列正确")
        else:
            print(f"❌ load_and_chunk方法chunk_id序列错误，期望: {expected_ids}, 实际: {chunk_ids}")
        
        # 显示每个chunk的详细信息
        print("\n每个chunk的详细信息:")
        for chunk in chunks:
            print(f"chunk_id: {chunk.metadata.get('chunk_id')}, "
                  f"title: {chunk.metadata.get('title')}, "
                  f"word_count: {chunk.metadata.get('word_count')}")
    
    finally:
        # 清理临时文件
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_chunk_id_generation()
    test_load_and_chunk()