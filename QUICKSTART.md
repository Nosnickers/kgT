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

## 🎯 下一步

1. **探索图谱**
   - 使用 Neo4j Browser 可视化图谱
   - 访问 http://localhost:7474

2. **自定义提取**
   - 修改 `entity_extractor.py` 中的实体和关系类型
   - 调整 Prompt 模板

3. **处理其他数据**
   - 替换 `data/` 目录下的文件
   - 支持任何 Markdown 格式的文本

4. **性能优化**
   - 调整批处理大小
   - 使用 GPU 加速（如果支持）
   - 实现并行处理

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
