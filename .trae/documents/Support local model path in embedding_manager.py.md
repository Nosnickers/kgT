## 支持本地模型路径

**目标**：让 `embedding_manager.py` 支持使用本地模型路径，避免每次都从 Hugging Face 在线下载

**修改内容**：

1. **修改** **`embedding_manager.py`**：

   * 在 `_load_model` 方法中添加逻辑，检查模型名称是否为本地路径

   * 首次使用在线模式下载模型后，下次使用优先从本地缓存取`all-MiniLM-L6-v2 模型，本地没有再尝试在线模式`

   * 如果是本地路径（以 `/` 或 `\` 开头），直接加载本地模型

   * 否则从 Hugging Face Hub 下载

2. **更新** **`qa_cli.py`** **参数说明**：

   * 在 `--embedding-model` 参数的帮助文本中说明支持本地路径

   * 例如：`--embedding-model C:\Users\elege\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf`

**使用方式**：

* 在线模式（默认）

* 本地模式：`--embedding-model C:\path\to\local\model`

