# Knowledge Graph Builder

从非结构化文本数据构建知识图谱的原型系统，使用 LangChain + Ollama + Neo4j。

## 功能特性

- 从 Markdown 文件加载和分块文本数据
- 使用本地 Ollama (Mistral 7B) 进行实体和关系提取
- 将知识存储到 Neo4j 图数据库
- 支持批量处理和进度跟踪
- 提供图谱查询和导出功能
- 适配 RTX 3060 6G 显存

## 技术栈

- **Python 3.10+**
- **LangChain** - LLM 集成框架
- **Ollama** - 本地大语言模型服务
- **Neo4j** - 图数据库
- **Mistral 7B** - 本地 LLM 模型

## 项目结构

```
KG/
├── config.py                 # 配置管理
├── requirements.txt          # Python 依赖
├── .env.example             # 环境变量示例
├── data/
│   └── Apple_Environmental_Progress_Report_2024.md
├── src/
│   ├── __init__.py
│   ├── data_loader.py       # 数据加载和分块
│   ├── neo4j_manager.py     # Neo4j 数据库操作
│   ├── entity_extractor.py  # 实体关系提取
│   └── graph_builder.py     # 图谱构建流程
├── main.py                   # 主程序
└── README.md                 # 本文件
```

## 安装步骤

### 1. 安装 Ollama

下载并安装 Ollama: https://ollama.com/download

安装完成后，拉取 Mistral 7B 模型（推荐使用 4-bit 量化版本）：

```bash
ollama pull mistral:7b-instruct-v0.3-q4_0
```

验证模型是否可用：

```bash
ollama list
```

### 2. 安装 Neo4j

#### 方式 A：使用 Neo4j Desktop（推荐）

1. 下载 Neo4j Desktop: https://neo4j.com/download/
2. 安装并启动 Neo4j Desktop
3. 创建新项目并添加数据库
4. 记录连接信息（默认：bolt://localhost:7687）

#### 方式 B：使用 Docker

```bash
docker run -d \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your_password \
    neo4j:5.25.0
```

### 3. 安装 Python 依赖

创建虚拟环境（推荐）：

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 配置

1. 复制环境变量示例文件：

```bash
copy .env.example .env  # Windows
cp .env.example .env   # Linux/Mac
```

2. 编辑 `.env` 文件，设置你的配置：

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct-v0.3-q4_0

# Data Configuration
DATA_FILE=data/Apple_Environmental_Progress_Report_2024.md

