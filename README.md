# 知识图谱问答系统
基于本地大语言模型的知识图谱问答系统，支持从非结构化数据构建知识图谱，并通过向量检索和 LLM 生成智能回答。

[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/Nosnickers/kgT)
## 系统架构
知识图谱实体多轮提取 + Naive RAG

### 构建阶段
使用 Ollama 本地 deepseek-r1:8b 大模型，从非结构化数据提取知识图谱三元组结构，存入 Neo4j 图数据库；再使用知识图谱和原文，生成文本描述后，生成嵌入向量并入库 ChromaDB。

### 推理阶段
使用本地模型 deepseek-r1:8b，在用户输入提问时，先从向量数据库中检索相关 topK 实体、关系，再连同用户输入的文字，一同喂给本地 LLM，生成回答。

### Web 部署
使用 Flask + JavaScript 方式部署推理服务，提供页面对话式交互。

## 功能特性

- 知识图谱构建：从非结构化文本自动提取实体和关系
- 向量检索：基于语义相似度检索相关实体和关系
- 智能问答：结合检索结果和用户问题生成准确答案
- Web 界面：现代化响应式 UI，支持实时问答
- 数据源查看：弹框展示原始数据源内容
- 对话历史：支持多轮对话和上下文记忆
- 系统监控：实时显示系统状态和统计信息
- **双模型支持**：同时支持本地 Ollama 模型和在线 LLM API
- **深度思考模式**：支持 LLM 深度推理，提升复杂实体关系提取质量
- **实体链接**：增量构建时自动关联现有实体，避免重复创建
- **LLM详细日志**：完整记录实体提取过程，便于调试和分析
- **灵活配置**：支持 Pydantic 配置模型，环境变量和命令行参数灵活配置
- **本地嵌入模型**：支持配置本地模型路径，避免重复下载

## 技术栈

### 后端
- **Python 3.10+**
- **Flask** - Web 框架
- **LangChain** - LLM 集成框架
- **Ollama** - 本地大语言模型服务（支持 deepseek-r1:8b 等）
- **在线LLM** - 支持 OpenAI 兼容 API（阿里云通义千问等）
- **Neo4j** - 图数据库
- **ChromaDB** - 向量数据库
- **all-MiniLM-L6-v2** - 嵌入模型（支持本地模型路径配置）

### 前端
- **原生 HTML + CSS + JavaScript**
- **Tailwind CSS** - 样式框架（通过 CDN）
- **Fetch API** - 异步数据交互

## 项目结构

```
KG/
├── config.py                 # 配置管理（支持Pydantic配置模型）
├── requirements.txt           # Python 依赖
├── .env.example              # 环境变量示例
├── data/                     # 数据目录
│   ├── Apple_Environmental_Progress_Report_2024.md  # 默认数据文件
│   ├── oralRecords.md        # 口腔病历数据
│   └── oralChunks.md         # 口腔病历分块数据
├── chroma_db/                # ChromaDB 向量数据库
├── src/
│   ├── __init__.py
│   ├── data_loader.py        # 数据加载和分块
│   ├── neo4j_manager.py      # Neo4j 数据库操作
│   ├── entity_extractor.py   # 实体关系提取
│   ├── graph_builder.py      # 图谱构建流程
│   ├── text_generator.py     # 文本描述生成
│   ├── embedding_manager.py  # 嵌入向量管理
│   ├── vector_store.py       # 向量存储管理
│   ├── retriever.py          # 向量检索器
│   ├── qa_engine.py          # 问答引擎
│   └── llm_client.py         # LLM客户端（支持Ollama和在线API）
├── templates/
│   └── index.html            # Web 前端页面
├── test/                     # 测试脚本目录
├── main.py                   # 主程序（构建知识图谱）
├── qa_cli.py                 # 命令行问答工具
├── web_server.py             # Flask Web 服务器
├── QUICKSTART.md             # 快速开始指南
├── LOCAL_EMBEDDING_GUIDE.md  # 本地嵌入模型配置指南
├── LLM_LOGGING_IMPLEMENTATION.md  # LLM日志实现文档
├── FRONTEND.md               # Web 前端文档
├── start_web.bat             # Windows 启动脚本
└── README.md                 # 本文件
```

