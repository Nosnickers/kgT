## 修复 CSV 文件路径问题（不影响 main.py）

**问题**：`qa_cli.py` 自动从 JSON 文件名推导 CSV 文件名（`Dulce.json` → `Dulce.csv`），但 `main.py` 生成的 CSV 文件名是时间戳格式（如 `kg_build_20260111_145824.csv`）

**解决方案**：

1. 在 `qa_cli.py` 的 `build_parser` 中添加 `--csv-file` 参数，允许用户显式指定 CSV 文件路径
2. 修改 `build_index` 函数，优先使用 `--csv-file` 参数，如果没有提供则回退到自动推导的逻辑
3. 运行 `python qa_cli.py build-index --config .env --csv-file data/kg_build_20260111_145824.csv` 验证修复

这样既不影响 `main.py` 的正常工作，又能让 `qa_cli.py` 灵活地指定 CSV 文件路径。
