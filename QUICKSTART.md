# 快速开始指南

## 🚀 5 分钟快速启动

### 前置条件检查

1. **Python 3.10+ 已安装**
   ```bash
   python --version
   ```

2. **Ollama 已安装并运行**
   ```bash
   ollama --version
   ollama serve  # 在新终端启动
   ```

3. **Neo4j 已安装并运行**
   - 使用 Neo4j Desktop 或 Docker
   - 确保服务在 `bolt://localhost:7687` 运行

### 步骤 0：创建虚拟环境（推荐）

**为什么需要虚拟环境？**
- 避免与系统其他 Python 包冲突
- 为项目创建独立的依赖环境
- 便于管理和卸载

**创建虚拟环境：**
```bash
python -m venv venv
```

**激活虚拟环境（Windows PowerShell）：**
```bash
.\venv\Scripts\Activate.ps1
```

**激活虚拟环境（Windows CMD）：**
```bash
venv\Scripts\activate.bat
```

**激活虚拟环境（Linux/Mac）：**
```bash
source venv/bin/activate
```

**验证虚拟环境已激活：**
- 命令行提示符前会出现 `(venv)` 标记
- `python --version` 会显示虚拟环境中的 Python 版本

**停用虚拟环境：**
```bash
deactivate
```

**重要提示：**
- 每次打开新终端都需要重新激活虚拟环境
- 激活后，所有 `python` 和 `pip` 命令都会使用虚拟环境中的版本
- 虚拟环境文件可以删除（`rm -rf venv`），不会影响系统

### 步骤 1：安装依赖

**确保虚拟环境已激活，然后运行：**
```bash
pip install -r requirements.txt
```

**如果安装失败，尝试使用国内镜像：**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 步骤 2：拉取模型

```bash
ollama pull mistral:7b-instruct-v0.3-q4_0
```

### 步骤 3：配置环境

```bash
copy .env.example .env  # Windows
```

编辑 `.env` 文件，设置：
- `NEO4J_PASSWORD` - 你的 Neo4j 密码
- 其他配置保持默认即可

### 步骤 4：验证安装

```bash
python test_setup.py
```

所有测试应该通过（除了可能跳过 Neo4j 和 Ollama 连接测试）。

### 步骤 5：构建知识图谱

```bash
python main.py --build
```

等待处理完成（可能需要几分钟）。

### 步骤 6：查看结果

```bash
python main.py --summary
```

查看图谱统计信息。

```bash
python main.py --query "Apple"
```

查询特定实体的关系。

### 步骤 7：构建向量索引（可选，用于智能问答）

**什么是向量索引？**
- 将知识图谱中的实体和关系转换为文本描述
- 使用嵌入模型将文本转换为向量
- 存储到向量数据库（ChromaDB）中
- 支持基于向量相似度的智能检索

**构建向量索引：**
```bash
python qa_cli.py build-index --config .env --csv-file data/kg_build_20260111_145824.csv
```

**参数说明：**
- `--config`: 配置文件路径（默认：.env）
- `--csv-file`: CSV 文件路径（包含原始 chunk 数据）
- `--output`: 文本描述输出文件（默认：oral_kg_index.json）
- `--embedding-model`: 嵌入模型名称或本地路径（默认：all-MiniLM-L6-v2）
- `--vector-db`: 向量数据库路径（默认：./chroma_db）
- `--no-cache`: 禁用嵌入缓存

**使用本地缓存的模型：**
首次运行时，模型会自动从 Hugging Face Hub 下载并缓存到本地：
- Windows: `C:\Users\<用户名>\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2`
- Linux/Mac: `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2`

后续运行会自动使用缓存的模型，无需重新下载。

如果需要使用其他本地模型路径：
```bash
python qa_cli.py build-index --embedding-model "C:\path\to\local\model"
```

