import json
import logging
from datetime import datetime
from pathlib import Path

from config import Config
from src.entity_extractor import EntityExtractor
from apple_chunk_22_logging import ChunkLogger


def configure_logging(log_file: str = None):
    """配置日志记录"""
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"chief_complaint_validation_{timestamp}.log"
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return log_file


def load_medical_record(file_path: str) -> dict:
    """加载病历文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_medical_record(record: dict) -> str:
    """将病历字典格式化为文本"""
    text_parts = []
    
    if '主诉' in record:
        text_parts.append(f"主诉：{record['主诉']}")
    
    if '现病史' in record:
        text_parts.append(f"现病史：{record['现病史']}")
    
    if '既往史' in record:
        text_parts.append(f"既往史：{record['既往史']}")
    
    if '检查' in record:
        text_parts.append("检查：")
        for item in record['检查']:
            if item.get('内容'):
                text_parts.append(f"  - {item['内容']}")
    
    if '辅助检查' in record:
        text_parts.append("辅助检查：")
        for item in record['辅助检查']:
            if item.get('内容'):
                text_parts.append(f"  - {item['内容']}")
    
    if '诊断' in record:
        text_parts.append("诊断：")
        for item in record['诊断']:
            if item.get('内容'):
                text_parts.append(f"  - {item['内容']}")
    
    if '治疗方案' in record:
        text_parts.append("治疗方案：")
        for item in record['治疗方案']:
            if item.get('内容'):
                text_parts.append(f"  - {item['内容']}")
    
    if '处置' in record:
        text_parts.append("处置：")
        for item in record['处置']:
            if item.get('内容'):
                text_parts.append(f"  - {item['内容']}")
    
    if '医嘱' in record:
        text_parts.append(f"医嘱：{record['医嘱']}")
    
    return '\n'.join(text_parts)


def analyze_extraction_result(result, record_text: str):
    """分析提取结果，特别关注主诉关系"""
    logging.info("\n" + "=" * 80)
    logging.info("提取结果分析")
    logging.info("=" * 80)
    
    logging.info(f"\n原始病历文本：\n{record_text}")
    
    logging.info(f"\n提取的实体数量：{len(result.entities)}")
    logging.info("实体列表：")
    for i, entity in enumerate(result.entities, 1):
        logging.info(f"  {i}. 名称: {entity.name}, 类型: {entity.type}, 描述: {entity.description}")
    
    logging.info(f"\n提取的关系数量：{len(result.relationships)}")
    logging.info("关系列表：")
    for i, rel in enumerate(result.relationships, 1):
        logging.info(f"  {i}. {rel.source} -[{rel.type}]-> {rel.target}, 描述: {rel.description}")
    
    logging.info("\n" + "=" * 80)
    logging.info("主诉关系检查")
    logging.info("=" * 80)
    
    chief_complaint_rels = [rel for rel in result.relationships if rel.type == "CHIEF_COMPLAINT"]
    
    if chief_complaint_rels:
        logging.info(f"✓ 成功提取到 {len(chief_complaint_rels)} 个主诉关系：")
        for rel in chief_complaint_rels:
            logging.info(f"  - {rel.source} -[CHIEF_COMPLAINT]-> {rel.target}")
            logging.info(f"    描述: {rel.description}")
    else:
        logging.error("✗ 未提取到任何主诉关系（CHIEF_COMPLAINT）")
        logging.error("可能的原因：")
        logging.error("  1. LLM未能识别病历中的'主诉'字段")
        logging.error("  2. 主诉内容被提取为实体，但未创建关系")
        logging.error("  3. 提示词需要优化")
    
    symptom_entities = [entity for entity in result.entities if entity.type == "Symptom"]
    if symptom_entities:
        logging.info(f"\n提取的症状实体（{len(symptom_entities)}个）：")
        for entity in symptom_entities:
            logging.info(f"  - {entity.name}: {entity.description}")
    else:
        logging.warning("\n未提取到任何症状实体（Symptom）")
    
    visit_event_entities = [entity for entity in result.entities if entity.type == "VisitEvent"]
    if visit_event_entities:
        logging.info(f"\n提取的就诊事件实体（{len(visit_event_entities)}个）：")
        for entity in visit_event_entities:
            logging.info(f"  - {entity.name}: {entity.description}")
    else:
        logging.warning("\n未提取到任何就诊事件实体（VisitEvent）")


def validate_chief_complaint_extraction(
    config: Config,
    record_file: str,
    enable_detailed_logging: bool = True
):
    """验证主诉提取功能"""
    
    log_file = configure_logging()
    logging.info(f"日志文件: {log_file}")
    
    logging.info("\n" + "=" * 80)
    logging.info("主诉提取验证工具")
    logging.info("=" * 80)
    
    logging.info(f"\n配置信息:")
    logging.info(f"  Ollama Base URL: {config.ollama.base_url}")
    logging.info(f"  Ollama Model: {config.ollama.model}")
    logging.info(f"  Temperature: {config.ollama.temperature}")
    logging.info(f"  Num Ctx: {config.ollama.num_ctx}")
    
    logging.info(f"\n病历文件: {record_file}")
    
    chunk_logger = None
    if enable_detailed_logging:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chunk_logger = ChunkLogger(log_dir="logs")
        chunk_logger.log_file = f"chief_complaint_detailed_{timestamp}.log"
        logging.info(f"详细日志文件: {chunk_logger.log_file}")
    
    entity_extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    record = load_medical_record(record_file)
    record_text = format_medical_record(record)
    
    logging.info(f"\n格式化后的病历文本（{len(record_text)} 字符）：")
    logging.info("-" * 80)
    logging.info(record_text)
    logging.info("-" * 80)
    
    if chunk_logger:
        chunk_logger.log_section("验证主诉提取")
        chunk_logger.log_section("病历文本", record_text)
    
    logging.info("\n开始提取实体和关系...")
    
    prompt = entity_extractor.create_extraction_prompt()
    
    if chunk_logger:
        system_prompt = prompt.messages[0].content if prompt.messages else ""
        user_prompt = prompt.messages[1].content.format(text=record_text) if len(prompt.messages) > 1 else record_text
        
        chunk_logger.log_section("系统提示词", system_prompt)
        chunk_logger.log_section("用户提示词", user_prompt)
    
    formatted_prompt = prompt.format_messages(text=record_text)
    
    if chunk_logger:
        chunk_logger.info("正在调用LLM...")
    
    response = entity_extractor.llm.invoke(formatted_prompt)
    raw_content = response.content
    
    if chunk_logger:
        chunk_logger.log_section("LLM原始响应", raw_content)
    
    cleaned_content = entity_extractor.clean_json_response(raw_content)
    
    if chunk_logger:
        chunk_logger.log_section("清理后的JSON响应", cleaned_content)
    
    result_data = json.loads(cleaned_content)
    
    if chunk_logger:
        chunk_logger.log_section("解析后的JSON数据", result_data)
    
    result = entity_extractor.extract(record_text)
    
    if chunk_logger:
        chunk_logger.log_section("最终提取结果", {
            "实体数量": len(result.entities),
            "关系数量": len(result.relationships),
            "实体详情": [
                {"名称": e.name, "类型": e.type, "描述": e.description}
                for e in result.entities
            ],
            "关系详情": [
                {"源": r.source, "目标": r.target, "类型": r.type, "描述": r.description}
                for r in result.relationships
            ]
        })
    
    analyze_extraction_result(result, record_text)
    
    logging.info(f"\n验证完成！详细日志已保存到: {log_file}")
    if chunk_logger:
        logging.info(f"LLM详细日志已保存到: {chunk_logger.log_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="验证主诉（CHIEF_COMPLAINT）提取功能"
    )
    
    parser.add_argument(
        "--record",
        type=str,
        required=True,
        help="病历文件路径（如 data/chief_complaint_1.json）"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="配置文件路径（默认：.env）"
    )
    
    parser.add_argument(
        "--no-detailed-logging",
        action="store_true",
        help="禁用详细的LLM日志记录"
    )
    
    args = parser.parse_args()
    
    try:
        config = Config.from_env(args.config)
        config.validate_config()
        
        validate_chief_complaint_extraction(
            config=config,
            record_file=args.record,
            enable_detailed_logging=not args.no_detailed_logging
        )
        
    except Exception as e:
        logging.error(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
