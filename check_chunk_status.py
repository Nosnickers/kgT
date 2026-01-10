#!/usr/bin/env python3
"""
检查数据块状态和数量
"""

import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_loader import DataLoader

def main():
    """主函数"""
    print("=== 检查数据块状态 ===")
    
    try:
        # 检查Dulce.json文件
        loader = DataLoader('data/Dulce.json', chunk_size=800, chunk_overlap=100)
        chunks = loader.load_and_chunk()
        stats = loader.get_stats(chunks)
        
        print('=== 当前数据块状态 ===')
        print(f'总数据块数: {stats["total_chunks"]}')
        print(f'总字数: {stats["total_words"]}')
        print(f'平均每块字数: {stats["avg_words_per_chunk"]:.1f}')
        
        # 检查chunk_id范围
        chunk_ids = [chunk.metadata.get('chunk_id', 0) for chunk in chunks]
        if chunk_ids:
            print(f'chunk_id范围: {min(chunk_ids)} - {max(chunk_ids)}')
            print(f'实际chunk数量: {len(chunk_ids)}')
        
        # 检查前几个chunk的详细信息
        print('\n=== 前5个数据块信息 ===')
        for i, chunk in enumerate(chunks[:5]):
            print(f'chunk_id: {chunk.metadata.get("chunk_id", "N/A")}, 标题: {chunk.metadata.get("title", "N/A")}, 字数: {chunk.metadata.get("word_count", 0)}')
        
        # 检查最后几个chunk的详细信息
        print('\n=== 最后5个数据块信息 ===')
        for i, chunk in enumerate(chunks[-5:]):
            print(f'chunk_id: {chunk.metadata.get("chunk_id", "N/A")}, 标题: {chunk.metadata.get("title", "N/A")}, 字数: {chunk.metadata.get("word_count", 0)}')
        
        # 检查是否有重复的chunk_id
        unique_chunk_ids = set(chunk_ids)
        if len(unique_chunk_ids) != len(chunk_ids):
            print(f'\n⚠️ 警告: 发现重复的chunk_id! 唯一chunk_id数量: {len(unique_chunk_ids)}, 总chunk数量: {len(chunk_ids)}')
        else:
            print(f'\n✅ chunk_id唯一性检查通过')
            
        # 检查chunk_id序列是否连续
        expected_ids = list(range(min(chunk_ids), max(chunk_ids) + 1))
        missing_ids = set(expected_ids) - set(chunk_ids)
        if missing_ids:
            print(f'⚠️ 警告: 发现缺失的chunk_id: {sorted(missing_ids)}')
        else:
            print('✅ chunk_id序列连续性检查通过')
            
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()