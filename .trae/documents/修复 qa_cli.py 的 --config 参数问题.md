# 修复 qa_cli.py 的 --config 参数问题

## 问题
`interactive` 和 `query` 子命令缺少 `--config` 参数，导致无法读取配置文件。

## 修复步骤

### 1. 修改 interactive_parser（第323行之后）
在 `interactive_parser.add_argument('--embedding-model', ...)` 之前添加：
```python
interactive_parser.add_argument('--config', type=str, default='.env', help='配置文件路径（默认：.env）')
```

### 2. 修改 interactive_mode() 函数（第138行之后）
在 `try:` 块开始后添加：
```python
from config import Config
config = Config.from_env(args.config)
```
并使用配置文件中的值覆盖命令行参数的默认值（如果配置文件中有的话）

### 3. 修改 query_parser（第337行之后）
检查 `query_parser` 是否也需要添加 `--config` 参数，如果需要则添加

### 4. 修改 query_mode() 函数（第220行之后）
同样添加 `Config.from_env()` 调用

## 预期结果
修复后，以下命令将正常工作：
- `python qa_cli.py interactive --config .env --vector-db chroma_db --retrieval-mode hybrid --top-k 5 --min-similarity 0.7`
- `python qa_cli.py query "问题" --config .env`