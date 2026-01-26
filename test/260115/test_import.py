# 验证所有模块导入和基本功能
import sys
sys.path.append('src')

# Test imports
try:
    from data_loader import DataLoader
    from entity_extractor import EntityExtractor
    from graph_builder import GraphBuilder
    from neo4j_manager import Neo4jManager
    print("All imports successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

# Test data loader with a small file
import tempfile
import os

# Create a minimal markdown file with header pattern
test_content = """# Test Header
This is a test content.
病历片断 1：患者基本信息 - 测试
内容：
病历号：TEST123
姓名：测试
"""
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
    f.write(test_content)
    temp_file = f.name

try:
    loader = DataLoader(temp_file, chunk_size=100, chunk_overlap=20)
    chunks = loader.load_and_chunk()
    print(f"DataLoader test: loaded {len(chunks)} chunks")
    for chunk in chunks:
        print(f"  Chunk title: {chunk.metadata.get('title')}, words: {chunk.metadata.get('word_count')}")
finally:
    os.unlink(temp_file)

print("All tests passed")