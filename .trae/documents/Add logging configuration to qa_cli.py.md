## 在 qa\_cli.py 中添加日志配置

**目标**：让 `qa_cli.py` 的执行过程在终端中可见，显示 INFO 级别的日志

**修改内容**：

在 `qa_cli.py` 的 `main()` 函数中，在 `parser = argparse.ArgumentParser(...)` 之前添加日志配置：

1. 添加 `configure_logging` 函数（参考 main.py）
2. 在 `main()` 函数开始处调用 `configure_logging()`
3. 配置：

   * 设置日志级别为 INFO

   * 添加控制台 handler（StreamHandler）

   * 设置日志格式

**修改位置**：

* 在 `main()` 函数第 262 行之前添加日志配置

**预期效果**：
执行命令时会看到：

```
2026-01-11 20:19:07 - INFO - 开始构建向量索引...
2026-01-11 20:19:07 - INFO - 为 28 个实体生成嵌入...
2026-01-11 20:19:07 - INFO - 为 16 个关系生成嵌入...
2026-01-11 20:19:07 - INFO - 向量索引构建完成！
```

在线模式：

python qa\_cli.py build-index --config .env --csv-file data/kg\_build\_20260111\_145824.csv

<br />

本地模式：

python qa\_cli.py build-index --config .env --csv-file data/kg\_build\_20260111\_145824.csv --embedding-model "C:\Users\elege.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2\snapshots\c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
