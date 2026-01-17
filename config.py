import os
import logging
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class Neo4jConfig(BaseModel):
    uri: str = Field(default="bolt://localhost:7687")
    username: str = Field(default="neo4j")
    password: str = Field(default="")


class OllamaConfig(BaseModel):
    base_url: str = Field(default="http://localhost:11434")
    model: str = Field(default="deepseek-r1:8b")
    temperature: float = Field(default=0.1)
    num_ctx: int = Field(default=4096)
    deep_thought_mode: bool = Field(default=False)  # 是否启用深度思考模式


class DataConfig(BaseModel):
    file_path: str = Field(default="data/Dulce.json")
    chunk_size: int = Field(default=2000)
    chunk_overlap: int = Field(default=200)


class EmbeddingConfig(BaseModel):
    model_name: str = Field(default="all-MiniLM-L6-v2")
    local_model_path: Optional[str] = Field(default=None)
    cache_embeddings: bool = Field(default=True)


class ProcessingConfig(BaseModel):
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=2)
    batch_process_size: int = Field(default=10)  # 每处理多少个chunk后写入数据库
    enable_entity_linking: bool = Field(default=False)  # 是否启用实体链接功能
    entity_types_to_link: Optional[List[str]] = Field(default=None)  # 要链接的实体类型列表
    enable_llm_logging: bool = Field(default=False)  # 是否启用LLM详细日志记录


class Config(BaseModel):
    neo4j: Neo4jConfig
    ollama: OllamaConfig
    data: DataConfig
    embedding: EmbeddingConfig
    processing: ProcessingConfig

    @classmethod
    def from_env(cls, env_file: Optional[str] = None, data_file_override: Optional[str] = None) -> "Config":
        load_dotenv(env_file)
        
        data_file_path = data_file_override if data_file_override else os.getenv("DATA_FILE", "data/Apple_Environmental_Progress_Report_2024.md")
        logging.debug(f"Config.from_env() called with data_file_override={data_file_override}, DATA_FILE env={os.getenv('DATA_FILE')}")
        logging.info(f"Data file path determined: {data_file_path}")
        
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
                num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "4096")),
                deep_thought_mode=os.getenv("OLLAMA_DEEP_THOUGHT_MODE", "false").lower() == "true"
            ),
            data=DataConfig(
                file_path=data_file_path,
                chunk_size=int(os.getenv("CHUNK_SIZE", "2000")),
                chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200"))
            ),
            embedding=EmbeddingConfig(
                model_name=os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"),
                local_model_path=os.getenv("LOCAL_EMBEDDING_MODEL_PATH"),
                cache_embeddings=os.getenv("CACHE_EMBEDDINGS", "true").lower() == "true"
            ),
            processing=ProcessingConfig(
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                retry_delay=int(os.getenv("RETRY_DELAY", "2")),
                batch_process_size=int(os.getenv("BATCH_PROCESS_SIZE", "10")),
                enable_entity_linking=os.getenv("ENABLE_ENTITY_LINKING", "false").lower() == "true",
                entity_types_to_link=[t.strip() for t in os.getenv("ENTITY_TYPES_TO_LINK", "").split(",") if t.strip()] if os.getenv("ENTITY_TYPES_TO_LINK", "").strip() else None,
                enable_llm_logging=os.getenv("ENABLE_LLM_LOGGING", "false").lower() == "true"
            )
        )

    def validate_config(self) -> bool:
        if not self.neo4j.password:
            raise ValueError("NEO4J_PASSWORD must be set in environment variables")
        
        if not os.path.exists(self.data.file_path):
            raise FileNotFoundError(f"Data file not found: {self.data.file_path}")
        
        return True


config = Config.from_env()
