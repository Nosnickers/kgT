# 验证完整的数据加载和去重效果
import sys
sys.path.append('src')
from data_loader import DataLoader
import hashlib

loader = DataLoader('data/oralChunks.md')
chunks = loader.load_and_chunk()
print(f"Total chunks: {len(chunks)}")

# Check for duplicates
content_hashes = {}
duplicate_count = 0
for i, chunk in enumerate(chunks):
    content = chunk.content
    # Normalize whitespace
    content_norm = ' '.join(content.split())
    h = hashlib.md5(content_norm.encode('utf-8')).hexdigest()
    if h in content_hashes:
        duplicate_count += 1
        print(f"Chunk {i} duplicates chunk {content_hashes[h]}")
    else:
        content_hashes[h] = i

print(f"Duplicate chunks: {duplicate_count}")
print(f"Unique chunks: {len(content_hashes)}")

# Print first few chunks
for i in range(min(5, len(chunks))):
    chunk = chunks[i]
    print(f"\nChunk {i}:")
    print(f"  Title: {chunk.metadata.get('title', '')}")
    print(f"  Chunk ID: {chunk.metadata.get('chunk_id', '')}")
    print(f"  Word count: {chunk.metadata.get('word_count', '')}")
    print(f"  Content preview: {chunk.content[:100]}...")

# Print chunk size distribution
chunk_sizes = [len(chunk.content.split()) for chunk in chunks]
print(f"\nChunk size distribution: min={min(chunk_sizes)}, max={max(chunk_sizes)}, avg={sum(chunk_sizes)/len(chunk_sizes):.1f}")