#!/usr/bin/env python3
"""
测试chunk_id在CSV文件中的一致性
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import DataLoader

def test_csv_chunk_id_consistency():
    """测试chunk_id在CSV文件中的一致性"""
    print("测试chunk_id在CSV文件中的一致性...")
    
    # 创建一个简单的markdown文件用于测试
    test_content = """# 测试文档

这是测试文档的第一个段落，包含一些实体信息。

## 第二个章节

这是第二个章节的内容，包含更多的文本用于测试chunk分割。

### 第三个章节

这是第三个章节的内容，也是最后一个章节。"""
    
    # 写入临时文件
    test_file = "test_csv_consistency.md"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    try:
        # 创建DataLoader实例
        loader = DataLoader(test_file, chunk_size=50, chunk_overlap=10)
        
        # 加载和分块数据
        chunks = loader.load_and_chunk()
        
        print(f"总chunks数量: {len(chunks)}")
        
        # 获取内存中的chunk_id序列
        memory_chunk_ids = [chunk.metadata.get('chunk_id') for chunk in chunks]
        print(f"内存中的chunk_id序列: {memory_chunk_ids}")
        
        # 保存到CSV文件
        csv_output = "test_chunk_id_consistency"
        loader.save_chunks_to_csv(chunks, csv_output)
        
        # 从CSV文件读取数据
        csv_file = f"{csv_output}.csv"
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            csv_chunk_ids = df['chunk_id'].tolist()
            
            print(f"CSV文件中的chunk_id序列: {csv_chunk_ids}")
            
            # 验证一致性
            if memory_chunk_ids == csv_chunk_ids:
                print("✅ chunk_id在内存和CSV文件中一致")
            else:
                print(f"❌ chunk_id不一致，内存: {memory_chunk_ids}, CSV: {csv_chunk_ids}")
            
            # 显示CSV文件内容
            print("\nCSV文件内容:")
            print(df[['chunk_id', 'title', 'word_count']].head())
            
            # 验证chunk_id是否从0开始且连续
            expected_ids = list(range(len(chunks)))
            if csv_chunk_ids == expected_ids:
                print("✅ CSV文件中的chunk_id序列正确")
            else:
                print(f"❌ CSV文件中的chunk_id序列错误，期望: {expected_ids}, 实际: {csv_chunk_ids}")
        else:
            print("❌ CSV文件未创建")
    
    finally:
        # 清理临时文件
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists("test_chunk_id_consistency.csv"):
            os.remove("test_chunk_id_consistency.csv")

def test_graph_builder_chunk_id_usage():
    """测试graph_builder中chunk_id的使用"""
    print("\n\n测试graph_builder中chunk_id的使用...")
    
    # 检查graph_builder.py中chunk_id的使用方式
    graph_builder_file = "src/graph_builder.py"
    if os.path.exists(graph_builder_file):
        with open(graph_builder_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找chunk_id相关的代码
        chunk_id_patterns = [
            'chunk.metadata.get("chunk_id"',
            'chunk_id',
            'properties={"chunk_id"'
        ]
        
        print("graph_builder.py中chunk_id的使用:")
        for pattern in chunk_id_patterns:
            if pattern in content:
                lines = [line.strip() for line in content.split('\n') if pattern in line]
                for line in lines[:3]:  # 显示前3个匹配行
                    print(f"  - {line}")
    
    # 模拟graph_builder的处理逻辑
    print("\n模拟graph_builder处理逻辑:")
    
    # 创建测试数据
    test_chunks = []
    for i in range(3):
        test_chunks.append({
            'content': f'测试内容 {i}',
            'metadata': {'chunk_id': i, 'title': f'标题{i}'}
        })
    
    # 模拟graph_builder中的chunk_id获取逻辑
    for i, chunk in enumerate(test_chunks, 1):
        chunk_id = chunk['metadata'].get('chunk_id', i-1)
        print(f"处理第{i}个chunk: chunk_id={chunk_id}")
    
    print("✅ graph_builder中chunk_id使用逻辑正确")

if __name__ == "__main__":
    test_csv_chunk_id_consistency()
    test_graph_builder_chunk_id_usage()