# Processing Configuration
CHUNK_SIZE=2000
CHUNK_OVERLAP=200
MAX_RETRIES=3
RETRY_DELAY=2
```

## 使用方法

### 构建知识图谱

```bash
python main.py --build
```

这将：
1. 加载并分块 Markdown 文件
2. 使用 Ollama 提取实体和关系
3. 将结果存储到 Neo4j
4. 显示构建统计信息

### 查询实体信息

```bash
python main.py --query "Apple"
```

查询特定实体的关系信息。

### 显示图谱摘要

```bash
python main.py --summary
```

显示整个图谱的统计信息，包括实体和关系类型分布。

### 导出图谱

```bash
python main.py --export graph.json
```

将图谱导出为 JSON 文件。

### 不清除数据库重新构建

```bash
python main.py --build --no-clear
```

在现有数据库基础上添加新数据。

### 使用自定义配置文件

```bash
python main.py --build --config custom.env
```

## 实体类型

系统支持以下实体类型：

- **Organization**: 公司、机构、组织（如：Apple, suppliers）
- **Product**: 产品、设备、服务（如：MacBook Air, iPhone 15）
- **Material**: 材料、元素、物质（如：aluminum, cobalt）
- **Goal**: 目标、承诺、指标（如：Apple 2030, carbon neutrality）
- **Metric**: 测量值、统计数据（如：emissions, recycled percentage）
- **Initiative**: 计划、项目、活动（如：Power for Impact）
- **Location**: 地点、地区、国家（如：Nepal, Colombia）
- **Person**: 个人、角色（如：Lisa Jackson）
- **Technology**: 技术、方法、流程（如：renewable energy）
- **Program**: 结构化程序或框架（如：Supplier Clean Water Program）

## 关系类型

系统支持以下关系类型：

- **ACHIEVES**: Organization → Goal（组织实现目标）
- **USES**: Product → Material（产品使用材料）
- **REDUCES**: Initiative → Metric（计划减少指标）
- **CONTAINS**: Product → Material（产品包含材料）
- **IMPLEMENTS**: Organization → Initiative（组织实施计划）
- **LOCATED_IN**: Initiative → Location（计划位于某地）
- **PARTNERS_WITH**: Organization → Organization（组织合作）
- **PRODUCES**: Organization → Product（组织生产产品）
- **MEASURES**: Metric → Goal（指标衡量目标进展）
- **TARGETS**: Goal → Metric（目标针对特定指标）

## 性能优化建议

### 显存优化（RTX 3060 6G）

如果遇到显存不足问题，可以：

1. **使用更小的模型**：
   ```env
   OLLAMA_MODEL=qwen2.5:3b-instruct-q4_0
   ```

2. **减小上下文窗口**：
   ```env
   # 在 config.py 中调整
   num_ctx=2048  # 默认 4096
   ```

3. **减小分块大小**：
   ```env
   CHUNK_SIZE=1000  # 默认 2000
   ```

4. **使用更激进的量化**：
   ```bash
   ollama pull mistral:7b-instruct-v0.3-q3_k_m
   ```

### 处理速度优化

1. **增加批量大小**：在 `graph_builder.py` 中调整 `batch_size`
2. **减少重试次数**：设置 `MAX_RETRIES=1`
3. **并行处理**：可以修改代码支持多线程处理

## 常见问题

### 1. Ollama 连接失败

确保 Ollama 服务正在运行：

```bash
ollama serve
```

检查服务是否正常：

```bash
curl http://localhost:11434/api/tags
```

### 2. Neo4j 连接失败

确保 Neo4j 正在运行，检查端口是否正确：

```bash
# Windows
netstat -an | findstr 7687

# Linux/Mac
netstat -an | grep 7687
```

### 3. 显存不足

按照上面的"显存优化"建议调整配置。

### 4. 提取结果质量不高

可以尝试：

1. 调整 Prompt 模板（在 `entity_extractor.py` 中）
2. 使用更大的模型（如果显存允许）
3. 调整 temperature 参数（降低会更确定，升高会更随机）
4. 增加上下文窗口，提供更多上下文信息

### 5. JSON 解析错误

这是 LLM 输出格式问题，系统会自动重试。如果频繁出现：

1. 检查模型是否正确加载
2. 尝试使用不同的模型版本
3. 调整 Prompt 使其更明确

## 扩展开发

### 添加新的实体类型

在 `entity_extractor.py` 中的 `ENTITY_TYPES` 列表添加新类型：

```python
ENTITY_TYPES = [
    "Organization", "Product", "Material", "Goal", "Metric",
    "Initiative", "Location", "Person", "Technology", "Program",
    "YourNewType"  # 添加新类型
]
```

### 添加新的关系类型

在 `entity_extractor.py` 中的 `RELATIONSHIP_TYPES` 列表添加新类型：

```python
RELATIONSHIP_TYPES = [
    "ACHIEVES", "USES", "REDUCES", "CONTAINS", "IMPLEMENTS",
    "LOCATED_IN", "PARTNERS_WITH", "PRODUCES", "MEASURES", "TARGETS",
    "YourNewRelation"  # 添加新关系
]
```

### 自定义 Prompt

修改 `entity_extractor.py` 中的 `create_extraction_prompt()` 方法来自定义提取逻辑。

## 学习资源

- **LangChain 文档**: https://python.langchain.com/docs/get_started/introduction
- **Ollama 文档**: https://ollama.com/docs
- **Neo4j 文档**: https://neo4j.com/docs/getting-started/
- **Cypher 查询语言**: https://neo4j.com/docs/cypher-manual/

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue。
