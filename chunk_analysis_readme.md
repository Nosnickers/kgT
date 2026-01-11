# Chunk分析测试脚本使用说明

## 功能概述
创建了两个测试脚本用于分析chunk_id 22的LLM输入输出过程，帮助排查实体提取幻觉问题。

## 脚本说明

### 1. test_chunk_22_logging.py
主要分析脚本，功能包括：
- 读取CSV文件中的指定chunk内容
- 记录完整的LLM交互过程
- 详细记录提示词、响应、验证过程
- 生成结构化的分析日志

### 2. test_chunk_logging.py  
快速测试脚本，用于验证功能是否正常。

## 使用方法

### 基本用法
```bash
# 分析chunk_id 22（默认）
python test_chunk_22_logging.py

# 分析其他chunk_id
python test_chunk_22_logging.py --chunk-id 15

# 使用深度思考模式
python test_chunk_22_logging.py --chunk-id 22 --deep-thought

# 指定不同的CSV文件
python test_chunk_22_logging.py --csv-file your_file.csv --chunk-id 22
```

### 参数说明
- `--chunk-id`: 要分析的chunk ID（默认：22）
- `--csv-file`: CSV文件路径（默认：kg_build_20260110_182346.csv）
- `--config`: 配置文件路径（默认：.env）
- `--log-dir`: 日志输出目录（默认：logs/）
- `--deep-thought`: 启用深度思考模式

### 快速测试
```bash
# 运行功能测试
python test_chunk_logging.py
```

## 日志输出

脚本会在 `logs/` 目录下生成详细的日志文件，包含：

1. **系统提示词**: 完整的实体类型和关系类型定义
2. **用户提示词**: 发送给LLM的实际文本内容
3. **LLM原始响应**: 包含思考过程标签的完整响应
4. **清理后的JSON**: 提取的有效JSON内容
5. **验证过程**: 每个实体和关系的验证结果
6. **最终结果**: 提取到的实体和关系列表

## 分析内容

日志文件会详细记录：
- 原始文本内容与提取结果的对比
- LLM是否产生了幻觉（提取了不存在的实体）
- 提示词是否足够明确和具体
- 验证规则是否过滤了有效数据

## 排查建议

通过分析日志可以：
1. 检查LLM响应中是否包含原始文本中不存在的实体
2. 验证提示词是否需要调整以减少幻觉
3. 检查JSON解析和清理过程是否丢失有效信息
4. 分析验证规则是否过于严格

## 注意事项

- 确保Ollama服务正在运行
- 确保配置文件(.env)中的模型配置正确
- 日志文件可能较大，建议定期清理logs目录