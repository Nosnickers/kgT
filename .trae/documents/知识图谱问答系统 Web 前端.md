# 知识图谱问答系统 Web 前端实现计划

## 技术栈
- **后端**: Flask（轻量级 Web 框架）
- **前端**: 原生 HTML + CSS + JavaScript
- **样式**: Tailwind CSS（通过 CDN）
- **图标**: Heroicons SVG

## 实现步骤

### 1. 创建 Flask 后端服务
- 创建 `web_server.py` 作为 Web 服务器
- 实现 `/api/query` API 端点，集成现有的 QAEngine
- 支持配置参数：retrieval_mode、top_k、min_similarity、entity_types、relationship_types
- 返回 JSON 格式的问答结果

### 2. 创建前端页面
- 创建 `templates/index.html` 作为主页面
- 使用 Tailwind CSS 构建现代化 UI
- 包含以下组件：
  - 顶部导航栏（标题 + 状态指示）
  - 问题输入区域（文本框 + 提交按钮）
  - 配置面板（可折叠，包含检索参数设置）
  - 答案展示区域（Markdown 格式渲染）
  - 来源信息展示区域（实体和关系列表）

### 3. 实现交互逻辑
- JavaScript 处理表单提交
- 调用后端 API 获取答案
- 动态渲染答案和来源信息
- 显示加载状态和错误提示
- 支持对话历史记录

### 4. 添加依赖
- 在 `requirements.txt` 添加 `flask` 和 `flask-cors`

### 5. 创建启动脚本
- 创建 `start_web.bat` 用于启动 Web 服务

## 部署和构建说明

### 安装依赖
```bash
pip install flask flask-cors
```

### 启动服务
```bash
python web_server.py
```
服务将在 `http://localhost:5000` 启动

### 访问前端
在浏览器中打开 `http://localhost:5000` 即可使用问答界面

### 配置说明
- 确保 Ollama 服务运行（`http://localhost:11434`）
- 确保向量数据库已构建（运行 `python qa_cli.py build-index`）
- 可在 `web_server.py` 中修改端口和配置

## 文件结构
```
KG/
├── web_server.py          # Flask Web 服务器
├── templates/
│   └── index.html         # 前端页面
├── start_web.bat          # Windows 启动脚本
└── requirements.txt       # 更新依赖
```

## 核心功能
1. 交互式问答界面
2. 检索结果可视化（实体、关系）
3. 可配置的检索参数
4. 响应式设计
5. 对话历史记录