# 本地嵌入模型配置指南

## 概述

本系统支持使用本地安装的嵌入模型，避免每次运行时都从 Hugging Face Hub 下载模型。这可以显著提高启动速度，特别是在网络环境不佳的情况下。

## 配置方法

### 1. 环境变量配置

在 `.env` 文件中设置 `LOCAL_EMBEDDING_MODEL_PATH` 变量：

```bash
# 嵌入模型配置
LOCAL_EMBEDDING_MODEL_PATH=C:/Users/YourName/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
```

### 2. 获取本地模型路径

#### 方法一：首次运行后自动获取

1. 首次运行系统时，模型会自动下载到 Hugging Face 缓存目录
2. 查看日志输出，找到模型下载的路径
3. 将该路径配置到 `.env` 文件中

#### 方法二：手动查找缓存目录

Hugging Face 缓存目录通常位于：

- **Windows**: `C:/Users/<YourUsername>/.cache/huggingface/hub/`
- **Linux/Mac**: `~/.cache/huggingface/hub/`

在缓存目录中查找模型文件夹，例如：
- `models--sentence-transformers--all-MiniLM-L6-v2`
- `models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2`
- `models--sentence-transformers--all-mpnet-base-v2`

### 3. 路径格式说明

- **Windows**: 使用正斜杠 `/` 或双反斜杠 `\\`
  ```bash
  LOCAL_EMBEDDING_MODEL_PATH=C:/Users/YourName/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
  ```
  
- **Linux/Mac**: 使用正斜杠 `/`
  ```bash
  LOCAL_EMBEDDING_MODEL_PATH=/home/yourname/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
  ```

## 支持的模型

| 模型名称 | 维度 | 语言 | 特点 |
|---------|------|------|------|
| all-MiniLM-L6-v2 | 384 | 英文 | 轻量级，速度快 |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | 多语言 | 支持100+语言 |
| all-mpnet-base-v2 | 768 | 英文 | 性能更好，速度较慢 |

## 使用方式

### 命令行工具

```bash
# 构建向量索引
python qa_cli.py build-index --config .env

# 交互式问答
python qa_cli.py interactive --config .env

# 单次问答
python qa_cli.py query "你的问题" --config .env
```

### Web 服务器

```bash
python web_server.py
```

Web 服务器会自动从配置文件读取本地模型路径。

### 测试配置

运行测试脚本验证配置是否正确：

```bash
python test_local_embedding.py
```

## 工作原理

1. **配置加载**: 系统从 `.env` 文件加载 `LOCAL_EMBEDDING_MODEL_PATH` 配置
2. **路径验证**: 检查本地路径是否存在
3. **模型加载**: 如果路径存在，从本地加载；否则从 Hugging Face Hub 下载
4. **日志输出**: 系统会记录使用的模型路径，方便调试

## 日志示例

### 使用本地模型
```
INFO - 使用本地嵌入模型路径: C:/Users/elege/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2
INFO - 正在加载嵌入模型: C:\Users\elege\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2
INFO - 嵌入模型加载成功，向量维度: 384
```

### 使用在线下载
```
WARNING - 本地模型路径不存在: /invalid/path，将使用模型: all-MiniLM-L6-v2
INFO - 从 Hugging Face Hub 下载模型: all-MiniLM-L6-v2
INFO - 嵌入模型加载成功，向量维度: 384
```

## 故障排除

### 问题 1: 找不到本地模型路径

**症状**: 日志显示 "本地模型路径不存在"

**解决方案**:
1. 检查路径是否正确
2. 确认路径使用正确的分隔符（Windows 用 `/` 或 `\\`）
3. 确认模型文件夹存在

### 问题 2: 模型加载失败

**症状**: 加载模型时出现错误

**解决方案**:
1. 确认模型文件完整
2. 检查是否有足够的磁盘空间
3. 尝试删除缓存重新下载

### 问题 3: 向量维度不匹配

**症状**: 重新构建索引后查询失败

**解决方案**:
1. 确保使用相同的模型
2. 清除旧的向量数据库：`python qa_cli.py build-index --clear-db`
3. 重新构建索引

## 性能对比

| 方式 | 首次加载 | 后续加载 | 网络依赖 |
|------|---------|---------|---------|
| 本地模型 | 快 | 快 | 无 |
| 在线下载 | 慢 | 慢 | 有 |

## 最佳实践

1. **首次运行**: 让系统自动下载模型到缓存目录
2. **配置本地路径**: 将缓存路径配置到 `.env` 文件
3. **定期更新**: 如需更新模型，删除缓存文件夹重新下载
4. **备份模型**: 将模型文件夹备份到其他位置
5. **团队共享**: 将模型文件夹共享给团队成员，避免重复下载

## 相关文件

- [`.env.example`](file:///d:/workspace/pytorch/KG/.env.example) - 环境变量配置示例
- [`config.py`](file:///d:/workspace/pytorch/KG/config.py) - 配置管理
- [`src/embedding_manager.py`](file:///d:/workspace/pytorch/KG/src/embedding_manager.py) - 嵌入管理器
- [`test_local_embedding.py`](file:///d:/workspace/pytorch/KG/test_local_embedding.py) - 测试脚本
