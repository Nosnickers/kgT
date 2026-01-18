import argparse
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from config import Config
from src.data_loader import DataLoader
from src.neo4j_manager import Neo4jManager
from src.entity_extractor import EntityExtractor
from src.graph_builder import GraphBuilder
from src.llm_client import create_llm_client


def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║          Knowledge Graph Builder from Unstructured Text         ║
    ║                                                               ║
    ║              Using LangChain + Ollama + Neo4j                ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def configure_logging(log_file: str = None):
    """配置日志记录"""
    # 如果没有指定日志文件，生成基于时间的文件名
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"kg_build_{timestamp}.log"
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的handler
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 文件handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加handler
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return log_file

def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║          Knowledge Graph Builder from Unstructured Text         ║
    ║                                                               ║
    ║              Using LangChain + Ollama + Neo4j                ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    logging.info(banner)


def print_config(config: Config):
    logging.info("\n" + "=" * 60)
    logging.info("Configuration:")
    logging.info("=" * 60)
    logging.info(f"Neo4j URI: {config.neo4j.uri}")
    logging.info(f"Neo4j Username: {config.neo4j.username}")
    logging.info(f"Ollama Base URL: {config.ollama.base_url}")
    logging.info(f"Ollama Model: {config.ollama.model}")
    logging.info(f"Data File: {config.data.file_path}")
    logging.info(f"Chunk Size: {config.data.chunk_size}")
    logging.info(f"Chunk Overlap: {config.data.chunk_overlap}")
    logging.info(f"Batch Process Size: {config.processing.batch_process_size}")
    logging.info(f"Enable Entity Linking: {config.processing.enable_entity_linking}")
    if config.processing.entity_types_to_link:
        logging.info(f"Entity Types to Link: {', '.join(config.processing.entity_types_to_link)}")
    logging.info(f"Enable LLM Logging: {config.processing.enable_llm_logging}")
    logging.info("=" * 60 + "\n")


def build_graph(config: Config, clear_db: bool = True, csv_output_prefix: str = None, 
                enable_llm_logging: bool = False, enable_entity_linking: bool = False,
                entity_types_to_link: Optional[List[str]] = None):
    logging.info("Initializing components...")
    
    # 如果启用LLM日志记录，创建ChunkLogger
    logger = None
    if enable_llm_logging:
        from apple_chunk_22_logging import ChunkLogger
        logger = ChunkLogger(log_dir="logs")
        logging.info("LLM详细日志记录已启用")
    
    data_loader = DataLoader(
        file_path=config.data.file_path,
        chunk_size=config.data.chunk_size,
        chunk_overlap=config.data.chunk_overlap
    )
    
    neo4j_manager = Neo4jManager(
        uri=config.neo4j.uri,
        username=config.neo4j.username,
        password=config.neo4j.password
    )
    
    # 创建统一的LLM客户端
    from src.llm_client import LLMConfig, LLMClient
    if config.enable_online_llm and config.online_llm:
        # 在线LLM配置
        llm_config = LLMConfig(
            enable_online=True,
            api_key=config.online_llm.api_key,
            base_url=config.online_llm.base_url,
            model=config.online_llm.model,
            temperature=config.online_llm.temperature,
            max_tokens=config.online_llm.max_tokens,
            timeout=config.online_llm.timeout
        )
    else:
        # Ollama配置
        llm_config = LLMConfig(
            enable_online=False,
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
            num_ctx=config.ollama.num_ctx,
            deep_thought_mode=config.ollama.deep_thought_mode
        )
    llm_client = LLMClient(llm_config)
    
    entity_extractor = EntityExtractor(
        base_url=config.ollama.base_url,  # 向后兼容，但会被llm_client覆盖
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode,
        llm_client=llm_client
    )
    
    graph_builder = GraphBuilder(
        data_loader=data_loader,
        neo4j_manager=neo4j_manager,
        entity_extractor=entity_extractor,
        max_retries=config.processing.max_retries,
        retry_delay=config.processing.retry_delay,
        logger=logger,  # 传递logger给GraphBuilder
        enable_entity_linking=enable_entity_linking,
        entity_types_to_link=entity_types_to_link
    )
    
    logging.info("Connecting to Neo4j...")
    neo4j_manager.connect()
    
    try:
        logging.info("Building knowledge graph...")
        stats = graph_builder.build_graph(
            show_progress=True, 
            clear_database=clear_db,
            batch_process_size=config.processing.batch_process_size,
            csv_output_prefix=csv_output_prefix
        )
        
        logging.info("\n" + "=" * 60)
        logging.info("Build Summary:")
        logging.info("=" * 60)
        logging.info(f"Chunks processed: {stats['chunks_processed']}")
        logging.info(f"Entities extracted: {stats['entities_extracted']}")
        logging.info(f"Relationships extracted: {stats['relationships_extracted']}")
        logging.info(f"Entities created in Neo4j: {stats['entities_created']}")
        logging.info(f"Relationships created in Neo4j: {stats['relationships_created']}")
        
        extraction_stats = stats.get('extraction_stats', {})
        if extraction_stats:
            logging.info(f"\nAverage entities per chunk: {extraction_stats.get('avg_entities_per_chunk', 0):.2f}")
            logging.info(f"Average relationships per chunk: {extraction_stats.get('avg_relationships_per_chunk', 0):.2f}")
            
            entity_types = extraction_stats.get('entity_type_distribution', {})
            if entity_types:
                logging.info("\nEntity Type Distribution:")
                for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                    logging.info(f"  {entity_type}: {count}")
            
            rel_types = extraction_stats.get('relationship_type_distribution', {})
            if rel_types:
                logging.info("\nRelationship Type Distribution:")
                for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
                    logging.info(f"  {rel_type}: {count}")
        
        logging.info("=" * 60 + "\n")
        
        return graph_builder
        
    except Exception as e:
        logging.error(f"Error building graph: {e}")
        raise
    finally:
        neo4j_manager.close()


