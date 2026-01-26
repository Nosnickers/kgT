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
from langchain_core.messages import SystemMessage, HumanMessage


# 知识图谱构建器类
class GraphBuilder:
    # 初始化知识图谱构建器
    def __init__(
        self,
        data_loader: DataLoader,           # 数据加载器实例
        neo4j_manager: Neo4jManager,      # Neo4j管理器实例
        entity_extractor: EntityExtractor, # 实体提取器实例
        max_retries: int = 3,             # 最大重试次数（默认3次）
        retry_delay: int = 2,              # 重试延迟时间（默认2秒）
        logger: Optional[Any] = None,        # 可选的日志记录器
        enable_entity_linking: bool = False, # 是否启用实体链接功能（查询现有实体）
        entity_types_to_link: List[str] = None  # 要链接的实体类型列表，None表示使用默认值
    ):
        self.data_loader = data_loader
        self.neo4j_manager = neo4j_manager
        self.entity_extractor = entity_extractor
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger
        self.enable_entity_linking = enable_entity_linking
        
        # 设置要链接的实体类型
        if entity_types_to_link is None:
            # 默认链接患者相关实体类型
            self.entity_types_to_link = ["Patient", "PatientId"]
        else:
            self.entity_types_to_link = entity_types_to_link
        
        # 缓存已查询的现有实体，减少数据库查询次数
        self.existing_entities_cache: Dict[str, List[Dict[str, Any]]] = {}

    def _query_existing_entities(self, entity_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        查询图数据库中现有的实体
        
        Args:
            entity_types: 要查询的实体类型列表，如果为None则使用self.entity_types_to_link
            
        Returns:
            字典，键为实体类型，值为该类型的实体列表
        """
        if not self.enable_entity_linking:
            return {}
        
        import logging
        
        if entity_types is None:
            entity_types = self.entity_types_to_link
        
        result = {}
        for entity_type in entity_types:
            # 检查缓存
            if entity_type in self.existing_entities_cache:
                result[entity_type] = self.existing_entities_cache[entity_type]
                logging.debug(f"从缓存获取 {entity_type} 类型实体: {len(result[entity_type])} 个")
                continue
            
            try:
                # 使用Cypher查询指定类型的实体
                with self.neo4j_manager.driver.session() as session:
                    query = """
                    MATCH (e:Entity {type: $entity_type})
                    RETURN e.name AS name, e.type AS type, e.description AS description, properties(e) AS properties
                    LIMIT 100
                    """
                    records = session.run(query, entity_type=entity_type)
                    
                    entity_list = []
                    for record in records:
                        entity_list.append({
                            "name": record["name"],
                            "type": record["type"],
                            "description": record["description"] or "",
                            "properties": dict(record["properties"])
                        })
                
                self.existing_entities_cache[entity_type] = entity_list
                result[entity_type] = entity_list
                logging.info(f"查询到 {entity_type} 类型实体: {len(entity_list)} 个")
            except Exception as e:
                logging.error(f"查询 {entity_type} 类型实体失败: {e}")
                result[entity_type] = []
        
        return result
    
    def _format_existing_entities_for_prompt(self, existing_entities: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        将现有实体信息格式化为提示词文本
        
        Args:
            existing_entities: 现有实体字典
            
        Returns:
            格式化的文本，用于添加到提示词中
        """
        if not existing_entities:
            return ""
        
        parts = []
        for entity_type, entities in existing_entities.items():
            if not entities:
                continue
            
            parts.append(f"现有 {entity_type} 实体（{len(entities)} 个）：")
            for i, entity in enumerate(entities[:10]):  # 限制最多显示10个
                desc = entity.get("description", "")
                if desc:
                    parts.append(f"  {i+1}. {entity['name']} - {desc}")
                else:
                    parts.append(f"  {i+1}. {entity['name']}")
        
        if parts:
            return "\n".join(parts)
        return ""
    
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
    # 带日志记录的实体提取方法
    def _extract_with_logging(self, chunk: DataChunk) -> ExtractionResult:
        """带详细日志记录的实体提取方法"""
        import json
        import logging
        
        chunk_id = chunk.metadata.get('chunk_id')
        title = chunk.metadata.get('title', '')
        combined_text = f"标题：{title}\n内容：{chunk.content}"
        
        if self.logger:
            self.logger.log_section(f"处理Chunk {chunk_id}")
            self.logger.log_section("标题", title)
            self.logger.log_section("组合文本", combined_text)
        
        # 如果启用了实体链接，查询现有实体并构建上下文
        existing_entities_context = ""
        if self.enable_entity_linking:
            try:
                existing_entities = self._query_existing_entities()
                existing_entities_context = self._format_existing_entities_for_prompt(existing_entities)
                if existing_entities_context:
                    logging.info(f"为数据块 {chunk_id} 提供 {sum(len(entities) for entities in existing_entities.values())} 个现有实体上下文")
            except Exception as e:
                logging.warning(f"查询现有实体失败，继续无上下文提取: {e}")
        
        # 创建提取提示（根据是否提供上下文）
        prompt = self.entity_extractor.create_extraction_prompt(
            existing_entities_context=existing_entities_context if existing_entities_context else None
        )
        # 调试日志：检查提示模板
        logging.info(f"提示模板类型: {type(prompt)}")
        if hasattr(prompt, 'input_variables'):
            logging.info(f"提示模板 input_variables: {prompt.input_variables}")
        logging.info(f"提示模板消息数量: {len(prompt.messages) if prompt.messages else 0}")
        
        # 获取系统提示词和用户提示词
        system_prompt = prompt.messages[0].content if prompt.messages else ""
        # 处理 HumanMessagePromptTemplate（模板对象）和 HumanMessage（消息对象）
        if len(prompt.messages) > 1:
            msg = prompt.messages[1]
            if hasattr(msg, 'template'):  # HumanMessagePromptTemplate
                user_prompt = msg.template.format(text=combined_text)
                original_template = msg.template
            elif hasattr(msg, 'content'):  # HumanMessage
                user_prompt = msg.content.format(text=combined_text)
                original_template = msg.content
            else:
                user_prompt = combined_text
                original_template = str(msg)
        else:
            user_prompt = combined_text
            original_template = "无消息"
        # 调试日志：检查用户提示词格式化
        logging.info(f"原始用户提示词模板: {original_template[:200] if original_template else '无消息'}")
        logging.info(f"格式化后的用户提示词 (用于日志): {user_prompt[:200] if user_prompt else '空'}")
        
        if self.logger:
            self.logger.log_section("系统提示词", system_prompt)
            self.logger.log_section("用户提示词", user_prompt)
        
        # 格式化提示消息
        formatted_prompt = prompt.format_messages(text=combined_text)
        # 调试日志：记录格式化后的提示词
        logging.info(f"原始文本长度: {len(chunk.content)}，组合文本长度: {len(combined_text)}")
        logging.info(f"组合文本预览: {combined_text[:150] if combined_text else '空'}")
        if formatted_prompt and len(formatted_prompt) > 1:
            logging.info(f"格式化后的用户提示词内容: {formatted_prompt[1].content[:200] if formatted_prompt[1].content else '空'}")
            # 检查格式化是否成功
            if "{text}" in formatted_prompt[1].content or "<text>" in formatted_prompt[1].content:
                logging.warning("检测到未替换的占位符，使用直接字符串格式化")
                # 直接格式化用户提示词
                # 从提示模板中获取用户提示词模板
                if len(prompt.messages) > 1:
                    msg = prompt.messages[1]
                    if hasattr(msg, 'template'):  # HumanMessagePromptTemplate
                        human_prompt = msg.template
                    elif hasattr(msg, 'content'):  # HumanMessage
                        human_prompt = msg.content
                    else:
                        human_prompt = "Extract entities and relationships from: {text}"
                else:
                    human_prompt = "Extract entities and relationships from: {text}"
                formatted_human_prompt = human_prompt.format(text=combined_text)
                # 重新构建formatted_prompt
                # 获取系统提示词
                system_content = ""
                if prompt.messages and len(prompt.messages) > 0:
                    system_msg = prompt.messages[0]
                    if hasattr(system_msg, 'content'):
                        system_content = system_msg.content
                formatted_prompt = [
                    SystemMessage(content=system_content),
                    HumanMessage(content=formatted_human_prompt)
                ]
                logging.info(f"直接格式化后的用户提示词: {formatted_human_prompt[:200]}")
        
        # 调用LLM进行提取
        if self.logger:
            self.logger.info("正在调用LLM...")
        
        response = self.entity_extractor.llm.invoke(formatted_prompt)
        raw_content = response.content
        
        if self.logger:
            self.logger.log_section("LLM原始响应", raw_content)
        
        # 清理JSON响应内容
        cleaned_content = self.entity_extractor.clean_json_response(raw_content)
        
        if self.logger:
            self.logger.log_section("清理后的JSON响应", cleaned_content)
        
        # 解析JSON数据
        result_data = json.loads(cleaned_content)
        
        if self.logger:
            self.logger.log_section("解析后的JSON数据", result_data)
        
        # 数据清理和验证过程
        if self.logger:
            self.logger.log_section("开始数据验证和清理")
        
        # 清理实体数据
        cleaned_entities = []
        for entity in result_data.get("entities", []):
            cleaned_entity = self._clean_entity_data(entity)
            
            # 基本字段验证
            if not self._validate_entity_data(cleaned_entity):
                if self.logger:
                    self.logger.warning(f"✗ 无效实体被跳过（基本验证失败）: {cleaned_entity}")
                continue
            
            # 文本验证（防止幻觉）
            if hasattr(self.entity_extractor, '_validate_entity_against_text'):
                if not self.entity_extractor._validate_entity_against_text(cleaned_entity, combined_text):
                    if self.logger:
                        self.logger.warning(f"✗ 无效实体被跳过（未在文本中找到）: {cleaned_entity}")
                    continue
            
            cleaned_entities.append(cleaned_entity)
            if self.logger:
                self.logger.info(f"✓ 有效实体: {cleaned_entity}")
        
        # 清理关系数据
        cleaned_relationships = []
        for rel in result_data.get("relationships", []):
            cleaned_rel = self._clean_relationship_data(rel)
            if self._validate_relationship_data(cleaned_rel):
                cleaned_relationships.append(cleaned_rel)
                if self.logger:
                    self.logger.info(f"✓ 有效关系: {cleaned_rel}")
            else:
                if self.logger:
                    self.logger.warning(f"✗ 无效关系被跳过: {cleaned_rel}")
        
        # 转换为实体对象列表
        entities = []
        for entity in cleaned_entities:
            try:
                entities.append(ExtractedEntity(
                    name=entity['name'],
                    type=entity['type'],
                    description=entity.get('description', ''),
                    chunk_id=chunk_id
                ))
            except Exception as e:
                if self.logger:
                    self.logger.error(f"创建实体对象失败: {e}, 数据: {entity}")
        
        # 转换为关系对象列表
        relationships = []
        for rel in cleaned_relationships:
            try:
                relationships.append(ExtractedRelationship(
                    source=rel['source'],
                    target=rel['target'],
                    type=rel['type'],
                    description=rel.get('description', ''),
                    chunk_id=chunk_id
                ))
            except Exception as e:
                if self.logger:
                    self.logger.error(f"创建关系对象失败: {e}, 数据: {rel}")
        
        if self.logger:
            self.logger.log_section("提取结果", {
                "实体数量": len(entities),
                "关系数量": len(relationships),
                "实体详情": [
                    {"名称": e.name, "类型": e.type, "描述": e.description}
                    for e in entities
                ],
                "关系详情": [
                    {"源": r.source, "目标": r.target, "类型": r.type, "描述": r.description}
                    for r in relationships
                ]
            })
        
        return ExtractionResult(entities=entities, relationships=relationships)
    
    def _clean_entity_data(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理实体数据"""
        if 'name' in entity_data:
            entity_data['name'] = entity_data['name'].strip('"\'')
        if 'type' in entity_data:
            entity_data['type'] = entity_data['type'].strip('"\'')
        if 'description' in entity_data and entity_data['description']:
            entity_data['description'] = entity_data['description'].strip('"\'')
        return entity_data
    
    def _clean_relationship_data(self, rel_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理关系数据"""
        if 'source' in rel_data:
            rel_data['source'] = rel_data['source'].strip('"\'')
        if 'target' in rel_data:
            rel_data['target'] = rel_data['target'].strip('"\'')
        if 'type' in rel_data:
            rel_data['type'] = rel_data['type'].strip('"\'')
        if 'description' in rel_data and rel_data['description']:
            rel_data['description'] = rel_data['description'].strip('"\'')
        return rel_data
    
    def _validate_entity_data(self, entity_data: Dict[str, Any]) -> bool:
        """验证实体数据的必填字段"""
        if not entity_data.get('name') or not entity_data.get('name').strip():
            return False
        
        if not entity_data.get('type') or not entity_data.get('type').strip():
            return False
        
        name = entity_data['name'].strip()
        entity_type = entity_data['type'].strip()
        
        if not name or name.lower() in ['entity_name', 'actual_entity_name_from_text', 'name']:
            return False
        
        if not entity_type or entity_type.lower() in ['entity_type', 'appropriate_entity_type', 'type']:
            return False
        
        return True
    
    def _validate_relationship_data(self, rel_data: Dict[str, Any]) -> bool:
        """验证关系数据的必填字段"""
        if not rel_data.get('source') or not rel_data.get('source').strip():
            return False
        
        if not rel_data.get('target') or not rel_data.get('target').strip():
            return False
        
        if not rel_data.get('type') or not rel_data.get('type').strip():
            return False
        
        source = rel_data['source'].strip()
        target = rel_data['target'].strip()
        rel_type = rel_data['type'].strip()
        
        if not source or source.lower() in ['source', 'actual_source_entity_name']:
            return False
        
        if not target or target.lower() in ['target', 'actual_target_entity_name']:
            return False
        
        if not rel_type or rel_type.lower() in ['type', 'appropriate_relationship_type']:
            return False
        
        if source == target:
            return False
        
        return True
    
    def _extract_with_retry(self, chunk: DataChunk) -> ExtractionResult:
        import logging
        
        # 如果有logger，使用带日志的提取方法
        if hasattr(self, 'logger') and self.logger:
            return self._extract_with_logging(chunk)
        
        # 否则使用原始的提取方法
        title = chunk.metadata.get('title', '')
        combined_text = f"标题：{title}\n内容：{chunk.content}"
        
        # 如果启用了实体链接，查询现有实体并构建上下文
        existing_entities_context = ""
        if self.enable_entity_linking:
            try:
                existing_entities = self._query_existing_entities()
                existing_entities_context = self._format_existing_entities_for_prompt(existing_entities)
                if existing_entities_context:
                    logging.info(f"为数据块 {chunk.metadata.get('chunk_id')} 提供 {sum(len(entities) for entities in existing_entities.values())} 个现有实体上下文")
            except Exception as e:
                logging.warning(f"查询现有实体失败，继续无上下文提取: {e}")
        
        for attempt in range(self.max_retries):
            try:
                # 提取实体（根据是否提供上下文选择方法）
                if existing_entities_context:
                    result = self.entity_extractor.extract_with_context(
                        combined_text, 
                        existing_entities_context=existing_entities_context
                    )
                else:
                    result = self.entity_extractor.extract(combined_text)
                    
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