## 安装步骤

### 1. 安装 Ollama

下载并安装 Ollama: https://ollama.com/download

安装完成后，拉取 deepseek-r1:8b 模型：

```bash
ollama pull deepseek-r1:8b
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

2. 从`.env.example`复制自己的 `.env` 文件，设置你的配置：

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_TEMPERATURE=0.1
OLLAMA_NUM_CTX=4096
OLLAMA_DEEP_THOUGHT_MODE=false

# Online LLM Configuration (OpenAI-compatible APIs)
ENABLE_ONLINE_LLM=false
ONLINE_LLM_API_KEY=your_api_key
ONLINE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ONLINE_LLM_MODEL=qwen3-coder-plus

# Data Configuration
DATA_FILE=data/Apple_Environmental_Progress_Report_2024.md
CHUNK_SIZE=2000
CHUNK_OVERLAP=200

# Embedding Model Configuration
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
LOCAL_EMBEDDING_MODEL_PATH=/path/to/local/embedding/model
CACHE_EMBEDDINGS=true

# Processing Configuration
MAX_RETRIES=3
RETRY_DELAY=2

# Entity Linking Configuration
ENABLE_ENTITY_LINKING=false
ENTITY_TYPES_TO_LINK=Patient,PatientId

# LLM Logging Configuration
ENABLE_LLM_LOGGING=false
```

## 高级配置

### LLM模型选择

系统支持两种 LLM 模式：

#### 1. 本地 Ollama 模型

```env
OLLAMA_MODEL=deepseek-r1:8b
OLLAMA_BASE_URL=http://localhost:11434
```

支持的模型：
- deepseek-r1:8b
- mistral:7b-instruct-v0.3-q4_0
- qwen2.5:3b-instruct-q4_0

#### 2. 在线 LLM (OpenAI 兼容 API)

```env
ENABLE_ONLINE_LLM=true
ONLINE_LLM_API_KEY=your_api_key
ONLINE_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ONLINE_LLM_MODEL=qwen3-coder-plus
```

支持的服务：
- 阿里云通义千问 (qwen3-coder-plus, qwen-turbo 等)
- OpenAI API
- 其他 OpenAI 兼容 API

### 深度思考模式

启用深度思考模式可以让 LLM 进行更深入的推理，适用于复杂的实体关系提取：

```env
OLLAMA_DEEP_THOUGHT_MODE=true
```

### 嵌入模型配置

系统支持使用本地嵌入模型，避免每次从 Hugging Face Hub 下载：

```env
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
LOCAL_EMBEDDING_MODEL_PATH=/path/to/local/embedding/model
CACHE_EMBEDDINGS=true
```

详见 [LOCAL_EMBEDDING_GUIDE.md](LOCAL_EMBEDDING_GUIDE.md)

### 实体链接配置

实体链接功能允许系统在提取新实体时，先查询图数据库中现有的实体，避免重复创建并建立正确的关系。

**配置方式**（优先级：命令行参数 > 环境变量 > 默认值）：

1. **环境变量配置**（`.env`文件中添加）：
   ```env
   # 实体链接配置
   ENABLE_ENTITY_LINKING=true
   ENTITY_TYPES_TO_LINK=Patient,PatientId,Diagnosis
   
   # LLM日志记录配置
   ENABLE_LLM_LOGGING=false
   ```

2. **命令行参数配置**：
   ```bash
   # 启用实体链接
   python main.py --build --enable-entity-linking --entity-types-to-link "Patient,PatientId"
   
   # 启用LLM详细日志记录
   python main.py --build --enable-llm-logging
   
   # 同时启用两个功能
   python main.py --build --enable-entity-linking --enable-llm-logging
   ```

### 实体链接使用场景

#### 场景1：增量构建患者病历
**场景描述**：在已有患者基本信息的基础上，增量添加新的诊断、症状等信息。

**操作步骤**：
1. 首次构建：导入患者基本信息（是否--no-clear清空数据库可选）
   ```bash
   python main.py --build --config .env --no-clear
   ```