def query_graph(graph_builder: GraphBuilder, entity_name: str):
    logging.info(f"\nQuerying information about: {entity_name}")
    logging.info("=" * 60)
    
    info = graph_builder.get_entity_info(entity_name)
    logging.info(f"Total relationships: {info['total_relationships']}")
    
    if info['relationships']:
        logging.info("\nRelationships:")
        for rel in info['relationships'][:10]:
            source = rel.get('source', {})
            r = rel.get('r', {})
            target = rel.get('other', {})
            logging.info(f"  {source.get('name', 'Unknown')} -[{r.get('type', 'UNKNOWN')}]-> {target.get('name', 'Unknown')}")
    
    logging.info("\n" + "=" * 60)


def show_graph_summary(graph_builder: GraphBuilder):
    logging.info("\nKnowledge Graph Summary:")
    logging.info("=" * 60)
    
    summary = graph_builder.get_graph_summary()
    logging.info(f"Total entities: {summary['total_entities']}")
    logging.info(f"Total relationships: {summary['total_relationships']}")
    
    logging.info("\nEntity Types:")
    for entity_type, count in sorted(summary['entity_types'].items(), key=lambda x: x[1], reverse=True):
        logging.info(f"  {entity_type}: {count}")
    
    logging.info("\nRelationship Types:")
    for rel_type, count in sorted(summary['relationship_types'].items(), key=lambda x: x[1], reverse=True):
        logging.info(f"  {rel_type}: {count}")
    
    logging.info("=" * 60 + "\n")


def export_graph(graph_builder: GraphBuilder, output_path: str):
    logging.info(f"\nExporting graph to: {output_path}")
    success = graph_builder.export_to_json(output_path)
    if success:
        logging.info("Export completed successfully!")
    else:
        logging.error("Export failed!")


