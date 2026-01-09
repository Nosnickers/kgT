import re
from typing import List, Dict, Any
from pathlib import Path


class DataChunk:
    def __init__(self, content: str, metadata: Dict[str, Any]):
        self.content = content
        self.metadata = metadata

    def __repr__(self):
        return f"DataChunk(length={len(self.content)}, metadata={self.metadata})"


class DataLoader:
    def __init__(self, file_path: str, chunk_size: int = 2000, chunk_overlap: int = 200):
        self.file_path = Path(file_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_markdown(self) -> str:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    def clean_text(self, text: str) -> str:
        text = re.sub(r'Image /page/\d+/Picture/\d+ description: \{.*?\}', '', text, flags=re.DOTALL)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return text

    def split_by_headers(self, text: str) -> List[Dict[str, str]]:
        sections = []
        current_section = {"title": "Introduction", "content": ""}
        
        lines = text.split('\n')
        for line in lines:
            if line.startswith('#'):
                if current_section["content"].strip():
                    sections.append(current_section)
                title = re.sub(r'^#+\s*', '', line).strip()
                current_section = {"title": title, "content": ""}
            else:
                current_section["content"] += line + '\n'
        
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections

    def chunk_text(self, text: str, title: str = "", start_chunk_id: int = 0) -> List[DataChunk]:
        chunks = []
        words = text.split()
        current_chunk = ""
        chunk_count = start_chunk_id
        
        for i, word in enumerate(words):
            if len(current_chunk) + len(word) + 1 > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(DataChunk(
                        content=current_chunk.strip(),
                        metadata={
                            "title": title,
                            "chunk_id": chunk_count,
                            "word_count": len(current_chunk.split())
                        }
                    ))
                    chunk_count += 1
                
                overlap_words = current_chunk.split()[-self.chunk_overlap:]
                current_chunk = ' '.join(overlap_words) + ' ' + word + ' '
            else:
                current_chunk += word + ' '
        
        if current_chunk.strip():
            chunks.append(DataChunk(
                content=current_chunk.strip(),
                metadata={
                    "title": title,
                    "chunk_id": chunk_count,
                    "word_count": len(current_chunk.split())
                }
            ))
            chunk_count += 1
        
        # 返回下一个可用的chunk_id，而不是当前chunk_count
        # 如果没有创建任何chunk，返回start_chunk_id
        next_chunk_id = chunk_count if chunks else start_chunk_id
        return chunks, next_chunk_id

    def load_and_chunk(self) -> List[DataChunk]:
        raw_text = self.load_markdown()
        cleaned_text = self.clean_text(raw_text)
        sections = self.split_by_headers(cleaned_text)
        
        all_chunks = []
        global_chunk_count = 0
        
        for section in sections:
            chunks, chunk_count = self.chunk_text(section["content"], section["title"], global_chunk_count)
            all_chunks.extend(chunks)
            global_chunk_count = chunk_count
        
        return all_chunks

    def get_stats(self, chunks: List[DataChunk]) -> Dict[str, Any]:
        total_chunks = len(chunks)
        total_words = sum(chunk.metadata.get("word_count", 0) for chunk in chunks)
        avg_words = total_words / total_chunks if total_chunks > 0 else 0
        
        sections = {}
        for chunk in chunks:
            title = chunk.metadata.get("title", "Unknown")
            if title not in sections:
                sections[title] = 0
            sections[title] += 1
        
        return {
            "total_chunks": total_chunks,
            "total_words": total_words,
            "avg_words_per_chunk": avg_words,
            "sections": sections
        }

    def save_chunks_to_csv(self, chunks: List[DataChunk], output_prefix: str) -> None:
        """
        将数据块保存为csv文件
        
        Args:
            chunks: 数据块列表
            output_prefix: 输出文件名前缀，与日志文件名保持一致
        """
        import pandas as pd
        import logging
        
        # 准备csv数据
        csv_data = []
        for chunk in chunks:
            csv_data.append({
                "content": chunk.content,
                "title": chunk.metadata.get("title", ""),
                "chunk_id": chunk.metadata.get("chunk_id", 0),
                "word_count": chunk.metadata.get("word_count", 0)
            })
        
        # 创建DataFrame
        df = pd.DataFrame(csv_data)
        
        # 生成输出文件名
        output_file = f"{output_prefix}.csv"
        
        # 保存为csv文件
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # 记录保存信息
        logging.info(f"已将 {len(chunks)} 个数据块保存到 {output_file}")