**预期输出：**
```
2026-01-11 22:35:33,679 - INFO - 开始构建向量索引...
2026-01-11 22:35:35,963 - INFO - Connected to Neo4j at bolt://localhost:7687
2026-01-11 22:35:35,963 - INFO - 成功加载 23 个chunk数据
2026-01-11 22:35:35,969 - INFO - 从Neo4j获取到 28 个实体
2026-01-11 22:35:35,974 - INFO - 从Neo4j获取到 16 个关系
2026-01-11 22:35:35,974 - INFO - 成功生成文本描述并保存到: knowledge_graph_texts.json
2026-01-11 22:35:35,974 - INFO - 生成 28 个实体文本描述
2026-01-11 22:35:35,976 - INFO - 生成 16 个关系文本描述
2026-01-11 22:35:35,976 - INFO - 开始生成嵌入向量...
2026-01-11 22:35:35,985 - INFO - 正在加载嵌入模型: all-MiniLM-L6-v2
2026-01-11 22:35:35,985 - INFO - 从 Hugging Face Hub 下载模型: all-MiniLM-L6-v2
2026-01-11 22:35:35,986 - INFO - Use pytorch device_name: cpu
2026-01-11 22:35:35,988 - INFO - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
2026-01-11 22:35:46,590 - INFO - 嵌入模型加载成功，向量维度: 384
2026-01-11 22:35:46,590 - INFO - 为 28 个实体生成嵌入...
2026-01-11 22:35:46,590 - INFO - 为 28 个缺失的实体生成嵌入...
2026-01-11 22:35:46,655 - INFO - 为 16 个关系生成嵌入...
2026-01-11 22:35:46,655 - INFO - 为 16 个缺失的关系生成嵌入...
2026-01-11 22:35:46,691 - INFO - 开始初始化向量存储...
2026-01-11 22:35:46,825 - INFO - 向量集合初始化成功
2026-01-11 22:35:46,825 - INFO - 开始添加实体到向量存储...
2026-01-11 22:35:47,417 - INFO - 成功添加 26/28 个实体到向量存储
2026-01-11 22:35:47,417 - INFO - 开始添加关系到向量存储...
2026-01-11 22:35:47,777 - INFO - 成功添加 16/16 个关系到向量存储
2026-01-11 22:35:47,779 - INFO - 持久化向量数据...
2026-01-11 22:35:47,779 - INFO - 持久化向量数据到: chroma_db
2026-01-11 22:35:47,779 - INFO - 向量索引构建完成！
2026-01-11 22:35:47,780 - INFO -   - 实体总数: 26
2026-01-11 22:35:47,782 - INFO -   - 关系总数: 16
```

### 步骤 8：使用智能问答系统（需要先完成步骤 7）

**单次问答：**
```bash
python qa_cli.py query "Who is Alex Mercer?" --vector-db ./chroma_db
```

**交互式问答：**
```bash
python qa_cli.py interactive --vector-db ./chroma_db
```

**参数说明：**
- `--embedding-model`: 嵌入模型名称（默认：all-MiniLM-L6-v2）
- `--vector-db`: 向量数据库路径（默认：./chroma_db）
- `--llm-base-url`: LLM 基础 URL（默认：http://localhost:11434）
- `--llm-model`: LLM 模型名称（默认：deepseek-r1:8b）
- `--llm-temperature`: LLM 温度参数（默认：0.7）
- `--retrieval-mode`: 检索模式（entity/relationship/hybrid/contextual，默认：hybrid）
- `--top-k`: 返回的最相似结果数量（默认：5）
- `--entity-types`: 过滤的实体类型（逗号分隔）
- `--relationship-types`: 过滤的关系类型（逗号分隔）
- `--min-similarity`: 最小相似度阈值（默认：0.0）
- `--no-cache`: 禁用嵌入缓存

**预期输出：**
```
问题：Who is Alex Mercer?
答案：Alex Mercer 是一个角色，他是一名在Paranormal Military Squad中工作的特工，并且目前位于briefing room。

来源（5 个）：
  1. 实体: Alex Mercer (Character)
     相似度: 0.39
     描述: Alex Mercer is a Character. Agent in Paranormal Military Squad
  2. 实体: Alex (Character)
     相似度: 0.17
     描述: Alex is a Character.
  3. 关系: Alex Mercer LOCATED_AT briefing room
     相似度: 0.33
     描述: Alex Mercer is located at briefing room.
  4. 关系: Alex Mercer WORKS_FOR Paranormal Military Squad
     相似度: 0.31
     描述: Alex Mercer works for Paranormal Military Squad.
  5. 关系: Alex Mercer PART_OF Paranormal Military Squad
     相似度: 0.30
     描述: Alex Mercer is part of Paranormal Military Squad.
```

## 📊 预期输出示例

```
============================================================
Build Summary:
============================================================
Chunks processed: 712
Entities extracted: 150
Relationships extracted: 200
Entities created in Neo4j: 150
Relationships created in Neo4j: 200

Average entities per chunk: 0.21
Average relationships per chunk: 0.28

Entity Type Distribution:
  Organization: 45
  Product: 30
  Material: 25
  Goal: 15
  Metric: 20
  Initiative: 10
  Location: 5

Relationship Type Distribution:
  USES: 60
  ACHIEVES: 40
  REDUCES: 35
  CONTAINS: 30
  IMPLEMENTS: 20
  LOCATED_IN: 15
============================================================
```