def main():
    parser = argparse.ArgumentParser(
        description="""
Knowledge Graph Builder from Unstructured Text

This tool builds a knowledge graph from unstructured text using LangChain, Ollama, and Neo4j.
It extracts entities and relationships from text chunks and stores them in a Neo4j database.

Features:
- Extract entities (characters, locations, organizations, etc.) from fictional narratives
- Identify relationships between entities
- Support for deep thought mode for improved extraction accuracy
- Detailed LLM logging for debugging and analysis
- Batch processing with configurable chunk size and overlap
- Export to CSV and JSON formats

Examples:
  # Build the knowledge graph with default settings
  python main.py --build --config .env

  # Build with detailed LLM logging (includes deep thought process)
  python main.py --build --config .env --enable-llm-logging

  # Build without clearing the database
  python main.py --build --config .env --no-clear

  # Query information about a specific entity
  python main.py --query "Alex Mercer" --config .env

  # Show graph summary
  python main.py --summary --config .env

  # Export graph to JSON
  python main.py --export output.json --config .env
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the knowledge graph from the configured data file"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Query information about a specific entity (e.g., 'Alex Mercer')"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show a summary of the knowledge graph (entity counts, relationship counts, type distributions)"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="Export the knowledge graph to a JSON file at the specified path"
    )
    
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear the database before building (useful for incremental updates)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="Path to environment configuration file (default: .env). The file should contain settings for Neo4j, Ollama, and data processing."
    )
    
    parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Path to data file to process (overrides DATA_FILE in config file). Supports both JSON and Markdown formats. Examples: data/chief_complaint_1.json or data/oralRecords.md"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to the main log file (default: kg_build_YYYYMMDD_HHMMSS.log). This log contains general build progress and statistics."
    )
    
    parser.add_argument(
        "--enable-llm-logging",
        action="store_true",
        help="""
Enable detailed LLM logging for entity extraction.

When enabled, this creates a separate detailed log file in the 'logs' directory that records:
- System prompts sent to the LLM
- User prompts with text content
- Raw LLM responses (including deep thought process if enabled)
- Cleaned JSON responses
- Parsed JSON data
- Data validation and cleaning steps
- Final extraction results with entity and relationship details

This is useful for:
- Debugging entity extraction issues
- Analyzing LLM behavior and response patterns
- Understanding how deep thought mode affects extraction
- Verifying that entities and relationships are extracted correctly

The detailed log file will be named: chunk_analysis_YYYYMMDD_HHMMSS.log
        """
    )
    
    parser.add_argument(
        "--enable-entity-linking",
        action="store_true",
        help="""
Enable entity linking to existing entities in the knowledge graph.

When enabled, the system will query the Neo4j database for existing entities 
before extraction, and provide this context to the LLM. This helps:

- Avoid duplicate creation of existing entities (e.g., patient IDs, patients)
- Establish relationships between newly extracted entities and existing ones
- Support incremental knowledge graph building

Entity types to link can be configured via --entity-types-to-link or 
ENTITY_TYPES_TO_LINK environment variable.
        """
    )
    
    parser.add_argument(
        "--entity-types-to-link",
        type=str,
        default=None,
        help="""
Comma-separated list of entity types to link to existing entities in the graph.

Examples:
  --entity-types-to-link "Patient,PatientId"
  --entity-types-to-link "Patient,PatientId,Diagnosis,Symptom"

If not specified, defaults to "Patient,PatientId". Only entity types 
specified here will be queried from the existing graph.
        """
    )
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # 配置日志
    log_file = configure_logging(args.log_file)
    logging.info(f"Logging to file: {log_file}")
    logging.info(f"Command line arguments: data_file={args.data_file}, build={args.build}, config={args.config}")
    
    # 提取日志文件名前缀，用于csv输出
    import os
    csv_output_prefix = os.path.splitext(log_file)[0] if log_file else None
    
    print_banner()
    
    try:
        config = Config.from_env(args.config, data_file_override=args.data_file)
        config.validate_config()
        print_config(config)
        
        # 配置合并逻辑：命令行参数 > 环境变量 > 默认值
        enable_entity_linking = args.enable_entity_linking or config.processing.enable_entity_linking
        enable_llm_logging = args.enable_llm_logging or config.processing.enable_llm_logging
        entity_types_to_link = None
        
        # 处理实体类型列表
        if args.entity_types_to_link:
            # 命令行参数优先级最高
            entity_types_to_link = [t.strip() for t in args.entity_types_to_link.split(",") if t.strip()]
            logging.info(f"使用命令行指定的实体类型链接列表: {entity_types_to_link}")
        elif config.processing.entity_types_to_link:
            # 其次使用环境变量配置
            entity_types_to_link = config.processing.entity_types_to_link
            logging.info(f"使用环境变量配置的实体类型链接列表: {entity_types_to_link}")
        else:
            # 默认值
            entity_types_to_link = ["Patient", "PatientId"]
            logging.info(f"使用默认实体类型链接列表: {entity_types_to_link}")
        
        graph_builder = None
        
        if args.build or args.query or args.summary or args.export:
            neo4j_manager = Neo4jManager(
                uri=config.neo4j.uri,
                username=config.neo4j.username,
                password=config.neo4j.password
            )
            neo4j_manager.connect()
            
            data_loader = DataLoader(
                file_path=config.data.file_path,
                chunk_size=config.data.chunk_size,
                chunk_overlap=config.data.chunk_overlap
            )
            
            entity_extractor = EntityExtractor(
                base_url=config.ollama.base_url,
                model=config.ollama.model,
                temperature=config.ollama.temperature,
                num_ctx=config.ollama.num_ctx,
                deep_thought_mode=config.ollama.deep_thought_mode
            )
            
            graph_builder = GraphBuilder(
                data_loader=data_loader,
                neo4j_manager=neo4j_manager,
                entity_extractor=entity_extractor,
                max_retries=config.processing.max_retries,
                retry_delay=config.processing.retry_delay,
                logger=None,  # main函数中不传递logger，避免重复日志
                enable_entity_linking=enable_entity_linking,
                entity_types_to_link=entity_types_to_link
            )
        
        if args.build:
            build_graph(config, clear_db=not args.no_clear, csv_output_prefix=csv_output_prefix, 
                        enable_llm_logging=enable_llm_logging,
                        enable_entity_linking=enable_entity_linking,
                        entity_types_to_link=entity_types_to_link)
        
        if args.query:
            if not graph_builder:
                logging.error("Error: Please build the graph first using --build")
                return
            query_graph(graph_builder, args.query)
        
        if args.summary:
            if not graph_builder:
                logging.error("Error: Please build the graph first using --build")
                return
            show_graph_summary(graph_builder)
        
        if args.export:
            if not graph_builder:
                logging.error("Error: Please build the graph first using --build")
                return
            export_graph(graph_builder, args.export)
        
        if graph_builder:
            graph_builder.neo4j_manager.close()
        
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        logging.error("\nPlease make sure:")
        logging.error("1. .env file exists with correct configuration")
        logging.error("2. NEO4J_PASSWORD is set")
        logging.error("3. Data file exists at the specified path")
        sys.exit(1)
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