2. 后续增量构建：启用实体链接，添加新信息
   ```bash
   python main.py --build --config .env --no-clear --enable-entity-linking
   ```

**效果**：新提取的诊断"黄染牙"会自动关联到现有患者"林悦"，而不是创建新患者。

#### 场景2：多类型实体链接
**场景描述**：需要链接多种类型的实体（患者、诊断、症状等）。

**操作步骤**：
```bash
python main.py --build --config .env --no-clear \
    --enable-entity-linking \
    --entity-types-to-link "Patient,Diagnosis,Symptom"
```

**效果**：系统会查询图数据库中现有的患者、诊断和症状实体，新提取的实体会自动与现有实体建立关系。

#### 场景3：仅链接患者ID
**场景描述**：只链接患者ID，其他实体正常创建，最小化数据库查询。

**操作步骤**：
```bash
python main.py --build --config .env --no-clear \
    --enable-entity-linking \
    --entity-types-to-link "PatientId"
```

**效果**：仅查询患者ID，其他实体（诊断、症状等）正常创建，适合性能敏感场景。

### LLM详细日志记录

LLM详细日志记录功能会创建独立的日志文件，记录实体提取的完整过程，包括：
- 系统提示词和用户提示词
- LLM原始响应（含深度思考过程）
- 清理后的JSON响应
- 解析后的实体和关系数据

**启用方式**：
```bash
# 命令行启用
python main.py --build --enable-llm-logging

# 环境变量启用（.env文件中设置ENABLE_LLM_LOGGING=true）
```

**日志文件位置**：`logs/chunk_analysis_YYYYMMDD_HHMMSS.log`

## 使用方法

### 构建知识图谱

使用 `main.py` 构建知识图谱：

```bash
# 基本构建
python main.py --build

# 指定配置文件
python main.py --build --config .env

# 启用详细LLM日志
python main.py --build --enable-llm-logging

# 增量构建（不清空数据库）
python main.py --build --no-clear

# 指定数据文件
python main.py --build --data-file data/oralRecords.md
```

这将：
1. 加载并分块数据文件
2. 使用 Ollama（或其他配置的 LLM）提取实体和关系
3. 将结果存储到 Neo4j
4. 显示构建统计信息

### 查询单个实体

```bash
python main.py --query "Alex Mercer"
```

### 查看知识图谱摘要

```bash
python main.py --summary
```

### 导出知识图谱

```bash
python main.py --export output.json
```

### 构建向量索引

使用 `qa_cli.py` 构建向量索引：

```bash
python qa_cli.py build-index
```

这将：
1. 从 Neo4j 读取实体和关系
2. 生成文本描述
3. 生成嵌入向量
4. 存储到 ChromaDB

### 命令行问答

使用 `qa_cli.py` 进行问答：

```bash
# 单次问答
python qa_cli.py query "Who is Alex Mercer?"

# 交互式问答
python qa_cli.py interactive
```

### Web 界面问答

启动 Web 服务器：

**Windows:**

```bash
start_web.bat
```

**Linux/Mac:**

```bash
source venv/bin/activate
python web_server.py
```

服务将在 `http://localhost:5000` 启动。

在浏览器中打开 `http://localhost:5000` 即可使用问答界面。

### Web 界面功能

- **提问**：输入问题并提交查询
- **答案展示**：显示 LLM 生成的答案
- **来源信息**：显示检索到的相关实体和关系
- **数据源查看**：点击"查看数据源"按钮查看原始数据
- **系统统计**：显示实体和关系总数
- **对话历史**：支持多轮对话（可隐藏）

## API 接口

### 1. 健康检查

```
GET /api/health
```

响应：

```json
{
  "status": "ok",
  "components": {
    "embedding_manager": true,
    "vector_store": true,
    "retriever": true,
    "qa_engine": true
  }
}
```

### 2. 获取统计信息

```
GET /api/stats
```

响应：

```json
{
  "status": "success",
  "entity_count": 26,
  "relationship_count": 16
}
```

### 3. 问答查询

```
POST /api/query
Content-Type: application/json

{
  "query": "Who is Alex Mercer?",
  "retrieval_mode": "hybrid",
  "top_k": 5,
  "min_similarity": 0.0,
  "entity_types": ["Character"],
  "relationship_types": [],
  "use_conversation": false
}
```

