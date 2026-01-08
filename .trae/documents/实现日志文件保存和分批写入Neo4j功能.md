# 实现日志文件保存和分批写入Neo4j功能

## 1. 日志文件保存功能

### 实现方式
- 使用Python的logging模块替代print()函数
- 配置双处理器：控制台输出 + 文件输出
- 日志格式包含时间、级别、消息
- 日志文件默认按执行时间自动命名（格式：kg_build_YYYYMMDD_HHMMSS.log）

### 修改点
1. **main.py**
   - 添加日志配置，支持按时间自动命名
   - 保留命令行参数`--log-file`允许用户自定义日志路径
   - 将print_banner和print_config的输出改为logging调用

2. **所有模块文件**
   - 将所有print()调用替换为logging调用
   - 根据消息重要性选择合适的日志级别（info, warning, error）

## 2. 分批写入Neo4j数据库功能

### 实现方式
- 实现渐进式写入：处理一定数量的chunk后写入数据库
- 引入可配置的batch_process_size参数，默认值为10
- 保持实体去重逻辑
- 定期清空内存缓存

### 修改点
1. **graph_builder.py**
   - 在build_graph方法中添加batch_process_size参数
   - 修改处理流程，实现每处理N个chunk后写入数据库
   - 添加中间写入逻辑，包含实体和关系的批量创建
   - 优化内存使用，定期清空缓存

2. **config.py**
   - 添加batch_process_size配置项，默认值10

## 3. 配置参数

### 新增参数
- **日志文件路径**：通过命令行参数`--log-file`指定，默认按时间自动命名
- **批次处理大小**：通过配置文件指定，默认值为10

### 命令行参数
```bash
# 使用默认日志文件名和默认批次大小(10)
python main.py --build

# 指定自定义日志文件名
python main.py --build --log-file=build.log
```

## 4. 技术要点

### 日志模块
- 使用logging.basicConfig配置
- 设置文件处理器的编码为UTF-8
- 设置日志级别为INFO
- 使用datetime模块生成日志文件名

### 分批写入机制
- 每处理batch_process_size个chunk后，执行一次数据库写入
- 写入后清空内存中的实体和关系缓存
- 保持全局实体去重，避免重复创建
- 使用现有的_batch_create_with_retry方法进行批量写入

## 5. 预期效果

- 所有输出同时保存到日志文件和控制台
- 日志文件默认按执行时间自动命名，便于区分不同次运行
- 内存使用更加合理，避免处理大量数据时的内存溢出
- 支持自定义日志文件名
- 批次处理大小可配置，默认10个chunk

## 6. 代码修改范围

- **main.py**：日志配置、命令行参数
- **config.py**：添加batch_process_size配置项
- **src/graph_builder.py**：分批写入逻辑、日志替换
- **src/neo4j_manager.py**：日志替换
- **src/entity_extractor.py**：日志替换
- **src/data_loader.py**：日志替换

## 7. 实现步骤

1. 配置日志模块，支持按时间自动命名
2. 替换所有print()调用为logging调用
3. 在配置文件中添加batch_process_size参数
4. 实现每处理10个chunk后写入数据库的逻辑
5. 添加命令行参数支持自定义日志文件名
6. 测试验证功能

这个方案将确保在处理大量数据时，内存使用保持在合理水平，同时所有输出都被记录到按时间命名的日志文件中，便于后续分析。