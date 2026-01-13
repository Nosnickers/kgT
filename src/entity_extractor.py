# 导入JSON处理模块
import json
# 导入正则表达式模块
import re
# 导入日志模块
import logging
# 导入类型注解相关模块
from typing import List, Dict, Any, Optional
# 导入LangChain的Ollama聊天模型
from langchain_ollama import ChatOllama
# 导入LangChain的聊天提示模板
from langchain_core.prompts import ChatPromptTemplate
# 导入LangChain的JSON输出解析器
from langchain_core.output_parsers import JsonOutputParser
# 导入LangChain的消息类型
from langchain_core.messages import HumanMessage, SystemMessage
# 导入Pydantic模型和字段定义
from pydantic import BaseModel, Field


# 定义提取的实体数据模型
class ExtractedEntity(BaseModel):
    # 实体名称
    name: str = Field(description="实体的名称")
    # 实体类型（组织、产品、材料、目标等）
    type: str = Field(description="实体的类型（Organization, Product, Material, Goal, Metric, Initiative, Location等）")
    # 实体的简要描述（可选）
    description: Optional[str] = Field(default="", description="实体的简要描述")
    # 实体来源的chunk ID（可选）
    chunk_id: Optional[int] = Field(default=None, description="实体来源的chunk ID")


# 定义提取的关系数据模型
class ExtractedRelationship(BaseModel):
    # 源实体名称
    source: str = Field(description="源实体的名称")
    # 目标实体名称
    target: str = Field(description="目标实体的名称")
    # 关系类型（ACHIEVES, USES, REDUCES等）
    type: str = Field(description="关系的类型（ACHIEVES, USES, REDUCES, CONTAINS, IMPLEMENTS, LOCATED_IN等）")
    # 关系的简要描述（可选）
    description: Optional[str] = Field(default="", description="关系的简要描述")
    # 关系来源的chunk ID（可选）
    chunk_id: Optional[int] = Field(default=None, description="关系来源的chunk ID")


# 定义实体提取结果的数据模型
class ExtractionResult(BaseModel):
    # 提取的实体列表
    entities: List[ExtractedEntity] = Field(default_factory=list, description="提取的实体列表")
    # 提取的关系列表
    relationships: List[ExtractedRelationship] = Field(default_factory=list, description="提取的关系列表")


