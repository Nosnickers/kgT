## 问题分析
用户报告在Neo4j中看到实体 `Carbon Emissions` 和 `India` 带有 `chunk_id: [1, 2]` 和 `chunk_id: [0]`，但在对应chunk中根本没有找到这些实体。

## 根因
1. **Neo4j实体更新逻辑错误**：在 `neo4j_manager.py` 的 `batch_create_entities` 方法中，`ON MATCH` 子句直接使用 `e.chunk_id = $properties.chunk_id` 覆盖实体的chunk_id，而不是合并数组
2. **批次处理导致覆盖**：当同一个实体在不同批次中被处理时，数据库中的chunk_id会被最后一个批次的chunk_id覆盖，导致与实际出现位置不匹配
3. **关系处理存在同样问题**：`batch_create_relationships` 方法也存在相同的覆盖问题

## 解决方案
1. **修改实体批量创建逻辑**：
   - 将 `neo4j_manager.py` 中 `batch_create_entities` 方法的 `ON MATCH` 子句修改为合并chunk_id数组
   - 使用Neo4j的数组操作函数确保chunk_id唯一且有序

2. **修改关系批量创建逻辑**：
   - 对 `batch_create_relationships` 方法应用相同的修复

3. **修复具体实现**：
   - 在Cypher查询中使用 `apoc.coll.union` 或原生数组操作来合并chunk_id
   - 确保描述字段也正确处理，避免丢失信息

## 代码修改点
1. `src/neo4j_manager.py` 第133-139行：修改实体批量创建的Cypher查询
2. `src/neo4j_manager.py` 第167-175行：修改关系批量创建的Cypher查询

## 预期效果
- 实体的chunk_id数组将包含该实体实际出现的所有chunk_id
- 关系的chunk_id数组将包含该关系实际出现的所有chunk_id
- 实体描述将保留最完整的信息，避免被覆盖
- 用户将能在指定chunk中找到对应的实体