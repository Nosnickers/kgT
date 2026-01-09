import re
import json
from typing import List, Dict, Any, Union
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
        
    def detect_file_format(self) -> str:
        """检测文件格式"""
        file_extension = self.file_path.suffix.lower()
        if file_extension == '.json':
            return 'json'
        elif file_extension in ['.md', '.markdown', '.txt']:
            return 'markdown'
        else:
            # 默认尝试markdown格式
            return 'markdown'

    def load_markdown(self) -> str:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content

    def load_json(self) -> List[Dict[str, Any]]:
        """加载JSON格式的数据"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

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

    def process_json_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """处理JSON数据，转换为章节格式"""
        sections = []
        
        for item in data:
            # 提取章节信息
            item_id = item.get('id', 'unknown')
            text_content = item.get('text', '')
            metadata = item.get('metadata', {})
            
            # 从文本中提取标题（如果有markdown标题格式）
            lines = text_content.split('\n')
            title = f"Chapter {item_id}"  # 默认标题
            
            # 查找第一个标题行
            for line in lines:
                if line.startswith('#'):
                    title = re.sub(r'^#+\s*', '', line).strip()
                    break
            
            # 清理文本内容
            cleaned_text = self.clean_text(text_content)
            
            sections.append({
                "title": title,
                "content": cleaned_text,
                "metadata": metadata
            })
        
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
        """加载并分块数据，支持多种文件格式"""
        file_format = self.detect_file_format()
        
        if file_format == 'json':
            # 处理JSON格式数据
            json_data = self.load_json()
            sections = self.process_json_data(json_data)
        else:
            # 处理Markdown格式数据
            raw_text = self.load_markdown()
            cleaned_text = self.clean_text(raw_text)
            sections = self.split_by_headers(cleaned_text)
        
        all_chunks = []
        global_chunk_count = 0
        
        for section in sections:
            # 提取章节内容，支持不同的section格式
            content = section.get("content", "")
            title = section.get("title", "Unknown")
            
            chunks, chunk_count = self.chunk_text(content, title, global_chunk_count)
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