# 实体提取器类
class EntityExtractor:
    # 支持的实体类型列表 - 口腔临床专用
    ENTITY_TYPES = [
        "Patient", "VisitEvent", "Tooth", "Symptom", "Diagnosis", 
        "Treatment", "MedicalMaterial", "Drug", "MedicalStaff"
    ]
    
    # 支持的关系类型列表 - 口腔临床专用
    RELATIONSHIP_TYPES = [
        "BELONGS_TO", "CHIEF_COMPLAINT", "EXAMINATION_FINDING", "DIAGNOSED_AS", 
        "PLANNED_AS", "RECEIVED", "TARGETS", "USES", "CAUSES", "RELIEVES", 
        "LOCATED_AT", "ASSOCIATED_WITH", "ADJACENT_TO", "EXECUTED_BY", "CONTAINS_SUBSTEP"
    ]

    # 初始化实体提取器
    def __init__(self, base_url: str, model: str, temperature: float = 0.1, num_ctx: int = 4096, deep_thought_mode: bool = False):
        # 创建Ollama聊天模型实例
        self.llm = ChatOllama(
            base_url=base_url,  # Ollama服务器地址
            model=model,        # 使用的模型名称
            temperature=temperature,  # 生成文本的随机性参数
            num_ctx=num_ctx      # 上下文窗口大小
        )
        # 创建JSON输出解析器
        self.parser = JsonOutputParser(pydantic_object=ExtractionResult)
        # 是否启用深度思考模式
        self.deep_thought_mode = deep_thought_mode

    # 创建实体和关系提取的提示模板
    def create_extraction_prompt(self) -> ChatPromptTemplate:
        # 基础提示模板 - 针对口腔临床病历优化
        base_prompt = """You are an expert knowledge graph builder specializing in extracting entities and relationships from oral clinical medical records.

Your task is to extract structured clinical information from dental medical records and return them in a structured JSON format.

ENTITY TYPES (use only these for oral clinical content):
- Patient: The individual receiving dental treatment (e.g., "林某", "王某某", "张某")
- VisitEvent: A specific medical visit or consultation (e.g., "2023年10月26日就诊", "2023年11月15日就诊")
- Tooth: Specific tooth using FDI two-digit notation (e.g., "11", "12", "21", "22", "16", "26", "36", "46")
- Symptom: Patient's subjective complaints and objective clinical findings (e.g., "上前牙颜色偏黄", "自发痛", "冷热刺激痛", "龋洞", "叩痛")
- Diagnosis: Professional medical diagnosis with ICD-10 codes (e.g., "黄染牙 (K00.8)", "中龋 (K02.1)", "慢性牙髓炎 (K04.01)")
- Treatment: Medical procedures performed or planned (e.g., "Beyond冷光美白术", "树脂充填术", "根管治疗术", "拔除术", "全瓷冠修复")
- MedicalMaterial: Materials and supplies used in treatment (e.g., "纳米树脂", "玻璃离子水门汀", "多聚甲醛失活剂", "全瓷冠", "美白凝胶")
- Drug: Medications used in treatment (e.g., "阿替卡因肾上腺素注射液", "丁香油酚")
- MedicalStaff: Healthcare providers (e.g., "A陈医生", "A李医生")

RELATIONSHIP TYPES (use only these for oral clinical content):
- BELONGS_TO: Patient → VisitEvent (a visit belongs to a patient)
- CHIEF_COMPLAINT: VisitEvent → Symptom (main complaint of the visit)
- EXAMINATION_FINDING: VisitEvent → Symptom (clinical examination findings)
- DIAGNOSED_AS: VisitEvent → Diagnosis (diagnosis made during the visit)
- PLANNED_AS: VisitEvent → Treatment (treatment planned for the visit)
- RECEIVED: Patient → Treatment (patient received a treatment)
- TARGETS: Treatment → Tooth/Diagnosis (treatment targets a specific tooth or diagnosis)
- USES: Treatment → MedicalMaterial/Drug (treatment uses materials or drugs)
- CAUSES: Symptom/Diagnosis → Treatment (clinical decision: problem leads to treatment)
- RELIEVES: Treatment → Symptom (treatment aims to relieve symptoms)
- LOCATED_AT: Symptom → Tooth (symptom is located at a specific tooth)
- ASSOCIATED_WITH: Diagnosis → Tooth (diagnosis is associated with a specific tooth)
- ADJACENT_TO: Tooth → Tooth (teeth are physically adjacent)
- EXECUTED_BY: Treatment → MedicalStaff (treatment performed by medical staff)
- CONTAINS_SUBSTEP: Treatment → Treatment (complex treatment contains sub-steps)

EXTRACTION RULES FOR ORAL CLINICAL RECORDS:
1. Extract patients by their names (may be anonymized like "林某", "王某某")
2. Extract visit events with dates and key information
3. Extract teeth using FDI two-digit notation (e.g., "16" not "右上第一恒磨牙")
4. Extract symptoms from both chief complaints and examination findings
5. **CRITICAL - Extract CHIEF_COMPLAINT relationships:**
   - ALWAYS extract the main complaint (主诉) as a Symptom entity
   - ALWAYS create a CHIEF_COMPLAINT relationship: VisitEvent → Symptom
   - The chief complaint is typically found under "主诉：" section
   - Example: "主诉：上前牙颜色偏黄" → Symptom entity "上前牙颜色偏黄" + CHIEF_COMPLAINT relationship
6. Extract diagnoses with names and ICD-10 codes when available
7. Extract all treatments performed or planned
8. Extract all medical materials and drugs used
9. Extract medical staff names
10. **CRITICAL - Description Rules:**
   - For patients: include age, gender, and basic info from record
   - For visit events: include date, department, and key clinical info
   - For teeth: use FDI notation, include tooth type if mentioned
   - For symptoms: describe symptom and its characteristics
   - For diagnoses: include diagnosis name and ICD-10 code
   - For treatments: describe the procedure and key steps
   - **NEVER invent or add information not present in the text**
   - Keep descriptions concise and directly based on the text
11. **CRITICAL - Context Rules:**
    - Focus on clinically relevant entities and relationships
    - Extract relationships that show clinical decision-making
    - Pay attention to tooth-specific information and treatments
    - **ALWAYS extract CHIEF_COMPLAINT relationship when "主诉" is mentioned**
12. **CRITICAL - Strict Extraction:**
    - Extract ONLY entities and relationships that EXPLICITLY appear in THE PROVIDED TEXT
    - DO NOT create examples, scenarios, or sample content
    - DO NOT use names or information not in the actual medical record
    - DO NOT invent any diagnoses, treatments, or clinical findings
13. Return results in JSON object with the following OUTPUT FORMAT structure:

EXAMPLE FORMAT (FOR STRUCTURE REFERENCE ONLY - NOT REAL DATA):
{
  "entities": [
    {
      "name": "示例患者",
      "type": "Patient",
      "description": "32岁女性，外企项目经理"
    },
    {
      "name": "就诊事件",
      "type": "VisitEvent",
      "description": "2023年10月26日就诊"
    },
    {
      "name": "上前牙颜色偏黄",
      "type": "Symptom",
      "description": "患者主诉上前牙颜色偏黄，影响美观"
    }
  ],
  "relationships": [
    {
      "source": "示例患者",
      "target": "就诊事件",
      "type": "BELONGS_TO",
      "description": "该就诊属于该患者"
    },
    {
      "source": "就诊事件",
      "target": "上前牙颜色偏黄",
      "type": "CHIEF_COMPLAINT",
      "description": "该就诊的主诉是上前牙颜色偏黄"
    }
  ]
}

IMPORTANT REMINDERS:
- The EXAMPLE FORMAT above is ONLY for JSON structure reference
- The example contains ZERO real data from the medical record
- You MUST extract entities and relationships ONLY from THE PROVIDED TEXT below
- Replace the EXAMPLE values with your actual extracted entities and relationships from the provided text
- DO NOT use any example names or information in your actual extraction
- Every entity name must match EXACTLY what appears in the provided text
- Every relationship must be EXPLICITLY described in the provided text"""
        
        # 用户提示，提供要提取的文本
        human_prompt = """Extract entities and relationships from the oral clinical medical record below:

{text}

Return the extraction result in JSON format. Remember to extract ONLY from the text above, not from the example."""

        # 创建并返回聊天提示模板
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=base_prompt),  # 系统消息
            HumanMessage(content=human_prompt)      # 用户消息
        ])

    # 验证实体数据的必填字段
    def _validate_entity_data(self, entity_data: Dict[str, Any]) -> bool:
        """验证实体数据的必填字段"""
        # 检查必填字段是否存在
        if not entity_data.get('name') or not entity_data.get('name').strip():
            logging.error(f"实体数据缺少必填字段 'name': {entity_data}")
            return False
        
        if not entity_data.get('type') or not entity_data.get('type').strip():
            logging.error(f"实体数据缺少必填字段 'type': {entity_data}")
            return False
        
        # 检查字段值是否有效
        name = entity_data['name'].strip()
        entity_type = entity_data['type'].strip()
        
        # 检查名称是否为空或占位符
        if not name or name.lower() in ['entity_name', 'actual_entity_name_from_text', 'name', '示例患者', '示例牙位']:
            logging.error(f"实体名称无效或为占位符: {name}")
            return False
        
        # 检查类型是否为空或占位符
        if not entity_type or entity_type.lower() in ['entity_type', 'appropriate_entity_type', 'type']:
            logging.error(f"实体类型无效或为占位符: {entity_type}")
            return False
        
        return True

    # 验证关系数据的必填字段
    def _validate_relationship_data(self, rel_data: Dict[str, Any]) -> bool:
        """验证关系数据的必填字段"""
        # 检查必填字段是否存在
        if not rel_data.get('source') or not rel_data.get('source').strip():
            logging.error(f"关系数据缺少必填字段 'source': {rel_data}")
            return False
        
        if not rel_data.get('target') or not rel_data.get('target').strip():
            logging.error(f"关系数据缺少必填字段 'target': {rel_data}")
            return False
        
        if not rel_data.get('type') or not rel_data.get('type').strip():
            logging.error(f"关系数据缺少必填字段 'type': {rel_data}")
            return False
        
        # 检查字段值是否有效
        source = rel_data['source'].strip()
        target = rel_data['target'].strip()
        rel_type = rel_data['type'].strip()
        
        # 检查源实体是否为空或占位符
        if not source or source.lower() in ['source', 'actual_source_entity_name', '示例患者', '示例患者']:
            logging.error(f"关系源实体无效或为占位符: {source}")
            return False
        
        # 检查目标实体是否为空或占位符
        if not target or target.lower() in ['target', 'actual_target_entity_name', '就诊事件', '示例就诊事件']:
            logging.error(f"关系目标实体无效或为占位符: {target}")
            return False
        
        # 检查关系类型是否为空或占位符
        if not rel_type or rel_type.lower() in ['type', 'appropriate_relationship_type']:
            logging.error(f"关系类型无效或为占位符: {rel_type}")
            return False
        
        # 检查源和目标是否相同
        if source == target:
            logging.error(f"关系源和目标实体相同: {source} -> {target}")
            return False
        
        return True

    # 从文本中提取实体和关系（带校验和重试机制）
    def extract(self, text: str, max_retries: int = 3) -> ExtractionResult:
        """从文本中提取实体和关系，包含必填字段校验和重试机制"""
        
        for attempt in range(max_retries):
            try:
                # 创建提取提示
                prompt = self.create_extraction_prompt()
                
                # 格式化提示消息
                formatted_prompt = prompt.format_messages(text=text)
                
                # 调用LLM进行提取
                response = self.llm.invoke(formatted_prompt)
                content = response.content
                
                # 清理JSON响应内容
                content = self.clean_json_response(content)
                
                # 解析JSON数据
                result_data = json.loads(content)
                
                # 清理实体和关系数据中的多余引号
                def clean_entity_data(entity_data):
                    if 'name' in entity_data:
                        entity_data['name'] = entity_data['name'].strip('"\'')
                    if 'type' in entity_data:
                        entity_data['type'] = entity_data['type'].strip('"\'')
                    if 'description' in entity_data and entity_data['description']:
                        entity_data['description'] = entity_data['description'].strip('"\'')
                    return entity_data
                
                def clean_relationship_data(rel_data):
                    if 'source' in rel_data:
                        rel_data['source'] = rel_data['source'].strip('"\'')
                    if 'target' in rel_data:
                        rel_data['target'] = rel_data['target'].strip('"\'')
                    if 'type' in rel_data:
                        rel_data['type'] = rel_data['type'].strip('"\'')
                    if 'description' in rel_data and rel_data['description']:
                        rel_data['description'] = rel_data['description'].strip('"\'')
                    return rel_data
                
                # 清理实体数据
                cleaned_entities = []
                for entity in result_data.get("entities", []):
                    cleaned_entity = clean_entity_data(entity)
                    # 验证实体数据
                    if self._validate_entity_data(cleaned_entity):
                        cleaned_entities.append(cleaned_entity)
                    else:
                        logging.warning(f"跳过无效实体数据: {cleaned_entity}")
                
                # 清理关系数据
                cleaned_relationships = []
                for rel in result_data.get("relationships", []):
                    cleaned_rel = clean_relationship_data(rel)
                    # 验证关系数据
                    if self._validate_relationship_data(cleaned_rel):
                        cleaned_relationships.append(cleaned_rel)
                    else:
                        logging.warning(f"跳过无效关系数据: {cleaned_rel}")
                
                # 检查是否有有效的实体或关系
                if not cleaned_entities and not cleaned_relationships:
                    logging.warning(f"第 {attempt + 1} 次尝试未提取到有效数据，进行重试")
                    continue
                
                # 转换为实体对象列表
                entities = []
                for entity in cleaned_entities:
                    try:
                        entities.append(ExtractedEntity(**entity))
                    except Exception as e:
                        logging.error(f"创建实体对象失败: {e}, 数据: {entity}")
                
                # 转换为关系对象列表
                relationships = []
                for rel in cleaned_relationships:
                    try:
                        relationships.append(ExtractedRelationship(**rel))
                    except Exception as e:
                        logging.error(f"创建关系对象失败: {e}, 数据: {rel}")
                
                # 返回提取结果对象
                return ExtractionResult(entities=entities, relationships=relationships)
                
            # 处理JSON解析错误
            except json.JSONDecodeError as e:
                logging.error(f"第 {attempt + 1} 次尝试JSON解析错误: {e}")
                logging.error(f"响应内容: {content}")
                if attempt == max_retries - 1:
                    return ExtractionResult(entities=[], relationships=[])
            # 处理其他异常
            except Exception as e:
                logging.error(f"第 {attempt + 1} 次尝试提取错误: {e}")
                if attempt == max_retries - 1:
                    return ExtractionResult(entities=[], relationships=[])
        
        # 所有重试都失败
        logging.error(f"所有 {max_retries} 次尝试均失败")
        return ExtractionResult(entities=[], relationships=[])

    # 清理LLM返回的JSON响应内容
    def clean_json_response(self, content: str) -> str:
        # 去除首尾空白字符
        content = content.strip()
        
        # 处理包含<think>标签的响应
        if "<think>" in content:
            # 移除<think>和</think>标签，以及标签内的内容
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            # 去除可能的空白字符
            content = content.strip()
        
        # 如果包含```json标记，则提取标记内的内容
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        # 如果包含```标记，则提取标记内的内容
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # 寻找JSON数据的开始位置 - 找到第一个'{'字符
        json_start = content.find('{')
        if json_start == -1:
            # 没有找到JSON数据的开始位置，返回空JSON
            return "{}"
        
        # 从第一个'{'开始提取内容
        content = content[json_start:]
        
        # 寻找JSON数据的结束位置 - 正确匹配括号
        brace_count = 0
        json_end = -1
        for i, char in enumerate(content):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_end = i + 1
                    break
        
        if json_end == -1:
            # 没有找到匹配的结束括号，返回空JSON
            return "{}"
        
        # 提取有效的JSON部分
        content = content[:json_end]
        
        # 验证提取的内容是否为有效的JSON
        try:
            import json
            json.loads(content)
            return content
        except json.JSONDecodeError:
            # 如果不是有效的JSON，返回空JSON
            return "{}"

    # 批量提取多个文本的实体和关系
    def extract_batch(self, texts: List[str]) -> List[ExtractionResult]:
        results = []
        # 遍历每个文本进行提取
        for text in texts:
            result = self.extract(text)
            results.append(result)
        return results

    # 验证提取结果的有效性
    def validate_extraction(self, result: ExtractionResult) -> bool:
        # 验证所有实体类型是否有效
        for entity in result.entities:
            if entity.type not in self.ENTITY_TYPES:
                print(f"警告: 实体 '{entity.name}' 的类型 '{entity.type}' 无效")
                return False
        
        # 验证所有关系类型是否有效
        for rel in result.relationships:
            if rel.type not in self.RELATIONSHIP_TYPES:
                print(f"警告: 关系 '{rel.source} -> {rel.target}' 的类型 '{rel.type}' 无效")
                return False
        
        return True

    # 获取提取结果的统计信息
    def get_extraction_stats(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        # 计算总实体数
        total_entities = sum(len(result.entities) for result in results)
        # 计算总关系数
        total_relationships = sum(len(result.relationships) for result in results)
        
        # 初始化实体类型和关系类型的计数字典
        entity_type_counts = {}
        relationship_type_counts = {}
        
        # 统计各种实体类型和关系类型的数量
        for result in results:
            for entity in result.entities:
                entity_type_counts[entity.type] = entity_type_counts.get(entity.type, 0) + 1
            
            for rel in result.relationships:
                relationship_type_counts[rel.type] = relationship_type_counts.get(rel.type, 0) + 1
        
        # 返回统计信息
        return {
            "total_chunks": len(results),  # 文本块总数
            "total_entities": total_entities,  # 总实体数
            "total_relationships": total_relationships,  # 总关系数
            "avg_entities_per_chunk": total_entities / len(results) if results else 0,  # 每块平均实体数
            "avg_relationships_per_chunk": total_relationships / len(results) if results else 0,  # 每块平均关系数
            "entity_type_distribution": entity_type_counts,  # 实体类型分布
            "relationship_type_distribution": relationship_type_counts  # 关系类型分布
        }
