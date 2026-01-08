import argparse
import sys
import logging
from datetime import datetime
from pathlib import Path

from config import Config
from src.data_loader import DataLoader
from src.neo4j_manager import Neo4jManager
from src.entity_extractor import EntityExtractor
from src.graph_builder import GraphBuilder


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
    logging.info("=" * 60 + "\n")


def build_graph(config: Config, clear_db: bool = True):
    logging.info("Initializing components...")
    
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
    
    entity_extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx
    )
    
    graph_builder = GraphBuilder(
        data_loader=data_loader,
        neo4j_manager=neo4j_manager,
        entity_extractor=entity_extractor,
        max_retries=config.processing.max_retries,
        retry_delay=config.processing.retry_delay
    )
    
    logging.info("Connecting to Neo4j...")
    neo4j_manager.connect()
    
    try:
        logging.info("Building knowledge graph...")
        stats = graph_builder.build_graph(
            show_progress=True, 
            clear_database=clear_db,
            batch_process_size=config.processing.batch_process_size
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
        description="Build a knowledge graph from unstructured text using LangChain, Ollama, and Neo4j"
    )
    
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the knowledge graph"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Query information about a specific entity"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show graph summary"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        help="Export graph to JSON file"
    )
    
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear the database before building"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=".env",
        help="Path to environment configuration file (default: .env)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (default: kg_build_YYYYMMDD_HHMMSS.log)"
    )
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # 配置日志
    log_file = configure_logging(args.log_file)
    logging.info(f"Logging to file: {log_file}")
    
    print_banner()
    
    try:
        config = Config.from_env(args.config)
        config.validate_config()
        print_config(config)
        
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
                num_ctx=config.ollama.num_ctx
            )
            
            graph_builder = GraphBuilder(
                data_loader=data_loader,
                neo4j_manager=neo4j_manager,
                entity_extractor=entity_extractor,
                max_retries=config.processing.max_retries,
                retry_delay=config.processing.retry_delay
            )
        
        if args.build:
            build_graph(config, clear_db=not args.no_clear)
        
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
