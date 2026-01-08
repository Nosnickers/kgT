import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class Neo4jConfig(BaseModel):
    uri: str = Field(default="bolt://localhost:7687")
    username: str = Field(default="neo4j")
    password: str = Field(default="")


class OllamaConfig(BaseModel):
    base_url: str = Field(default="http://localhost:11434")
    model: str = Field(default="mistral:7b-instruct-v0.3-q4_0")
    temperature: float = Field(default=0.1)
    num_ctx: int = Field(default=4096)


class DataConfig(BaseModel):
    file_path: str = Field(default="data/Apple_Environmental_Progress_Report_2024.md")
    chunk_size: int = Field(default=2000)
    chunk_overlap: int = Field(default=200)


class ProcessingConfig(BaseModel):
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=2)
    batch_process_size: int = Field(default=10)  # 每处理多少个chunk后写入数据库


class Config(BaseModel):
    neo4j: Neo4jConfig
    ollama: OllamaConfig
    data: DataConfig
    processing: ProcessingConfig

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "Config":
        load_dotenv(env_file)
        
        return cls(
            neo4j=Neo4jConfig(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                username=os.getenv("NEO4J_USERNAME", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "")
            ),
            ollama=OllamaConfig(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "mistral:7b-instruct-v0.3-q4_0"),
                temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
                num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "4096"))
            ),
            data=DataConfig(
                file_path=os.getenv("DATA_FILE", "data/Apple_Environmental_Progress_Report_2024.md"),
                chunk_size=int(os.getenv("CHUNK_SIZE", "2000")),
                chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200"))
            ),
            processing=ProcessingConfig(
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                retry_delay=int(os.getenv("RETRY_DELAY", "2")),
                batch_process_size=int(os.getenv("BATCH_PROCESS_SIZE", "10"))
            )
        )

    def validate_config(self) -> bool:
        if not self.neo4j.password:
            raise ValueError("NEO4J_PASSWORD must be set in environment variables")
        
        if not os.path.exists(self.data.file_path):
            raise FileNotFoundError(f"Data file not found: {self.data.file_path}")
        
        return True


config = Config.from_env()
