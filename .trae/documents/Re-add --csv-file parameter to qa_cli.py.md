## 重新添加 --csv-file 参数支持

**问题**：之前的修改没有正确保存到文件中，导致 `--csv-file` 参数缺失

**解决方案**：
1. 在 `build_parser` 中添加 `--csv-file` 参数（第273行后）
2. 修改 `build_index` 函数，支持显式指定 CSV 文件（第31-34行）
3. 运行命令验证修复

**修改内容**：
- 在 `build_parser` 中添加：`build_parser.add_argument('--csv-file', type=str, help='CSV文件路径（包含chunk数据）')`
- 在 `build_index` 函数中添加逻辑：优先使用 `args.csv_file`，如果没有则回退到自动推导