响应：

```json
{
  "status": "success",
  "data": {
    "query": "Who is Alex Mercer?",
    "answer": "Alex is a character...",
    "sources": [
      {
        "type": "entity",
        "name": "Alex Mercer",
        "entity_type": "Character",
        "text_description": "Alex Mercer is a Character...",
        "similarity": 0.95
      }
    ],
    "retrieval_mode": "hybrid",
    "retrieval_count": 3
  }
}
```

### 4. 清空对话历史

```
POST /api/clear-conversation
```

### 5. 获取对话历史

```
GET /api/conversation-history
```

### 6. 查看数据源

```
GET /api/data-source
```

响应：

```json
{
  "status": "success",
  "data": [
    {
      "id": "1",
      "text": "# Operation: Dulce\n\n## Chapter 1\n\n..."
    }
  ]
}
```

## 检索模式

系统支持以下检索模式：

- **hybrid**：混合检索（实体+关系）
- **entity**：仅检索实体
- **relationship**：仅检索关系
- **contextual**：上下文增强检索

## 实体类型

系统支持以下实体类型：

- **Character**：角色、人物
- **Organization**：公司、机构、组织
- **Location**：地点、地区
- **Technology**：技术、设备
- **Concept**：概念、想法
- **Object**：物体、物品
- **Event**：事件、活动

## 关系类型

系统支持以下关系类型：

- **WORKS_FOR**：工作于
- **LOCATED_AT**：位于
- **USES**：使用
- **INTERACTS_WITH**：与...互动
- **PART_OF**：属于
- **INVOLVED_IN**：参与
- **RELATED_TO**：相关
- **LEADS**：领导
- **OWNS**：拥有
- **PARTICIPATES_IN**：参与

## 性能优化建议

### 显存优化（RTX 3060 6G）

如果遇到显存不足问题，可以：

1. **使用更小的模型**：
   ```env
   OLLAMA_MODEL=qwen2.5:3b-instruct-q4_0
   ```

2. **减小上下文窗口**：
   ```env
   num_ctx=2048  # 默认 4096
   ```

3. **减小分块大小**：
   ```env
   CHUNK_SIZE=1000  # 默认 2000
   ```

4. **使用更激进的量化**：
   ```bash
   ollama pull deepseek-r1:8b-q4_k_m
   ```

### 处理速度优化

1. **增加批量大小**：在 `graph_builder.py` 中调整 `batch_size`
2. **减少重试次数**：设置 `MAX_RETRIES=1`
3. **并行处理**：可以修改代码支持多线程处理

## 故障排除

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
    "Character", "Organization", "Location", "Technology",
    "Concept", "Object", "Event",
    "YourNewType"  # 添加新类型
]
```

### 添加新的关系类型

在 `entity_extractor.py` 中的 `RELATIONSHIP_TYPES` 列表添加新类型：

```python
RELATIONSHIP_TYPES = [
    "WORKS_FOR", "LOCATED_AT", "USES", "INTERACTS_WITH",
    "PART_OF", "INVOLVED_IN", "RELATED_TO",
    "LEADS", "OWNS", "PARTICIPATES_IN",
    "YourNewRelation"  # 添加新关系
]
```

### 自定义 Prompt

修改 `entity_extractor.py` 中的 `create_extraction_prompt()` 方法来自定义提取逻辑。

### 添加新的 API 端点

在 `web_server.py` 中添加新的路由：

```python
@app.route('/api/custom', methods=['GET'])
def custom_endpoint():
    return jsonify({'status': 'success', 'data': 'custom data'})
```

## 学习资源

- **LangChain 文档**: https://python.langchain.com/docs/get_started/introduction
- **Ollama 文档**: https://ollama.com/docs
- **Neo4j 文档**: https://neo4j.com/docs/getting-started/
- **Cypher 查询语言**: https://neo4j.com/docs/cypher-manual/
- **Flask 文档**: https://flask.palletsprojects.com/
- **ChromaDB 文档**: https://docs.trychroma.com/

## 许可证

本项目仅供学习和研究使用。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请提交 Issue。
