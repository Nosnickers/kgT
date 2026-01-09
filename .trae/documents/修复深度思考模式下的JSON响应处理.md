### 问题分析
从日志文件中可以看到，当启用深度思考模式时，模型返回的响应包含以下格式：
```
{<think>
...思考过程...
</think>

Please provide the text you'd like me to extract entities and relationships from. Once I have it, I'll perform the extraction using the specified rules and entity types.}
```

当前的`clean_json_response`方法存在以下问题：
1. 虽然能移除`<think>`标签，但无法正确处理标签前后的无效内容
2. 会尝试从非JSON内容中提取JSON，导致解析失败
3. 缺少对无效响应的处理逻辑

### 修复方案
1. **改进`<think>`标签处理**：确保完全移除包含思考过程的`<think>`和`</think>`标签
2. **添加JSON有效性检查**：在提取JSON前，检查内容是否包含有效的JSON结构
3. **增强内容清理逻辑**：处理各种边界情况，如开头的`{`和结尾的`}`
4. **添加异常处理**：确保在遇到无效响应时能优雅处理

### 实现步骤
1. 修改`src/entity_extractor.py`文件中的`clean_json_response`方法
2. 添加正则表达式匹配，确保只提取有效的JSON内容
3. 测试修复后的方法，验证它能正确处理包含`<think>`标签的响应
4. 确保修复不会影响正常的JSON响应处理

### 预期效果
修复后，深度思考模式下的实体提取功能将能正确处理包含思考过程的响应，提高系统的鲁棒性和可靠性。