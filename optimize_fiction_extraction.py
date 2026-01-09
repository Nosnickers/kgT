#!/usr/bin/env python3
"""
优化虚构文本的实体关系提取准确性
"""

import json
import logging
import sys
import os
from typing import List, Dict, Any

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from entity_extractor import EntityExtractor, ExtractionResult

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def analyze_extraction_results(extraction_result: ExtractionResult):
    """分析提取结果的优化空间"""
    logging.info("=== 分析提取结果优化空间 ===")
    
    # 1. 检查实体重复
    entity_names = {}
    for entity in extraction_result.entities:
        if entity.name in entity_names:
            logging.warning(f"重复实体: {entity.name}")
            entity_names[entity.name] += 1
        else:
            entity_names[entity.name] = 1
    
    # 2. 检查关系重复和方向
    relationship_pairs = {}
    for rel in extraction_result.relationships:
        key = f"{rel.source}→{rel.target}"
        if key in relationship_pairs:
            logging.warning(f"重复关系对: {key} (类型: {rel.type})")
            relationship_pairs[key].append(rel.type)
        else:
            relationship_pairs[key] = [rel.type]
    
    # 3. 检查关系语义一致性
    for rel in extraction_result.relationships:
        # 检查WORKS_FOR和PART_OF的关系语义
        if rel.type in ['WORKS_FOR', 'PART_OF']:
            # 这两个关系类型语义相近，可能需要合并或选择更合适的
            logging.info(f"语义相近关系: {rel.source} --[{rel.type}]--> {rel.target}")
    
    # 4. 实体类型分布分析
    type_distribution = {}
    for entity in extraction_result.entities:
        type_distribution[entity.type] = type_distribution.get(entity.type, 0) + 1
    
    logging.info("实体类型分布:")
    for entity_type, count in type_distribution.items():
        logging.info(f"  {entity_type}: {count}")
    
    # 5. 关系类型分布分析
    rel_type_distribution = {}
    for rel in extraction_result.relationships:
        rel_type_distribution[rel.type] = rel_type_distribution.get(rel.type, 0) + 1
    
    logging.info("关系类型分布:")
    for rel_type, count in rel_type_distribution.items():
        logging.info(f"  {rel_type}: {count}")

