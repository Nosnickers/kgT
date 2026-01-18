## 目标
设计模块化的 LLM 调用系统，统一处理线上（OpenAI 兼容 API）和线下（Ollama）模型，通过环境变量 `ENABLE_ONLINE_LLM` 切换，提供清晰、可维护的配置和调用接口。

## 整体架构
1. **新的 LLM 模块** (`src/llm_client.py`)：封装底层 LLM 调用，提供统一接口
2. **配置整合** (`config.py`)：统一管理 Ollama 和在线 LLM 配置
3. **现有组件改造** (`entity_extractor.py`, `qa_engine.py`)：使用新的 LLM 客户端
4. **调用方更新** (`main.py`, `qa_cli.py`, `web_server.py`)：适配新接口

## 详细步骤

### 1. 创建 LLM 客户端模块 (`src/llm_client.py`)
```python
"""
统一的 LLM 客户端，支持 Ollama 和 OpenAI 兼容 API
"""
import os
from typing import Optional, Dict, Any
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

class LLMConfig:
    """LLM 配置数据类"""
    def __init__(
        self,
        enable_online: bool = False,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "deepseek-r1:8b",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        timeout: int = 30,
        num_ctx: int = 4096,  # Ollama 特有
        deep_thought_mode: bool = False  # Ollama 特有
    ):
        self.enable_online = enable_online
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.deep_thought_mode = deep_thought_mode

class LLMClient:
    """统一的 LLM 客户端"""
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm: BaseChatModel = self._create_llm()
    
    def _create_llm(self) -> BaseChatModel:
        """创建底层 LLM 实例"""
        if self.config.enable_online:
            # OpenAI 兼容 API
            return ChatOpenAI(
                api_key=self.config.api_key or os.getenv("ONLINE_LLM_API_KEY"),
                base_url=self.config.base_url or os.getenv("ONLINE_LLM_BASE_URL"),
                model=self.config.model or os.getenv("ONLINE_LLM_MODEL"),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
        else:
            # Ollama 本地服务
            return ChatOllama(
                base_url=self.config.base_url or os.getenv("OLLAMA_BASE_URL"),
                model=self.config.model or os.getenv("OLLAMA_MODEL"),
                temperature=self.config.temperature,
                num_ctx=self.config.num_ctx
            )
    
    def invoke(self, prompt: str) -> str:
        """调用 LLM 并返回文本响应"""
        response = self.llm.invoke(prompt)
        return response.content

def create_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """工厂函数，创建 LLM 客户端"""
    if config is None:
        # 从环境变量创建默认配置
        config = LLMConfig(
            enable_online=os.getenv("ENABLE_ONLINE_LLM", "false").lower() == "true",
            api_key=os.getenv("ONLINE_LLM_API_KEY"),
            base_url=os.getenv("ONLINE_LLM_BASE_URL"),
            model=os.getenv("ONLINE_LLM_MODEL") or os.getenv("OLLAMA_MODEL", "deepseek-r1:8b"),
            temperature=float(os.getenv("ONLINE_LLM_TEMPERATURE") or os.getenv("OLLAMA_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("ONLINE_LLM_MAX_TOKENS", "4096")),
            timeout=int(os.getenv("ONLINE_LLM_TIMEOUT", "30")),
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "4096")),
            deep_thought_mode=os.getenv("OLLAMA_DEEP_THOUGHT_MODE", "false").lower() == "true"
        )
    return LLMClient(config)
```

### 2. 更新配置文件 (`config.py`)
- 保留现有的 `OllamaConfig`，添加 `OnlineLLMConfig`
- 在 `Config` 类中添加 `enable_online_llm: bool` 和 `online_llm: Optional[OnlineLLMConfig]` 字段
- 添加辅助方法 `create_llm_config()` 返回 `LLMConfig` 对象

### 3. 修改实体提取器 (`src/entity_extractor.py`)
- 修改 `__init__` 方法，添加 `llm_client` 参数（类型为 `LLMClient`）
- 为了向后兼容，保留原有参数，但内部使用 `LLMClient`
- 所有 LLM 调用通过 `llm_client.invoke()` 进行

### 4. 修改问答引擎 (`src/qa_engine.py`)
- 类似修改，添加 `llm_client` 参数
- 更新 `answer()` 方法使用新的客户端

### 5. 更新主程序 (`main.py`)
- 使用 `create_llm_client()` 创建 LLM 客户端
- 传递给 `EntityExtractor` 和 `GraphBuilder`

### 6. 更新命令行接口 (`qa_cli.py`)
- 添加在线 LLM 相关命令行参数
- 使用 `create_llm_client()` 创建客户端并传递给 `QAEngine`

### 7. 更新 Web 服务器 (`web_server.py`)
- 从配置创建 LLM 客户端
- 更新 `QAEngine` 初始化

### 8. 更新环境变量示例 (`.env.example`)
添加在线 LLM 配置：
```
ENABLE_ONLINE_LLM=false
ONLINE_LLM_API_KEY=
ONLINE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ONLINE_LLM_MODEL=qwen3-coder-plus
ONLINE_LLM_TEMPERATURE=0.1
ONLINE_LLM_MAX_TOKENS=4096
ONLINE_LLM_TIMEOUT=30
```

### 9. 更新依赖 (`requirements.txt`)
添加 `langchain-openai` 依赖

## 向后兼容性
- 默认 `ENABLE_ONLINE_LLM=false`，保持现有行为
- 所有现有参数和调用方式不变
- 新增的 `llm_client` 参数可选，优先使用旧参数创建客户端

## 优势
1. **模块化**：LLM 配置和调用逻辑集中管理
2. **可维护**：新增 LLM 提供商只需修改 `LLMClient._create_llm()`
3. **配置灵活**：支持环境变量、代码配置、命令行参数多种方式
4. **向后兼容**：现有代码无需修改