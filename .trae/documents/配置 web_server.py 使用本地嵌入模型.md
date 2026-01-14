## 修改计划

### 1. 修改 [config.py](file:///d:\workspace\pytorch\KG\config.py)
- 添加 `EmbeddingConfig` 类，包含：
  - `model_name`: 默认模型名称（如 'all-MiniLM-L6-v2'）
  - `local_model_path`: 本地模型路径（从 .env 的 LOCAL_EMBEDDING_MODEL_PATH 读取）
  - `cache_embeddings`: 是否缓存嵌入
- 在 `Config` 类中添加 `embedding` 配置项
- 在 `from_env()` 方法中读取 `LOCAL_EMBEDDING_MODEL_PATH` 环境变量

### 2. 修改 [web_server.py](file:///d:\workspace\pytorch\KG\web_server.py)
- 导入 `Config` 类
- 在 `initialize_components()` 函数中：
  - 从 .env 加载配置
  - 获取嵌入模型配置（优先使用本地路径）
  - 将配置传递给 `EmbeddingManager`

### 3. 修改 [EmbeddingManager](file:///d:\workspace\pytorch\KG\src\embedding_manager.py)
- 修改 `__init__` 方法，支持接收完整的配置对象
- 优化本地路径检测逻辑，如果本地路径不存在则回退到 Hugging Face Hub 下载

### 预期效果
- web_server.py 启动时会自动读取 .env 中的 LOCAL_EMBEDDING_MODEL_PATH
- 如果本地路径存在，直接使用本地模型，无需下载
- 如果本地路径不存在，自动从 Hugging Face Hub 下载默认模型
- 避免每次启动都重新下载模型