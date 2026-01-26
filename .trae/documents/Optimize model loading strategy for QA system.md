## 优化问答系统的嵌入向量复用策略

### 需求分析

**需求1**：明确指定使用原生余弦相似度（避免使用ONNX）
- 修改 `src/vector_store.py`，在初始化 ChromaDB 时添加 `hnsw_config` 配置

**需求2**：`interactive_mode` 和 `query_mode` 支持 `--embedding-model` 参数
- **已满足** ✅（代码中已经使用 `args.embedding_model`）

**需求3**：`interactive_mode` 和 `query_mode` 依赖 `build_index` 的向量库
- **已满足** ✅（使用相同的 `--vector-db` 参数读取向量库）

**新需求**：`interactive_mode` 和 `query_mode` 应该复用 `build_index` 生成的嵌入向量缓存
- **当前问题**：每次都重新生成嵌入向量，没有复用 `build_index` 生成的嵌入向量缓存

### 解决方案

1. **修改** `src/embedding_manager.py`：
   - 在 `embed_entities` 和 `embed_relationships` 方法中添加缓存检查逻辑
   - 如果缓存文件存在，则加载缓存并直接返回
   - 避免重复生成嵌入向量

2. **添加** `--use-embedding-cache` 参数：
   - 在 `interactive_parser` 和 `query_parser` 中添加该参数
   - 默认值为 `True`，表示使用缓存

3. **修改** `interactive_mode` 和 `query_mode`：
   - 使用 `args.use_embedding_cache` 参数
   - 如果为 `False`，则不加载缓存

### 修改内容

**文件1**：`src/embedding_manager.py`
- 添加 `load_cache_if_exists` 方法
- 修改 `embed_entities` 和 `embed_relationships` 方法

**文件2**：`qa_cli.py`
- 在 `interactive_parser` 中添加 `--use-embedding-cache` 参数
- 在 `query_parser` 中添加 `--use-embedding-cache` 参数
- 在 `interactive_mode` 和 `query_mode` 中使用该参数

**文件3**：`src/vector_store.py`
- 在初始化时添加 `hnsw_config` 配置

### 预期效果

- 首次运行 `build_index` 生成嵌入向量并保存缓存
- 后续运行 `interactive_mode` 或 `query_mode` 时，直接加载缓存的嵌入向量
- 大幅提升问答响应速度