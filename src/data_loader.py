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

    def chunk_text(self, text: str, title: str = "") -> List[DataChunk]:
        chunks = []
        words = text.split()
        current_chunk = ""
        chunk_count = 0
        
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
        
        return chunks

    def load_and_chunk(self) -> List[DataChunk]:
        raw_text = self.load_markdown()
        cleaned_text = self.clean_text(raw_text)
        sections = self.split_by_headers(cleaned_text)
        
        all_chunks = []
        for section in sections:
            chunks = self.chunk_text(section["content"], section["title"])
            all_chunks.extend(chunks)
        
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
