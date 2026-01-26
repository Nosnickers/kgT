## 完整的 KAG 流程
### 1. 知识图谱构建 ✅
- 已完成 ：使用 main.py --build --data-file data/oralRecords.md
- 结果 ：771 个实体，596 个关系（包括 134 个 CHIEF_COMPLAINT 关系）
### 2. 文本描述生成 ✅
- 文件 ： text_generator.py
- 功能 ：从 Neo4j 读取实体和关系，生成文本描述和上下文
### 3. 嵌入向量生成 ✅
- 文件 ： embedding_manager.py
- 功能 ：使用 all-MiniLM-L6-v2 模型生成嵌入向量
### 4. 向量存储 ✅
- 文件 ： vector_store.py
- 功能 ：使用 ChromaDB 存储向量和元数据
### 5. 向量检索 ✅
- 文件 ： retriever.py
- 功能 ：基于向量相似度检索实体和关系
### 6. 问答引擎 ✅
- 文件 ： qa_engine.py
- 功能 ：结合检索结果和 LLM 生成答案
### 7. 命令行接口 ✅
- 文件 ： qa_cli.py
- 功能 ：提供 build-index、query、interactive 命令
## 使用方法
### 构建向量索引
```
# 使用最新的 CSV 文件（从 oralRecords.
md 构建的）
python qa_cli.py build-index 
--config .env --csv-file 
kg_build_20260114_091444.csv
```
### 交互式问答
```
python qa_cli.py interactive 
--config .env --vector-db ./
chroma_db
```
### 单次问答
```
python qa_cli.py query "林某的主诉是什
么？" --config .env
```
## 系统架构
```
用户问题 → qa_cli.py
    ↓
Retriever (向量检索)
    ↓
VectorStore (ChromaDB)
    ↓
QAEngine (LLM 生成答案)
    ↓
用户答案
```
所有代码已经完整实现，可以直接使用！