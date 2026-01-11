## 修复 ChunkLogger 缺少日志方法的问题

### 问题分析
- `DetailedEntityExtractor` 中的 `self.logger` 是 `ChunkLogger` 对象
- 代码试图调用 `self.logger.info()` 和 `self.logger.error()` 方法
- 但 `ChunkLogger` 类只定义了 `log_section()`, `log_prompt()`, `log_response()` 方法
- 没有标准的 `info()`, `error()`, `warning()` 等日志方法

### 解决方案
在 `ChunkLogger` 类中添加代理方法，委托给内部的 `self.logger`：

1. **添加标准日志方法**：
   - `info(msg)`: 委托给 `self.logger.info(msg)`
   - `error(msg)`: 委托给 `self.logger.error(msg)`
   - `warning(msg)`: 委托给 `self.logger.warning(msg)`
   - `debug(msg)`: 委托给 `self.logger.debug(msg)`

2. **保持现有功能**：
   - `log_section()`, `log_prompt()`, `log_response()` 方法保持不变
   - 这些方法仍然使用内部的 `self.logger`

### 修改位置
文件：`d:\workspace\pytorch\KG\test_chunk_22_logging.py`
在 `ChunkLogger` 类中添加代理方法（约第90行之后）