## 🔧 常见问题解决

### 问题 1：pip install 失败

使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 2：Ollama 连接失败

确保 Ollama 服务正在运行：
```bash
ollama serve
```

检查端口：
```bash
curl http://localhost:11434/api/tags
```

### 问题 3：Neo4j 连接失败

检查 Neo4j 是否运行：
```bash
# Windows
netstat -an | findstr 7687
```

确保密码正确。

### 问题 4：显存不足

使用更小的模型：
```bash
ollama pull qwen2.5:3b-instruct-q4_0
```

修改 `.env`：
```env
OLLAMA_MODEL=qwen2.5:3b-instruct-q4_0
```

### 问题 5：处理速度慢

这是正常的，因为：
- 本地 LLM 推理速度有限
- 需要处理 712 个 chunks
- 每个 chunk 都需要 LLM 推理

可以：
- 减小 `CHUNK_SIZE`（会减少总 chunks 数）
- 使用更小的模型
- 只处理部分数据（修改 data_loader.py）

### 问题 6：向量索引构建失败

**错误：`chromadb.HnswConfig` 不存在**
- 这是 ChromaDB 版本兼容性问题
- 已在代码中修复，无需手动处理

**错误：CSV 文件不存在**
- 确保使用正确的 CSV 文件路径
- 检查 `data/` 目录下的 CSV 文件名
- 使用 `--csv-file` 参数指定正确路径

**错误：嵌入模型下载失败**
- 检查网络连接
- 首次运行会从 Hugging Face Hub 下载模型（约 30-50MB）
- 后续运行会使用缓存的模型

### 问题 7：问答检索不到结果

**可能原因：**
1. 向量索引未构建
   - 解决：先运行 `python qa_cli.py build-index`

2. 查询语言与知识图谱语言不匹配
   - 解决：使用英文查询（知识图谱文本为英文）
   - 或使用多语言嵌入模型（如 `paraphrase-multilingual-MiniLM-L12-v2`）

3. 相似度阈值过高
   - 解决：降低 `--min-similarity` 参数（默认为 0.0）

4. 嵌入模型未正确加载
   - 解决：检查日志中的模型加载信息
   - 确保模型缓存目录有写入权限

### 问题 8：LLM 生成答案不准确

**可能原因：**
1. 检索到的知识不足
   - 解决：增加 `--top-k` 参数（默认为 5）
   - 尝试不同的检索模式（`--retrieval-mode`）

2. LLM 温度参数过高
   - 解决：降低 `--llm-temperature` 参数（默认为 0.7）
   - 对于事实性问答，建议使用 0.1-0.3

3. 知识图谱信息不完整
   - 解决：重新构建知识图谱，添加更多实体和关系
   - 检查 Neo4j 中的数据完整性

## 🎯 下一步

1. **探索图谱**
   - 使用 Neo4j Browser 可视化图谱
   - 访问 http://localhost:7474

2. **构建向量索引并使用智能问答**
   - 运行 `python qa_cli.py build-index` 构建向量索引
   - 使用 `python qa_cli.py query` 或 `python qa_cli.py interactive` 进行问答
   - 支持多种检索模式和参数配置

3. **自定义提取**
   - 修改 `entity_extractor.py` 中的实体和关系类型
   - 调整 Prompt 模板

4. **处理其他数据**
   - 替换 `data/` 目录下的文件
   - 支持任何 Markdown 格式的文本

5. **性能优化**
   - 调整批处理大小
   - 使用 GPU 加速（如果支持）
   - 实现并行处理

6. **向量检索优化**
   - 尝试不同的嵌入模型（如多语言模型）
   - 调整相似度阈值和 top-k 参数
   - 使用不同的检索模式（entity/relationship/hybrid/contextual）

## 📚 学习资源

- 查看 [README.md](README.md) 了解详细文档
- 查看 [config.py](config.py) 了解配置选项
- 查看 [src/](src/) 目录了解实现细节

## 💡 提示

- 首次运行建议只处理少量数据测试
- 可以使用 `--no-clear` 选项增量添加数据
- 定期导出图谱备份：`python main.py --export backup.json`
- 使用 `tqdm` 显示进度条，方便监控处理进度

## 🆘 需要帮助？

1. 查看 [README.md](README.md) 的常见问题部分
2. 检查错误日志
3. 提交 Issue 到项目仓库

祝你使用愉快！🎉
