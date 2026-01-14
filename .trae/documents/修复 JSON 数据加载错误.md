## 修复 JSON 数据加载错误

**问题**：`AttributeError: 'str' object has no attribute 'get'`
**原因**：`chief_complaint_1.json` 是单个对象格式，而代码期望数组格式

**修复步骤**：

1. **修改 `data_loader.py` 的 `load_json()` 方法**
   - 检测返回的数据类型（列表或字典）
   - 如果是字典，将其转换为列表格式以便统一处理

2. **修改 `process_json_data()` 方法**
   - 添加对字典类型数据的处理逻辑
   - 确保无论输入是列表还是单个对象，都能正确处理

3. **测试修复**
   - 重新运行 `python main.py --build --config .env`
   - 验证能够成功加载 `chief_complaint_1.json` 数据
   - 确保主诉提取功能正常工作