def optimize_extraction_prompt():
    """优化提示模板"""
    logging.info("=== 优化提示模板 ===")
    
    # 创建优化后的提示模板
    optimized_prompt = """You are an expert knowledge graph builder specializing in extracting entities and relationships from fictional stories, novels, and narrative texts.

Your task is to extract characters, locations, organizations, and their relationships from the given fictional text and return them in a structured JSON format.

ENTITY TYPES (use only these for fictional content):
- Character: People, agents, protagonists, antagonists (e.g., Alex Mercer, Taylor Cruz, Jordan Hayes)
- Organization: Groups, teams, agencies, factions (e.g., Paranormal Military Squad, secret organizations)
- Location: Places, settings, environments (e.g., briefing room, Dulce base, laboratory)
- Technology: Devices, equipment, scientific tools (e.g., monitors, alien technology, comms system)
- Concept: Abstract ideas, themes, missions (e.g., Operation: Dulce, anomalies, protocols)
- Object: Physical items, artifacts, props (e.g., folder, table, screens)
- Event: Occurrences, incidents, plot points (e.g., briefing, transmission, crash site)

RELATIONSHIP TYPES (use only these for fictional content):
- WORKS_FOR: Character → Organization (a character works for an organization)
- LOCATED_AT: Character/Organization → Location (someone/something is located at a place)
- USES: Character → Technology/Object (a character uses technology or objects)
- INTERACTS_WITH: Character → Character (characters interact with each other)
- PART_OF: Character → Organization (a character is part of an organization)
- INVOLVED_IN: Character → Event (a character is involved in an event)
- RELATED_TO: Any entity → Any entity (general relationship when specific type doesn't fit)
- LEADS: Character → Organization/Team (a character leads a group)
- OWNS: Character → Object/Technology (a character owns something)
- PARTICIPATES_IN: Character → Event (a character participates in an event)

EXTRACTION RULES FOR FICTIONAL CONTENT:
1. Extract characters by their full names when available (e.g., "Alex Mercer" not just "Alex")
2. Focus on main characters and important supporting characters
3. Extract locations that are significant to the plot
4. Extract organizations and groups that play a role in the story
5. Extract relationships that show character interactions and plot development
6. **Description Rules:**
   - For characters: describe their role, personality traits, or actions in the story
   - For organizations: describe their purpose or role in the narrative
   - For locations: describe their significance or atmosphere in the story
   - **NEVER invent or add information that is not present in the text**
   - Keep descriptions concise and directly based on the text
7. **Context Rules:**
   - Focus on entities that are relevant to the story's plot and characters
   - Extract relationships that show character dynamics and plot connections
   - Pay attention to dialogue and character interactions
8. **OPTIMIZATION RULES:**
   - Avoid duplicate entities: if an entity appears multiple times, extract it only once
   - Avoid redundant relationships: choose the most specific relationship type
   - Standardize entity names: use consistent naming (e.g., "Paranormal Military Squad" not "PMS")
   - Ensure relationship direction: make sure source→target direction makes semantic sense
   - Prioritize specific relationships over generic ones (e.g., WORKS_FOR over RELATED_TO)
9. Do not hallucinate entities or relationships not present in the text
10. Return results in JSON object with the following OUTPUT FORMAT structure (replace the placeholder values with actual extracted entities and relationships):

{
  "entities": [
    {
      "name": "actual_entity_name_from_text",
      "type": "appropriate_entity_type",
      "description": "actual_description_from_text"
    }
  ],
  "relationships": [
    {
      "source": "actual_source_entity_name",
      "target": "actual_target_entity_name",
      "type": "appropriate_relationship_type",
      "description": "actual_relationship_description"
    }
  ]
}

IMPORTANT: DO NOT use the placeholder values shown above. Extract actual entity names, types, and descriptions from the provided text.
"""
    
    logging.info("✓ 优化后的提示模板已创建")
    return optimized_prompt

def create_enhanced_extractor():
    """创建增强的实体提取器"""
    logging.info("=== 创建增强的实体提取器 ===")
    
    # 创建标准的实体提取器
    extractor = EntityExtractor(
        base_url="http://localhost:11434",
        model="mistral:7b-instruct-v0.3-q4_0",
        temperature=0.1,
        num_ctx=4096,
        deep_thought_mode=True
    )
    
    # 添加后处理功能
    class EnhancedEntityExtractor:
        def __init__(self, extractor):
            self.extractor = extractor
        
        def extract_with_optimization(self, text: str) -> ExtractionResult:
            """增强的提取方法，包含后处理优化"""
            # 1. 执行标准提取
            result = self.extractor.extract(text)
            
            # 2. 后处理优化
            result = self.post_process_result(result)
            
            return result
        
        def post_process_result(self, result: ExtractionResult) -> ExtractionResult:
            """后处理优化提取结果"""
            # 去重实体
            unique_entities = self.deduplicate_entities(result.entities)
            
            # 优化关系
            optimized_relationships = self.optimize_relationships(result.relationships)
            
            # 标准化实体名称
            standardized_entities = self.standardize_entity_names(unique_entities)
            
            return ExtractionResult(
                entities=standardized_entities,
                relationships=optimized_relationships
            )
        
        def deduplicate_entities(self, entities: List) -> List:
            """去重实体"""
            seen = set()
            unique_entities = []
            
            for entity in entities:
                # 使用名称和类型作为唯一标识
                key = (entity.name.lower(), entity.type)
                if key not in seen:
                    seen.add(key)
                    unique_entities.append(entity)
                else:
                    logging.info(f"去重实体: {entity.name} ({entity.type})")
            
            return unique_entities
        
        def optimize_relationships(self, relationships: List) -> List:
            """优化关系"""
            # 去除重复的关系对
            seen_pairs = set()
            optimized = []
            
            for rel in relationships:
                pair_key = (rel.source.lower(), rel.target.lower())
                
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    optimized.append(rel)
                else:
                    logging.info(f"去重关系: {rel.source} → {rel.target} ({rel.type})")
            
            return optimized
        
        def standardize_entity_names(self, entities: List) -> List:
            """标准化实体名称"""
            standardized = []
            
            for entity in entities:
                # 移除多余的括号和缩写
                standardized_name = entity.name
                
                # 如果名称包含括号，尝试提取完整名称
                if '(' in standardized_name and ')' in standardized_name:
                    # 例如: "Paranormal Military Squad (PMS)" → "Paranormal Military Squad"
                    standardized_name = standardized_name.split('(')[0].strip()
                
                # 更新实体名称
                if standardized_name != entity.name:
                    logging.info(f"标准化实体名称: '{entity.name}' → '{standardized_name}'")
                    entity.name = standardized_name
                
                standardized.append(entity)
            
            return standardized
    
    return EnhancedEntityExtractor(extractor)

