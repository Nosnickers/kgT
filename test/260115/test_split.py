# 验证标题检测功能
import sys
sys.path.append('src')
from data_loader import DataLoader

loader = DataLoader('data/oralChunks.md')
with open('data/oralChunks.md', 'r', encoding='utf-8') as f:
    text = f.read()

sections = loader.split_by_headers(text)
print(f"Number of sections: {len(sections)}")
for i, section in enumerate(sections):
    print(f"Section {i}: title='{section['title']}', content length={len(section['content'])}")
    # print first 100 chars of content
    print(f"  Content preview: {section['content'][:100]}...")
    print()