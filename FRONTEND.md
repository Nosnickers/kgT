# 知识图谱问答系统 Web 前端

基于 Flask 和原生 JavaScript 构建的知识图谱问答系统 Web 界面。

## 功能特性

- 交互式问答界面
- 实时显示查询状态
- 检索结果可视化（实体、关系）
- 可配置的检索参数（检索模式、Top-K、相似度阈值等）
- 对话历史记录
- 系统状态监控
- 响应式设计

## 系统架构

```
浏览器 (前端)
    ↓ HTTP/JSON
Flask Web 服务器 (web_server.py)
    ↓
QAEngine (问答引擎)
    ↓
Retriever (检索器) + LLM (Ollama)
    ↓
VectorStore (ChromaDB)
```

## 安装步骤

### 1. 安装 Python 依赖

确保已激活虚拟环境，然后安装新增的依赖：

```bash
pip install flask flask-cors
```

或者重新安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 确保向量数据库已构建

如果还没有构建向量索引，请先运行：

```bash
python qa_cli.py build-index
```

### 3. 确保 Ollama 服务运行

确保 Ollama 服务正在运行：

```bash
ollama serve
```

检查模型是否可用：

```bash
ollama list
```

## 启动服务

### Windows

双击运行 `start_web.bat` 或在命令行中执行：

```bash
start_web.bat
```

### Linux/Mac

```bash
source venv/bin/activate
python web_server.py
```

服务将在 `http://localhost:5000` 启动。

## 访问界面

在浏览器中打开：`http://localhost:5000`

## 使用说明

### 基本问答

1. 在文本框中输入问题
2. 点击"提交"按钮或按 Enter 键
3. 系统将显示答案和相关来源信息

### 配置检索参数

在右侧"检索配置"面板中可以调整：

- **检索模式**：
  - `hybrid`：混合检索（实体+关系）
  - `entity`：仅检索实体
  - `relationship`：仅检索关系
  - `contextual`：上下文增强检索

- **返回数量 (Top-K)**：返回的最相似结果数量（1-20）

- **最小相似度**：过滤低相似度的结果（0.0-1.0）

- **实体类型过滤**：指定要检索的实体类型，用逗号分隔（例如：`Character, Organization`）

- **关系类型过滤**：指定要检索的关系类型，用逗号分隔（例如：`WORKS_FOR, PART_OF`）

### 对话历史

- 勾选"使用对话历史"可以让系统记住之前的对话内容
- 点击"清空历史"可以清除所有对话记录
- 对话历史显示在右侧面板中

### 系统统计

右侧面板显示当前系统的统计信息：
- 实体总数
- 关系总数

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
  "entity_count": 100,
  "relationship_count": 200
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
    "answer": "Alex Mercer is a character...",
    "sources": [
      {
        "type": "entity",
        "name": "Alex Mercer",
        "similarity": 0.95,
        "text_description": "..."
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

响应：
```json
{
  "status": "success",
  "message": "对话历史已清空"
}
```

### 5. 获取对话历史

```
GET /api/conversation-history
```

响应：
```json
{
  "status": "success",
  "data": [
    {
      "user": "Who is Alex Mercer?",
      "assistant": "Alex Mercer is a character..."
    }
  ]
}
```

## 配置说明

### 修改端口

在 `web_server.py` 中修改最后一行：

```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

将 `port=5000` 改为你想要的端口号。

### 修改 LLM 配置

在 `web_server.py` 中修改 `initialize_components()` 函数：

```python
qa_engine = QAEngine(
    retriever=retriever,
    llm_base_url='http://localhost:11434',
    llm_model='deepseek-r1:8b',
    llm_temperature=0.7
)
```

### 修改向量数据库路径

在 `web_server.py` 中修改：

```python
vector_store = VectorStore(persist_directory='./chroma_db')
```

## 故障排除

### 1. 服务启动失败

**问题**：启动时提示组件初始化失败

**解决方案**：
- 确保 Ollama 服务正在运行
- 确保向量数据库已构建
- 检查日志输出查看具体错误

### 2. 查询失败

**问题**：提交查询后返回错误

**解决方案**：
- 检查 Ollama 服务是否正常运行
- 确认模型已下载：`ollama list`
- 检查向量数据库是否存在数据

### 3. 前端无法连接

**问题**：浏览器无法访问 `http://localhost:5000`

**解决方案**：
- 确认 Web 服务器已启动
- 检查端口是否被占用
- 尝试使用 `0.0.0.0:5000` 而不是 `localhost:5000`

### 4. 依赖安装失败

**问题**：`pip install` 失败

**解决方案**：
- 升级 pip：`pip install --upgrade pip`
- 使用国内镜像源：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

## 性能优化

### 1. 启用嵌入缓存

默认已启用嵌入缓存，可以加快查询速度。

### 2. 调整 Top-K 值

较小的 Top-K 值（如 3-5）可以提高查询速度。

### 3. 使用更小的模型

如果 Ollama 模型较大，可以考虑使用更小的模型以提高响应速度。

## 安全建议

### 1. 生产环境部署

在生产环境中：
- 设置 `debug=False`
- 使用反向代理（如 Nginx）
- 添加身份验证
- 使用 HTTPS

### 2. 访问控制

如果需要限制访问，可以在 `web_server.py` 中添加：

```python
from flask import request

@app.before_request
def limit_remote_addr():
    if request.remote_addr != '127.0.0.1':
        abort(403)
```

## 扩展开发

### 添加新的 API 端点

在 `web_server.py` 中添加新的路由：

```python
@app.route('/api/custom', methods=['GET'])
def custom_endpoint():
    return jsonify({'status': 'success', 'data': 'custom data'})
```

### 修改前端样式

编辑 `templates/index.html` 中的 CSS 部分，或添加自定义样式文件。

### 添加新功能

1. 在 `web_server.py` 中实现后端逻辑
2. 在 `templates/index.html` 中添加前端界面
3. 在 JavaScript 中添加交互逻辑

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题，请提交 Issue。
