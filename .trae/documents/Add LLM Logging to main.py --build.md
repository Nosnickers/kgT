## 为main.py --build添加LLM详细日志记录功能

### 📋 需求分析
1. **保持原始功能不变** - 默认情况下不影响现有功能
2. **添加可选日志记录** - 通过参数控制是否启用
3. **类似test_chunk_22_logging.py** - 记录完整的LLM交互过程

### 🔧 实现方案

#### 1. 修改GraphBuilder类
**文件**: `src/graph_builder.py`

**修改内容**:
- 在`__init__`中添加可选的`logger`参数
- 添加`_extract_with_logging`方法（类似test_chunk_22_logging.py中的实现）
- 修改`_extract_with_retry`方法，根据是否有logger决定使用哪个提取方法

#### 2. 修改main.py
**文件**: `main.py`

**修改内容**:
- 添加`--enable-llm-logging`参数（默认False）
- 如果启用，创建`ChunkLogger`实例
- 将logger传递给GraphBuilder
- 日志文件名与现有日志保持一致

#### 3. 修改EntityExtractor
**文件**: `src/entity_extractor.py`

**修改内容**:
- 添加`extract_with_logging`方法（如果不存在）
- 确保方法能够记录完整的LLM交互过程

### 📝 具体修改步骤

#### 步骤1: 修改GraphBuilder的__init__方法
添加可选的logger参数：
```python
def __init__(
    self,
    data_loader: DataLoader,
    neo4j_manager: Neo4jManager,
    entity_extractor: EntityExtractor,
    max_retries: int = 3,
    retry_delay: int = 2,
    logger: Optional[Any] = None  # 新增：可选的日志记录器
):
```

#### 步骤2: 添加_extract_with_logging方法
在GraphBuilder中添加带日志记录的提取方法：
```python
def _extract_with_logging(self, chunk: DataChunk) -> ExtractionResult:
    """带详细日志记录的实体提取方法"""
    if self.logger:
        self.logger.log_section(f"处理Chunk {chunk.metadata.get('chunk_id')}")
        self.logger.log_section("文本内容", chunk.content)
    
    # 调用entity_extractor的extract方法（带日志）
    result = self.entity_extractor.extract(chunk.content)
    
    if self.logger:
        self.logger.log_section("提取结果", {
            "实体数量": len(result.entities),
            "关系数量": len(result.relationships)
        })
    
    return result
```

#### 步骤3: 修改_extract_with_retry方法
根据是否有logger决定使用哪个提取方法：
```python
def _extract_with_retry(self, chunk: DataChunk) -> ExtractionResult:
    # 如果有logger，使用带日志的提取方法
    if hasattr(self, 'logger') and self.logger:
        return self._extract_with_logging(chunk)
    
    # 否则使用原始的提取方法
    # ... 原有代码
```

#### 步骤4: 修改main.py
添加日志记录参数和配置：
```python
parser.add_argument(
    "--enable-llm-logging",
    action="store_true",
    help="启用LLM详细日志记录"
)

# 在build_graph函数中
if args.enable_llm_logging:
    from test_chunk_22_logging import ChunkLogger
    logger = ChunkLogger(log_dir="logs")
    graph_builder = GraphBuilder(
        data_loader=data_loader,
        neo4j_manager=neo4j_manager,
        entity_extractor=entity_extractor,
        max_retries=config.processing.max_retries,
        retry_delay=config.processing.retry_delay,
        logger=logger  # 传递logger
    )
```

### ✅ 预期效果
1. **默认行为不变** - 不添加`--enable-llm-logging`时，功能与原来完全一致
2. **启用日志记录** - 添加`--enable-llm-logging`后，记录完整的LLM交互过程
3. **日志文件** - 保存到`logs/`目录，文件名与主日志保持一致
4. **不影响性能** - 日志记录是可选的，不影响原始性能

### 🎯 使用方法
```bash
# 正常构建（不记录LLM日志）
python main.py --build --config .env

# 构建并记录LLM详细日志
python main.py --build --config .env --enable-llm-logging
```