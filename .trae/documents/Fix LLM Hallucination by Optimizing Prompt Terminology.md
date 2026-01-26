## 修复LLM误认为文本是占位符的问题

### 🔍 问题分析
LLM在深度思考模式下，看到用户提示词中的"Text:"标签后，仍然误认为后面的真实文本是占位符"<text>"。

### 📋 解决方案

#### 修改用户提示词（第184-189行）
**位置**: `src/entity_extractor.py` 第184-189行

**修改前**:
```python
human_prompt = """Extract entities and relationships from the following text:

Text:
{text}

Return the extraction result in JSON format."""
```

**修改后**:
```python
human_prompt = """Extract entities and relationships from the following text:

ACTUAL TEXT CONTENT (this is real text, not a placeholder):
{text}

Return the extraction result in JSON format."""
```

### 🎯 修改原理
1. **明确标识**: 将"Text:"改为"ACTUAL TEXT CONTENT"，明确告诉LLM这是真实内容
2. **双重确认**: 添加"(this is real text, not a placeholder)"进一步强调
3. **避免混淆**: 避免使用可能引起歧义的简单标签

### ✅ 预期效果
LLM将能够：
1. 正确识别这是真实文本而非占位符
2. 基于实际文本内容提取实体和关系
3. 不再返回空结果