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
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
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
    type: str = Field(description="实体的类型")
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
    type: str = Field(description="关系的类型")
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
    # 支持的实体类型列表 
    ENTITY_TYPES = [
        "Patient", # (patient_id, name可不输出，若存在则脱敏)
        "PatientId", # 患者ID
        "Demographics", # 患者基本信息（年龄、性别等）
        "ChiefComplaint", # 主诉
        "PresentIllness", # 现病史事件/病程
        "PastHistory", # 既往病史
        "FamilyHistory", # 家族病史
        "SocialHistory", # 社会病史（吸烟、饮酒、职业等）
        "Symptom", # 症状
        "Sign", # 体征
        "Diagnosis", # 诊断
        "Medication", # 药物名，含剂量/频次/途径
        "Procedure", # 操作/手术/治疗过程
        "LabTest", # 检验项
        "LabValue", # 检验数值/单位
        "Imaging", # 影像检查项
        "Allergies", # 过敏
        "Treatment", # 治疗
        "Vitals", #  vital signs (体温、血压、脉搏、呼吸等)
        "Duration", # 时长
        "TemporalExpression", # 时间表达，如“3天前”
        "Material", # 材料
    ]
    
    # 支持的关系类型列表 
    RELATIONSHIP_TYPES = [
        "HAS_DIAGNOSIS", # 诊断关系 (Patient -> Diagnosis)
        "DIAGNOSIS_HAS_SYMPTOM", # 诊断包含症状 (Diagnosis -> Symptom)
        "SYMPTOM_OF", # 症状属于 (Symptom -> Diagnosis)
        "MEDICATION_TREAT_FOR", # 药物治疗目标 (Medication -> Diagnosis)
        "MEDICATION_HAS_DOSE", # 药物剂量 (Medication -> Dose)
        "LABTEST_HAS_VALUE", # 检验结果 (LabTest -> LabValue)
        "PROCEDURE_PERFORMED_ON", # 治疗过程 performed on (Procedure -> BodyPart/Diagnosis)
        "ALLERGY_TO", # 过敏 (Patient -> Allergen)
        "FAMILY_HISTORY_OF", # 家族病史 (Patient -> Diagnosis)
        "CHIEF_COMPLAINT", # 主诉关系 (VisitEvent -> Symptom)
        "MEDICAL_ADVICE", # 医嘱 (Patient -> Treatment)
        # 新增口腔科材料相关关系类型
        "PROCEDURE_USES_MATERIAL", # 治疗使用材料 (Procedure -> Material)
        "MATERIAL_HAS_COMPONENT", # 材料包含成分 (Material -> Component)
        "PROCEDURE_PERFORMED_BY", # 治疗由医生执行 (Procedure -> Doctor)
        "PROCEDURE_AIMS_TO_ACHIEVE", # 治疗旨在达成目标 (Procedure -> Goal/Target)
        "PATIENT_HAS_OCCUPATION", # 患者有职业 (Patient -> Occupation)
        "PATIENT_IS_FIRST_VISIT", # 患者首次就诊 (Patient -> FirstVisitStatus)
    ]

    # 初始化实体提取器
    def __init__(self, base_url: str, model: str, temperature: float = 0.1, num_ctx: int = 4096, deep_thought_mode: bool = False):
        # 根据深度思考模式配置LLM参数
        llm_kwargs = {
            "base_url": base_url,
            "model": model,
            "temperature": temperature,
            "num_ctx": num_ctx
        }
        
        # 如果深度思考模式关闭，添加停止标记以防止思考过程输出
        # 暂时注释掉stop tokens，因为会导致空响应
        # if not deep_thought_mode:
        #     llm_kwargs["stop"] = ["<think>", "</think>"]
        
        # 创建Ollama聊天模型实例
        self.llm = ChatOllama(**llm_kwargs)
        
        # 创建JSON输出解析器
        self.parser = JsonOutputParser(pydantic_object=ExtractionResult)
        # 是否启用深度思考模式
        self.deep_thought_mode = deep_thought_mode

    # 创建实体和关系提取的提示模板
    def create_extraction_prompt(self) -> ChatPromptTemplate:
        # 基础提示模板 - 针对口腔临床病历优化
        base_prompt = """NO THINKING OUTPUT: DO NOT output any thinking process like <think>...</think>. Respond with JSON only.

NO HALLUCINATION POLICY: You MUST NOT invent, create, or extract any information that is not explicitly stated in the provided text. If something is not mentioned, do not extract it. This is critical for clinical accuracy.

IMPORTANT: The text is a real clinical record. It does NOT contain placeholder names like '张三', '李四', '李明' or example symptoms like '牙痛', '龋齿'. Extract ONLY the actual data present. The text may contain multiple patients - extract information for EACH patient separately.

You are an expert knowledge graph builder specializing in extracting entities and relationships from oral clinical medical records.

Your task is to extract structured clinical information from dental medical records and return them in a structured JSON format.

ENTITY TYPES (use only these for oral clinical content):
- Patient: The individual receiving dental treatment (extract name from '姓名：' field)
- PatientId: Patient identifier (extract from '病历号：' field)
- Demographics: Patient demographic information (extract from '年龄：', '性别：', '职业：' fields)
- ChiefComplaint: Main complaint of the patient
- PresentIllness: Present illness events/course
- PastHistory: Past medical history
- FamilyHistory: Family medical history
- SocialHistory: Social history
- Symptom: Patient's subjective complaints and objective clinical findings
- Sign: Clinical signs observed during examination
- Diagnosis: Professional medical diagnosis
- Medication: Medications with dosage/frequency/route
- Procedure: Medical procedures/surgeries
- LabTest: Laboratory test items
- LabValue: Laboratory test values/units
- Imaging: Imaging examination items
- Allergies: Allergies to medications or substances
- Treatment: Medical treatments
- Vitals: Vital signs
- Duration: Time duration
- TemporalExpression: Temporal expressions

RELATIONSHIP TYPES (use only these for oral clinical content):
- HAS_DIAGNOSIS: Patient → Diagnosis (patient has a diagnosis)
- DIAGNOSIS_HAS_SYMPTOM: Diagnosis → Symptom (diagnosis includes symptoms)
- SYMPTOM_OF: Symptom → Diagnosis (symptom belongs to a diagnosis)
- MEDICATION_TREAT_FOR: Medication → Diagnosis (medication treats a diagnosis)
- MEDICATION_HAS_DOSE: Medication → Dose (medication has dosage information)
- LABTEST_HAS_VALUE: LabTest → LabValue (lab test has result value)
- PROCEDURE_PERFORMED_ON: Procedure → BodyPart/Diagnosis (procedure performed on a body part or diagnosis)
- ALLERGY_TO: Patient → Allergen (patient has allergy to allergen)
- FAMILY_HISTORY_OF: Patient → Diagnosis (patient has family history of diagnosis)
- CHIEF_COMPLAINT: Patient → Symptom (main complaint of the patient)
- MEDICAL_ADVICE: Patient → Treatment (medical advice for the patient)
- PROCEDURE_USES_MATERIAL: Procedure → Material (treatment procedure uses material)
- MATERIAL_HAS_COMPONENT: Material → Component (material contains component)
- PROCEDURE_PERFORMED_BY: Procedure → Doctor (procedure performed by doctor)
- PROCEDURE_AIMS_TO_ACHIEVE: Procedure → Goal/Target (procedure aims to achieve goal)
- PATIENT_HAS_OCCUPATION: Patient → Occupation (patient has occupation)
- PATIENT_IS_FIRST_VISIT: Patient → FirstVisitStatus (patient is first visit)

RELATIONSHIP CREATION RULES:
- Use ONLY the relationship types listed above. Do not use entity types as relationship types.
- Create relationships only between entities that have been extracted from the text.
- If no clear relationships exist between extracted entities, leave the relationships array empty.
- Do not invent relationships. Only create relationships that are explicitly implied by the text structure (e.g., patient has a diagnosis, symptom belongs to diagnosis).

EXTRACTION GUIDELINES:
1. Extract EXACT values as they appear in the Chinese text. Do not translate or modify.
2. Look for field labels like '姓名：', '病历号：', '年龄：', '性别：', '职业：', '首次就诊：', '使用材料：' and extract the values that follow them.
3. Extract ALL demographic fields present: age, gender, occupation, first visit status. If the text contains multiple patients, extract information for EACH patient.
4. For example (format only, extract actual values from text): 
   - '姓名：[患者姓名]' → extract '[患者姓名]' as Patient entity
   - '病历号：[病历号]' → extract '[病历号]' as PatientId entity
   - '年龄：[年龄]' → extract '[年龄]' as Demographics entity
   - '性别：[性别]' → extract '[性别]' as Demographics entity
   - '职业：[职业]' → extract '[职业]' as Demographics entity
   - '首次就诊：[首次就诊状态]' → extract '[首次就诊状态]' as Demographics entity
5. Only extract entities that are explicitly stated in the text. Do not invent any names, symptoms, diagnoses, or treatments.
6. If no entities are found, return empty arrays.
7. Create relationships only between entities that have been extracted.

SPECIAL INSTRUCTION FOR SHORT TEXTS: If the text contains only demographic information (patient ID, name, age, gender, occupation, first visit), extract only those entities and leave the relationships array empty. Do not invent symptoms, diagnoses, or treatments.

OUTPUT FORMAT:
Return a JSON object with the following structure:
{
  "entities": [
    {
      "name": "exact entity name from text",
      "type": "entity type from the list above",
      "description": "brief description based on text (optional)"
    }
  ],
  "relationships": [
    {
      "source": "source entity name",
      "target": "target entity name",
      "type": "relationship type from the list above",
      "description": "brief description (optional)"
    }
  ]
}

REMEMBER:
- Extract ONLY from the user-provided text below.
- Do not use any examples or information from this prompt.
- If unsure, do not extract.
- Verify every entity name appears verbatim in the text."""
        
        # 用户提示，提供要提取的文本
        human_prompt = """Extract entities and relationships from the oral clinical medical record below:

{text}

Return the extraction result in JSON format. Remember to extract ONLY from the text above, not from the example."""

        # 创建并返回聊天提示模板
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=base_prompt),  # 系统消息
            HumanMessagePromptTemplate.from_template(human_prompt)      # 用户消息
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

    # 验证实体是否出现在原始文本中
    def _validate_entity_against_text(self, entity_data: Dict[str, Any], text: str) -> bool:
        """验证实体名称是否出现在原始文本中，防止幻觉"""
        name = entity_data.get('name', '').strip()
        if not name:
            return False
        
        # 常见幻觉关键词列表
        hallucination_keywords = [
            '李明', '张三', '李四', '王五', '赵六', '刘七', '陈八', '杨九', '周十'
        ]
        
        # 检查是否为常见幻觉关键词
        for keyword in hallucination_keywords:
            if keyword in name:
                logging.warning(f"实体名称包含幻觉关键词 '{keyword}': '{name}'")
                return False
        
        # 简单检查：实体名称是否作为子字符串出现在文本中
        # 注意：文本可能包含标点符号，实体名称可能被部分匹配
        # 我们进行宽松的检查：移除多余空格后检查
        normalized_name = ' '.join(name.split())
        normalized_text = ' '.join(text.split())
        
        if normalized_name.lower() in normalized_text.lower():
            return True
        
        # 如果名称包含标点符号（如"牙齿11, 12, 21, 22"），拆分为单个检查
        # 对于牙齿编号等复合实体，允许部分匹配
        if ',' in normalized_name or '，' in normalized_name:
            # 尝试拆分
            import re
            parts = re.split(r'[,，]\s*', normalized_name)
            for part in parts:
                if part.strip() and part.strip().lower() in normalized_text.lower():
                    return True
        
        # 特殊处理：对于牙齿编号如"11, 12, 21, 22"，可能在文本中以"牙齿11, 12, 21, 22"形式出现
        # 检查去除"牙齿"前缀后的匹配
        if normalized_name.replace('牙齿', '').strip().lower() in normalized_text.lower():
            return True
        
        # 检查去除常见前缀后的匹配（如"牙齿"、"牙位"）
        prefixes = ['牙齿', '牙位', '牙', 'tooth', 'teeth']
        for prefix in prefixes:
            if normalized_name.startswith(prefix):
                stripped = normalized_name[len(prefix):].strip()
                if stripped and stripped.lower() in normalized_text.lower():
                    return True
        
        logging.warning(f"实体名称未在文本中找到: '{name}' in text (前100字符): {normalized_text[:100]}...")
        return False

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
                # 调试日志：记录原始响应
                logging.debug(f"LLM原始响应长度: {len(content)}")
                if content:
                    logging.debug(f"LLM原始响应预览 (前500字符): {content[:500]}")
                else:
                    logging.warning("LLM返回空响应")
                
                # 清理JSON响应内容
                cleaned_content = self.clean_json_response(content)
                logging.debug(f"清理后的响应: {cleaned_content}")
                content = cleaned_content
                
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
                    # 验证实体数据基本字段
                    if not self._validate_entity_data(cleaned_entity):
                        logging.warning(f"跳过无效实体数据（基本验证失败）: {cleaned_entity}")
                        continue
                    # 验证实体是否出现在文本中（防幻觉）
                    if not self._validate_entity_against_text(cleaned_entity, text):
                        logging.warning(f"跳过可能幻觉实体（未在文本中找到）: {cleaned_entity}")
                        continue
                    cleaned_entities.append(cleaned_entity)
                
                # 清理关系数据
                cleaned_relationships = []
                # 构建有效实体名称集合，用于关系验证
                valid_entity_names = {entity['name'] for entity in cleaned_entities}
                for rel in result_data.get("relationships", []):
                    cleaned_rel = clean_relationship_data(rel)
                    # 验证关系数据基本字段
                    if not self._validate_relationship_data(cleaned_rel):
                        logging.warning(f"跳过无效关系数据（基本验证失败）: {cleaned_rel}")
                        continue
                    # 验证源实体和目标实体是否为有效实体
                    source_name = cleaned_rel.get('source', '').strip()
                    target_name = cleaned_rel.get('target', '').strip()
                    if source_name not in valid_entity_names:
                        logging.warning(f"跳过关系数据（源实体未在有效实体中找到）: {cleaned_rel}")
                        continue
                    if target_name not in valid_entity_names:
                        logging.warning(f"跳过关系数据（目标实体未在有效实体中找到）: {cleaned_rel}")
                        continue
                    # 检查关系类型是否为预定义类型（可选）
                    # 暂时跳过此检查
                    cleaned_relationships.append(cleaned_rel)
                
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
        original_length = len(content)
        content = content.strip()
        
        # 处理包含<think>标签的响应
        if "<think>" in content:
            # 移除<think>和</think>标签，以及标签内的内容
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
            # 去除可能的空白字符
            content = content.strip()
            logging.debug(f"清理后移除<think>标签，内容长度: {len(content)}")
        
        # 如果包含```json标记，则提取标记内的内容
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
            logging.debug(f"提取```json标记内内容，内容长度: {len(content)}")
        # 如果包含```标记，则提取标记内的内容
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            logging.debug(f"提取```标记内内容，内容长度: {len(content)}")
        
        # 寻找JSON数据的开始位置 - 找到第一个'{'字符
        json_start = content.find('{')
        if json_start == -1:
            # 没有找到JSON数据的开始位置，返回空JSON
            logging.warning(f"未找到JSON起始括号'{{'，原始内容长度: {original_length}，清理后内容: '{content[:100]}...'")
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
            logging.warning(f"未找到匹配的结束括号'}}'，括号计数: {brace_count}，内容: '{content[:100]}...'")
            return "{}"
        
        # 提取有效的JSON部分
        content = content[:json_end]
        
        # 验证提取的内容是否为有效的JSON
        try:
            import json
            json.loads(content)
            logging.debug(f"成功提取有效JSON，长度: {len(content)}")
            return content
        except json.JSONDecodeError:
            # 如果不是有效的JSON，返回空JSON
            logging.warning(f"提取的内容不是有效JSON，内容: '{content[:100]}...'")
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
