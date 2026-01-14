## 添加命令行参数支持多种数据源

**目标**：通过命令行参数支持 `data/chief_complaint_1.json` 和 `data/oralRecords.md` 两种数据源

**实施步骤**：

1. **在** **`main.py`** **中添加** **`--data-file`** **参数**

   * 添加新的命令行参数 `--data-file`，允许用户指定数据文件路径

   * 当命令行指定了 `--data-file` 时，覆盖配置文件中的 `DATA_FILE` 设置

2. **修改配置加载逻辑**

   * 在 `main()` 函数中，检查是否提供了 `--data-file` 参数

   * 如果提供了，使用命令行指定的文件路径创建 `Config` 对象

   * 如果未提供，使用 `.env` 配置文件中的默认值

3. **使用示例**

   ```bash
   # 使用 JSON 数据源
   python main.py --build --config .env --data-file data/chief_complaint_1.json

   # 使用 Markdown 数据源
   python main.py --build --config .env --data-file data/oralRecords.md
   ```

**优势**：

* 灵活切换不同数据源，无需修改配置文件

* 支持同时测试多种数据格式

* 保持向后兼容（不指定 `--data-file` 时使用配置文件默认值）

