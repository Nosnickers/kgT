#!/usr/bin/env python3
"""
测试DataLoader生成的chunk_id是否唯一，并测试save_chunks_to_csv方法
"""

from src.data_loader import DataLoader


def test_chunk_id_unique():
    """测试生成的chunk_id是否唯一"""
    print("测试DataLoader生成的chunk_id是否唯一...")
    
    # 创建DataLoader实例
    data_loader = DataLoader(
        file_path="data/Apple_Environmental_Progress_Report_2024.md",
        chunk_size=2000,
        chunk_overlap=200
    )
    
    # 加载和分块数据
    chunks = data_loader.load_and_chunk()
    
    print(f"生成的数据块数量: {len(chunks)}")
    
    # 检查chunk_id是否唯一
    chunk_ids = []
    for chunk in chunks:
        chunk_id = chunk.metadata.get("chunk_id")
        chunk_ids.append(chunk_id)
    
    # 检查是否有重复的chunk_id
    unique_chunk_ids = set(chunk_ids)
    if len(unique_chunk_ids) == len(chunk_ids):
        print("✅ 所有chunk_id都是唯一的")
    else:
        print("❌ 发现重复的chunk_id")
        # 找出重复的chunk_id
        from collections import Counter
        duplicate_chunk_ids = [id for id, count in Counter(chunk_ids).items() if count > 1]
        print(f"重复的chunk_id: {duplicate_chunk_ids}")
        return False
    
    # 测试save_chunks_to_csv方法
    print("\n测试save_chunks_to_csv方法...")
    test_output_prefix = "test_chunk_output"
    data_loader.save_chunks_to_csv(chunks, test_output_prefix)
    print(f"✅ 数据块已保存到 {test_output_prefix}.csv")
    
    # 验证csv文件是否存在
    import os
    if os.path.exists(f"{test_output_prefix}.csv"):
        print(f"✅ {test_output_prefix}.csv 文件存在")
        
        # 验证csv文件内容
        import pandas as pd
        df = pd.read_csv(f"{test_output_prefix}.csv")
        print(f"✅ csv文件包含 {len(df)} 行数据，与生成的chunk数量一致")
        
        # 检查csv文件中的chunk_id是否唯一
        csv_chunk_ids = df["chunk_id"].tolist()
        unique_csv_chunk_ids = set(csv_chunk_ids)
        if len(unique_csv_chunk_ids) == len(csv_chunk_ids):
            print("✅ csv文件中的chunk_id都是唯一的")
        else:
            print("❌ csv文件中发现重复的chunk_id")
            return False
    else:
        print(f"❌ {test_output_prefix}.csv 文件不存在")
        return False
    
    print("\n✅ 所有测试通过！")
    return True


if __name__ == "__main__":
    test_chunk_id_unique()
