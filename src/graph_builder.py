# 导入时间模块，用于重试延迟
import time
# 导入类型注解相关模块
from typing import List, Dict, Any, Optional
# 导入进度条库
from tqdm import tqdm

# 导入数据加载器相关模块
from src.data_loader import DataLoader, DataChunk
# 导入Neo4j管理器相关模块
from src.neo4j_manager import Neo4jManager, Entity, Relationship
# 导入实体提取器相关模块
from src.entity_extractor import EntityExtractor, ExtractionResult, ExtractedEntity, ExtractedRelationship


# 知识图谱构建器类
class GraphBuilder:
    # 初始化知识图谱构建器
    def __init__(
        self,
        data_loader: DataLoader,           # 数据加载器实例
        neo4j_manager: Neo4jManager,      # Neo4j管理器实例
        entity_extractor: EntityExtractor, # 实体提取器实例
        max_retries: int = 3,             # 最大重试次数（默认3次）
        retry_delay: int = 2              # 重试延迟时间（默认2秒）
    ):
        self.data_loader = data_loader
        self.neo4j_manager = neo4j_manager
        self.entity_extractor = entity_extractor
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # 构建知识图谱
    def build_graph(
        self,
        chunks: Optional[List[DataChunk]] = None,  # 数据块列表（可选）
        show_progress: bool = True,                # 是否显示进度条（默认True）
        clear_database: bool = True,               # 是否清空数据库（默认True）
        batch_process_size: int = 10,              # 每处理多少个chunk后写入数据库
        csv_output_prefix: Optional[str] = None    # 输出csv文件前缀，与日志文件名保持一致
    ) -> Dict[str, Any]:
        import logging
        
        # 如果需要清空数据库
        if clear_database:
            logging.info("正在清空数据库...")
            self.neo4j_manager.clear_database()  # 清空数据库
            self.neo4j_manager.create_constraints()  # 创建约束

        # 如果没有提供数据块，则加载和分块数据
        if chunks is None:
            logging.info("正在加载和分块数据...")
            chunks = self.data_loader.load_and_chunk()
            
            # 如果提供了csv输出前缀，则将数据块保存为csv文件
            if csv_output_prefix:
                self.data_loader.save_chunks_to_csv(chunks, csv_output_prefix)

        total_chunks = len(chunks)
        logging.info(f"正在处理 {total_chunks} 个数据块，每 {batch_process_size} 个数据块写入一次数据库...")
        
        # 存储所有实体（去重）
        all_entities = {}
        # 存储当前批次新增的实体
        new_entities = {}
        # 存储所有关系（去重）
        all_relationships = {}
        # 存储当前批次新增的关系
        new_relationships = []
        # 存储所有提取结果
        extraction_results = []
        
        # 统计信息
        total_entities_created = 0
        total_relationships_created = 0
        
        # 创建进度条迭代器
        chunks_iter = tqdm(chunks, desc="提取实体和关系") if show_progress else chunks
        
        # 遍历每个数据块
        for i, chunk in enumerate(chunks_iter, 1):
            # 获取当前chunk的ID
            chunk_id = chunk.metadata.get("chunk_id", i-1)
            
            # 带重试机制的实体提取
            result = self._extract_with_retry(chunk)
            extraction_results.append(result)
            
            # 处理提取的实体
            for entity in result.entities:
                # 清理实体名称和类型，去除两端的引号
                entity_name = entity.name.strip('"\'')
                entity_type = entity.type.strip('"\'')
                entity_desc = entity.description.strip('"\'') if entity.description else ""
                
                entity_key = (entity_name, entity_type)  # 使用清理后的名称和类型作为唯一键
                if entity_key not in all_entities:
                    # 创建新的Entity对象并添加到字典中，包含chunk_id数组
                    entity_obj = Entity(
                        name=entity_name,
                        type=entity_type,
                        properties={"description": entity_desc, "chunk_id": [chunk_id]}
                    )
                    all_entities[entity_key] = entity_obj
                    new_entities[entity_key] = entity_obj  # 记录为新增实体
                else:
                    # 实体已存在，合并chunk_id数组
                    entity_obj = all_entities[entity_key]
                    current_chunk_ids = entity_obj.properties.get("chunk_id", [])
                    if isinstance(current_chunk_ids, list):
                        if chunk_id not in current_chunk_ids:
                            current_chunk_ids.append(chunk_id)
                    else:
                        # 如果当前不是数组，转换为数组
                        entity_obj.properties["chunk_id"] = [current_chunk_ids, chunk_id] if current_chunk_ids != chunk_id else [current_chunk_ids]
                    # 更新实体对象
                    all_entities[entity_key] = entity_obj
                    new_entities[entity_key] = entity_obj  # 更新新增实体
            
            # 处理提取的关系
            for rel in result.relationships:
                # 清理关系数据，去除两端的引号
                rel_source = rel.source.strip('"\'')
                rel_target = rel.target.strip('"\'')
                rel_type = rel.type.strip('"\'')
                rel_desc = rel.description.strip('"\'') if rel.description else ""
                
                # 使用(source, target, type)作为关系唯一键
                rel_key = (rel_source, rel_target, rel_type)
                
                if rel_key not in all_relationships:
                    # 创建新的Relationship对象并添加到字典中，包含chunk_id数组
                    rel_obj = Relationship(
                        source=rel_source,
                        target=rel_target,
                        type=rel_type,
                        properties={"description": rel_desc, "chunk_id": [chunk_id]}
                    )
                    all_relationships[rel_key] = rel_obj
                    new_relationships.append(rel_obj)  # 记录为新增关系
                else:
                    # 关系已存在，合并chunk_id数组
                    rel_obj = all_relationships[rel_key]
                    current_chunk_ids = rel_obj.properties.get("chunk_id", [])
                    if isinstance(current_chunk_ids, list):
                        if chunk_id not in current_chunk_ids:
                            current_chunk_ids.append(chunk_id)
                    else:
                        # 如果当前不是数组，转换为数组
                        rel_obj.properties["chunk_id"] = [current_chunk_ids, chunk_id] if current_chunk_ids != chunk_id else [current_chunk_ids]
                    # 更新关系对象
                    all_relationships[rel_key] = rel_obj
                    # 添加到新增关系列表
                    new_relationships.append(rel_obj)
            
            # 每处理batch_process_size个chunk或处理完所有chunk后，写入数据库
            if i % batch_process_size == 0 or i == total_chunks:
                current_batch = i // batch_process_size if i % batch_process_size == 0 else i // batch_process_size + 1
                logging.info(f"\n批次 {current_batch}: 处理完 {i} 个数据块，准备写入数据库...")
                
                # 将当前批次的新增实体存储到Neo4j
                if new_entities:
                    logging.info(f"批次 {current_batch}: 正在将 {len(new_entities)} 个新增实体存储到Neo4j...")
                    entity_list = list(new_entities.values())
                    entities_created = self._batch_create_with_retry(
                        entity_list,
                        self.neo4j_manager.batch_create_entities
                    )
                    total_entities_created += entities_created
                else:
                    logging.info(f"批次 {current_batch}: 没有新增实体需要存储")
                
                # 将当前批次的关系存储到Neo4j
                logging.info(f"批次 {current_batch}: 正在将 {len(new_relationships)} 个关系存储到Neo4j...")
                relationships_created = self._batch_create_with_retry(
                    new_relationships,
                    self.neo4j_manager.batch_create_relationships
                )
                total_relationships_created += relationships_created
                
                # 清空新增关系列表和新增实体字典
                new_relationships = []
                new_entities = {}
                
                logging.info(f"批次 {current_batch}: 写入完成，已处理 {i}/{total_chunks} 个数据块")
        
        logging.info(f"\n提取完成：共提取 {len(all_entities)} 个唯一实体")
        logging.info(f"写入完成：共创建 {total_entities_created} 个实体和 {total_relationships_created} 个关系")
        
        # 构建统计信息
        stats = {
            "chunks_processed": total_chunks,  # 处理的数据块数量
            "entities_extracted": len(all_entities),  # 提取的实体数量
            "relationships_extracted": total_relationships_created,  # 提取的关系数量
            "entities_created": total_entities_created,  # 创建的实体数量
            "relationships_created": total_relationships_created,  # 创建的关系数量
            "extraction_stats": self.entity_extractor.get_extraction_stats(extraction_results)  # 提取统计信息
        }
        
        return stats

    # 带重试机制的实体提取
    def _extract_with_retry(self, chunk: DataChunk) -> ExtractionResult:
        import logging
        # 最多重试max_retries次
        for attempt in range(self.max_retries):
            try:
                # 提取实体
                result = self.entity_extractor.extract(chunk.content)
                if result.entities or result.relationships:
                    return result
                else:
                    logging.warning(f"从数据块 {chunk.metadata.get('chunk_id')} 中未提取到实体/关系")
                    return result
            except Exception as e:
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries - 1:
                    logging.warning(f"提取失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    time.sleep(self.retry_delay)
                else:
                    # 最后一次尝试失败
                    logging.error(f"提取失败，已尝试 {self.max_retries} 次: {e}")
                    return ExtractionResult(entities=[], relationships=[])

    # 带重试机制的批量创建
    def _batch_create_with_retry(
        self,
        items: List,        # 要创建的项列表
        create_func,        # 创建函数
        batch_size: int = 100  # 批次大小（默认100）
    ) -> int:
        import logging
        total_created = 0
        # 按批次处理
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            # 最多重试max_retries次
            for attempt in range(self.max_retries):
                try:
                    # 调用创建函数
                    created = create_func(batch)
                    total_created += created
                    break
                except Exception as e:
                    # 如果不是最后一次尝试，等待后重试
                    if attempt < self.max_retries - 1:
                        logging.warning(f"批量创建失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                        time.sleep(self.retry_delay)
                    else:
                        # 最后一次尝试失败
                        logging.error(f"批量创建失败，已尝试 {self.max_retries} 次: {e}")
        return total_created

    # 查询知识图谱
    def query_graph(self, query: str) -> List[Dict[str, Any]]:
        with self.neo4j_manager.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    # 获取实体信息
    def get_entity_info(self, entity_name: str) -> Dict[str, Any]:
        # 获取实体的关系
        relationships = self.neo4j_manager.get_entity_relationships(entity_name)
        
        return {
            "entity_name": entity_name,  # 实体名称
            "total_relationships": len(relationships),  # 关系总数
            "relationships": relationships  # 关系列表
        }

    # 查找实体连接
    def find_connections(
        self,
        entity_name: str,   # 实体名称
        max_depth: int = 2  # 最大深度（默认2）
    ) -> List[Dict[str, Any]]:
        with self.neo4j_manager.driver.session() as session:
            # Cypher查询，查找指定深度的实体连接
            query = """
            MATCH (start:Entity {name: $name})-[r*1..$max_depth]-(end:Entity)
            RETURN start, r, end
            LIMIT 100
            """
            result = session.run(query, name=entity_name, max_depth=max_depth)
            return [record.data() for record in result]

    # 获取图谱摘要
    def get_graph_summary(self) -> Dict[str, Any]:
        # 获取统计信息
        stats = self.neo4j_manager.get_statistics()
        
        return {
            "total_entities": stats["total_entities"],  # 实体总数
            "total_relationships": stats["total_relationships"],  # 关系总数
            "entity_types": stats["entity_types"],  # 实体类型分布
            "relationship_types": stats["relationship_types"]  # 关系类型分布
        }

    # 导出图谱到JSON文件
    def export_to_json(self, output_path: str) -> bool:
        try:
            # 获取图谱摘要
            summary = self.get_graph_summary()
            
            # 获取所有实体
            entities = []
            for entity_type in summary["entity_types"].keys():
                type_entities = self.neo4j_manager.get_entities_by_type(entity_type)
                entities.extend(type_entities)
            
            # 获取所有关系
            relationships = []
            for rel_type in summary["relationship_types"].keys():
                type_rels = self.neo4j_manager.get_relationships_by_type(rel_type)
                relationships.extend(type_rels)
            
            # 构建导出数据
            export_data = {
                "summary": summary,  # 图谱摘要
                "entities": entities,  # 所有实体
                "relationships": relationships  # 所有关系
            }
            
            # 导入JSON模块
            import json
            # 写入JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"图谱已导出到 {output_path}")
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

    # 可视化图谱样本
    def visualize_sample(self, entity_name: str, max_depth: int = 2) -> str:
        # 查找实体连接
        connections = self.find_connections(entity_name, max_depth)
        
        if not connections:
            return f"未找到实体 {entity_name} 的连接"
        
        # 构建可视化文本
        viz_text = f"知识图谱样本 (中心: {entity_name})\n"
        viz_text += "=" * 60 + "\n\n"
        
        # 显示前20个连接
        for conn in connections[:20]:
            start = conn.get("start", {})
            end = conn.get("end", {})
            rels = conn.get("r", [])
            
            viz_text += f"{start.get('name', 'Unknown')} "
            for rel in rels:
                viz_text += f"-[{rel.get('type', 'UNKNOWN')}]-> "
            viz_text += f"{end.get('name', 'Unknown')}\n"
        
        return viz_text
