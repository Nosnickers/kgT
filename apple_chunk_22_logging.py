#!/usr/bin/env python3
"""
测试脚本：专门用于记录chunk_id 22的LLM输入输出过程
用于分析实体提取幻觉问题
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent))

from config import Config
from src.entity_extractor import EntityExtractor, ExtractionResult


class ChunkLogger:
    """专门用于记录chunk处理过程的日志器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建基于时间的日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"chunk_22_analysis_{timestamp}.log"
        
        # 配置日志
        self.logger = logging.getLogger("chunk_analysis")
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有handler
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 文件handler
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 详细格式
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"开始记录chunk分析过程，日志文件: {self.log_file}")
    
    def log_section(self, title: str, content: Any = None):
        """记录一个分析章节"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"【{title}】")
        self.logger.info(f"{'='*80}")
        if content is not None:
            if isinstance(content, str):
                self.logger.info(content)
            else:
                self.logger.info(json.dumps(content, ensure_ascii=False, indent=2))
    
    def log_prompt(self, prompt_type: str, content: str):
        """记录提示词内容"""
        self.logger.info(f"\n{'-'*60}")
        self.logger.info(f"【{prompt_type}】:")
        self.logger.info(f"{'-'*60}")
        self.logger.info(content)
        self.logger.info(f"{'-'*60}")
    
    def log_response(self, response_type: str, content: str):
        """记录响应内容"""
        self.logger.info(f"\n{'-'*60}")
        self.logger.info(f"【{response_type}】:")
        self.logger.info(f"{'-'*60}")
        self.logger.info(content[:2000] + "..." if len(content) > 2000 else content)
        self.logger.info(f"{'-'*60}")
    
    def info(self, msg: str):
        """代理方法：委托给内部logger的info方法"""
        self.logger.info(msg)
    
    def error(self, msg: str):
        """代理方法：委托给内部logger的error方法"""
        self.logger.error(msg)
    
    def warning(self, msg: str):
        """代理方法：委托给内部logger的warning方法"""
        self.logger.warning(msg)
    
    def debug(self, msg: str):
        """代理方法：委托给内部logger的debug方法"""
        self.logger.debug(msg)


class DetailedEntityExtractor(EntityExtractor):
    """扩展的实体提取器，增加详细日志记录"""
    
    def __init__(self, base_url: str, model: str, temperature: float = 0.1, 
                 num_ctx: int = 4096, deep_thought_mode: bool = False, 
                 logger: Optional[ChunkLogger] = None):
        super().__init__(base_url, model, temperature, num_ctx, deep_thought_mode)
        self.logger = logger
    
    def extract_with_logging(self, text: str, chunk_id: int, max_retries: int = 3) -> ExtractionResult:
        """带详细日志记录的提取方法"""
        
        if self.logger:
            self.logger.log_section(f"开始处理Chunk ID: {chunk_id}")
            self.logger.log_section("原始文本内容", text)
        
        for attempt in range(max_retries):
            try:
                if self.logger:
                    self.logger.log_section(f"第 {attempt + 1} 次提取尝试")
                
                # 创建提取提示
                prompt = self.create_extraction_prompt()
                
                # 获取系统提示词
                system_prompt = prompt.messages[0].content if prompt.messages else ""
                user_prompt = prompt.messages[1].content.format(text=text) if len(prompt.messages) > 1 else text
                
                if self.logger:
                    self.logger.log_prompt("系统提示词", system_prompt)
                    self.logger.log_prompt("用户提示词", user_prompt)
                
                # 格式化提示消息
                formatted_prompt = prompt.format_messages(text=text)
                
                # 调用LLM进行提取
                if self.logger:
                    self.logger.info("正在调用LLM...")
                
                response = self.llm.invoke(formatted_prompt)
                raw_content = response.content
                
                if self.logger:
                    self.logger.log_response("LLM原始响应", raw_content)
                
                # 清理JSON响应内容
                cleaned_content = self.clean_json_response(raw_content)
                
                if self.logger:
                    self.logger.log_response("清理后的JSON响应", cleaned_content)
                
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
                    if self._validate_entity_data(cleaned_entity):
                        cleaned_entities.append(cleaned_entity)
                        if self.logger:
                            self.logger.info(f"✓ 有效实体: {cleaned_entity}")
                    else:
                        if self.logger:
                            self.logger.warning(f"✗ 无效实体被跳过: {cleaned_entity}")
                
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
                
                if self.logger:
                    self.logger.log_section("最终提取结果", {
                        "实体数量": len(cleaned_entities),
                        "关系数量": len(cleaned_relationships),
                        "实体列表": cleaned_entities,
                        "关系列表": cleaned_relationships
                    })
                
                # 转换为实体对象列表
                entities = []
                for entity in cleaned_entities:
                    try:
                        entities.append(self._create_extracted_entity(entity, chunk_id))
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"创建实体对象失败: {e}, 数据: {entity}")
                
                # 转换为关系对象列表
                relationships = []
                for rel in cleaned_relationships:
                    try:
                        relationships.append(self._create_extracted_relationship(rel, chunk_id))
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"创建关系对象失败: {e}, 数据: {rel}")
                
                return ExtractionResult(entities=entities, relationships=relationships)
                
            except json.JSONDecodeError as e:
                if self.logger:
                    self.logger.error(f"第 {attempt + 1} 次尝试JSON解析错误: {e}")
                    self.logger.error(f"响应内容: {cleaned_content}")
                if attempt == max_retries - 1:
                    if self.logger:
                        self.logger.error("所有重试均失败，返回空结果")
                    return ExtractionResult(entities=[], relationships=[])
            except Exception as e:
                if self.logger:
                    self.logger.error(f"第 {attempt + 1} 次尝试提取错误: {e}")
                if attempt == max_retries - 1:
                    if self.logger:
                        self.logger.error("所有重试均失败，返回空结果")
                    return ExtractionResult(entities=[], relationships=[])
        
        if self.logger:
            self.logger.error(f"所有 {max_retries} 次尝试均失败")
        return ExtractionResult(entities=[], relationships=[])
    
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
    
    def _create_extracted_entity(self, entity_data: Dict[str, Any], chunk_id: int):
        """创建提取的实体对象"""
        from src.entity_extractor import ExtractedEntity
        return ExtractedEntity(
            name=entity_data['name'],
            type=entity_data['type'],
            description=entity_data.get('description', ''),
            chunk_id=chunk_id
        )
    
    def _create_extracted_relationship(self, rel_data: Dict[str, Any], chunk_id: int):
        """创建提取的关系对象"""
        from src.entity_extractor import ExtractedRelationship
        return ExtractedRelationship(
            source=rel_data['source'],
            target=rel_data['target'],
            type=rel_data['type'],
            description=rel_data.get('description', ''),
            chunk_id=chunk_id
        )


def read_chunk_from_csv(csv_file: str, chunk_id: int) -> Optional[Dict[str, Any]]:
    """从CSV文件中读取指定chunk_id的内容"""
    import csv
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row.get('chunk_id', -1)) == chunk_id:
                    return row
    except Exception as e:
        print(f"读取CSV文件错误: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(
        description="分析特定chunk_id的LLM提取过程，记录详细日志"
    )
    
    parser.add_argument(
        "--chunk-id",
        type=int,
        default=22,
        help="要分析的chunk ID (默认: 22)"
    )
    
    parser.add_argument(
        "--csv-file",
        type=str,
        default="kg_build_20260110_182346.csv",
        help="CSV文件路径 (默认: kg_build_20260110_182346.csv)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="配置文件路径 (默认: .env)"
    )
    
    parser.add_argument(
        "--log-dir",
        type=str,
        default="logs",
        help="日志文件目录 (默认: logs)"
    )
    
    parser.add_argument(
        "--deep-thought",
        action="store_true",
        help="启用深度思考模式"
    )
    
    args = parser.parse_args()
    
    # 初始化日志记录器
    logger = ChunkLogger(args.log_dir)
    
    try:
        # 读取配置
        logger.log_section("加载配置")
        config = Config.from_env(args.config)
        config.validate_config()
        logger.logger.info(f"配置加载成功: Ollama模型={config.ollama.model}")
        
        # 读取CSV文件
        logger.log_section(f"读取CSV文件: {args.csv_file}")
        csv_path = Path(args.csv_file)
        if not csv_path.exists():
            logger.logger.error(f"CSV文件不存在: {csv_path}")
            return
        
        chunk_data = read_chunk_from_csv(str(csv_path), args.chunk_id)
        if not chunk_data:
            logger.logger.error(f"未找到chunk_id {args.chunk_id}")
            return
        
        logger.log_section(f"找到Chunk ID {args.chunk_id}的数据", chunk_data)
        
        # 提取文本内容
        chunk_text = chunk_data.get('content', '')
        word_count = chunk_data.get('word_count', 0)
        title = chunk_data.get('title', '')
        
        logger.log_section("Chunk详细信息", {
            "标题": title,
            "词数": word_count,
            "文本长度": len(chunk_text),
            "文本预览": chunk_text[:500] + "..." if len(chunk_text) > 500 else chunk_text
        })
        
        # 创建带日志记录的实体提取器
        logger.log_section("初始化实体提取器")
        extractor = DetailedEntityExtractor(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
            num_ctx=config.ollama.num_ctx,
            deep_thought_mode=args.deep_thought or config.ollama.deep_thought_mode,
            logger=logger
        )
        
        # 执行提取
        logger.log_section("开始实体提取过程")
        result = extractor.extract_with_logging(chunk_text, args.chunk_id)
        
        # 最终结果总结
        logger.log_section("提取结果总结", {
            "提取到的实体数量": len(result.entities),
            "提取到的关系数量": len(result.relationships),
            "实体详情": [
                {"名称": e.name, "类型": e.type, "描述": e.description}
                for e in result.entities
            ],
            "关系详情": [
                {"源": r.source, "目标": r.target, "类型": r.type, "描述": r.description}
                for r in result.relationships
            ]
        })
        
        logger.log_section("分析完成", f"详细日志已保存至: {logger.log_file}")
        
    except Exception as e:
        logger.logger.error(f"分析过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()