def test_enhanced_extraction():
    """测试增强的提取功能"""
    logging.info("=== 测试增强的提取功能 ===")
    
    # 加载测试文本
    sample_text = """=== 章节 1 ===
# Operation: Dulce

## Chapter 1

The thrumming of monitors cast a stark contrast to the rigid silence enveloping the group. Agent Alex Mercer, unfailingly determined on paper, seemed dwarfed by the enormity of the sterile briefing room where Paranormal Military Squad's elite convened. With dulled eyes, he scanned the projectors outlining their impending odyssey into Operation: Dulce.

"This is it, Mercer," a voice cut through the hum. Taylor Cruz, the squad's tactical lead, stood beside him. "Dulce isn't just another mission. It's the culmination of everything we've trained for."

Alex nodded, his gaze fixed on the schematics of the underground facility. "The alien technology they've recovered... it could change everything."

"Exactly," Taylor replied. "That's why we need you. Your unique abilities make you our best chance."

The Paranormal Military Squad (PMS) had been preparing for this moment for years. Their base in New York City served as the command center, but the real action would happen in Dulce, New Mexico."""
    
    # 创建增强提取器
    enhanced_extractor = create_enhanced_extractor()
    
    # 执行增强提取
    result = enhanced_extractor.extract_with_optimization(sample_text)
    
    # 分析结果
    analyze_extraction_results(result)
    
    # 输出结果
    logging.info("=== 增强提取结果 ===")
    logging.info(f"提取到 {len(result.entities)} 个实体:")
    for i, entity in enumerate(result.entities):
        logging.info(f"  {i+1}. {entity.name} ({entity.type}): {entity.description}")
    
    logging.info(f"提取到 {len(result.relationships)} 个关系:")
    for i, rel in enumerate(result.relationships):
        logging.info(f"  {i+1}. {rel.source} --[{rel.type}]--> {rel.target}: {rel.description}")
    
    # 保存结果
    with open('enhanced_fiction_extraction.json', 'w', encoding='utf-8') as f:
        json.dump({
            'entities': [entity.model_dump() for entity in result.entities],
            'relationships': [rel.model_dump() for rel in result.relationships]
        }, f, ensure_ascii=False, indent=2)
    
    logging.info("增强提取结果已保存到 enhanced_fiction_extraction.json")

def main():
    """主函数"""
    setup_logging()
    
    logging.info("=== 虚构文本实体关系提取优化开始 ===")
    
    # 优化提示模板
    optimized_prompt = optimize_extraction_prompt()
    
    # 测试增强的提取功能
    test_enhanced_extraction()
    
    logging.info("=== 优化完成 ===")

if __name__ == "__main__":
    main()