import argparse
import sys
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


def print_config(config: Config):
    print("\n" + "=" * 60)
    print("Configuration:")
    print("=" * 60)
    print(f"Neo4j URI: {config.neo4j.uri}")
    print(f"Neo4j Username: {config.neo4j.username}")
    print(f"Ollama Base URL: {config.ollama.base_url}")
    print(f"Ollama Model: {config.ollama.model}")
    print(f"Data File: {config.data.file_path}")
    print(f"Chunk Size: {config.data.chunk_size}")
    print(f"Chunk Overlap: {config.data.chunk_overlap}")
    print("=" * 60 + "\n")


def build_graph(config: Config, clear_db: bool = True):
    print("Initializing components...")
    
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
    
    print("Connecting to Neo4j...")
    neo4j_manager.connect()
    
    try:
        print("Building knowledge graph...")
        stats = graph_builder.build_graph(show_progress=True, clear_database=clear_db)
        
        print("\n" + "=" * 60)
        print("Build Summary:")
        print("=" * 60)
        print(f"Chunks processed: {stats['chunks_processed']}")
        print(f"Entities extracted: {stats['entities_extracted']}")
        print(f"Relationships extracted: {stats['relationships_extracted']}")
        print(f"Entities created in Neo4j: {stats['entities_created']}")
        print(f"Relationships created in Neo4j: {stats['relationships_created']}")
        
        extraction_stats = stats.get('extraction_stats', {})
        if extraction_stats:
            print(f"\nAverage entities per chunk: {extraction_stats.get('avg_entities_per_chunk', 0):.2f}")
            print(f"Average relationships per chunk: {extraction_stats.get('avg_relationships_per_chunk', 0):.2f}")
            
            entity_types = extraction_stats.get('entity_type_distribution', {})
            if entity_types:
                print("\nEntity Type Distribution:")
                for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {entity_type}: {count}")
            
            rel_types = extraction_stats.get('relationship_type_distribution', {})
            if rel_types:
                print("\nRelationship Type Distribution:")
                for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {rel_type}: {count}")
        
        print("=" * 60 + "\n")
        
        return graph_builder
        
    except Exception as e:
        print(f"Error building graph: {e}")
        raise
    finally:
        neo4j_manager.close()


def query_graph(graph_builder: GraphBuilder, entity_name: str):
    print(f"\nQuerying information about: {entity_name}")
    print("=" * 60)
    
    info = graph_builder.get_entity_info(entity_name)
    print(f"Total relationships: {info['total_relationships']}")
    
    if info['relationships']:
        print("\nRelationships:")
        for rel in info['relationships'][:10]:
            source = rel.get('source', {})
            r = rel.get('r', {})
            target = rel.get('other', {})
            print(f"  {source.get('name', 'Unknown')} -[{r.get('type', 'UNKNOWN')}]-> {target.get('name', 'Unknown')}")
    
    print("\n" + "=" * 60)


def show_graph_summary(graph_builder: GraphBuilder):
    print("\nKnowledge Graph Summary:")
    print("=" * 60)
    
    summary = graph_builder.get_graph_summary()
    print(f"Total entities: {summary['total_entities']}")
    print(f"Total relationships: {summary['total_relationships']}")
    
    print("\nEntity Types:")
    for entity_type, count in sorted(summary['entity_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {entity_type}: {count}")
    
    print("\nRelationship Types:")
    for rel_type, count in sorted(summary['relationship_types'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count}")
    
    print("=" * 60 + "\n")


def export_graph(graph_builder: GraphBuilder, output_path: str):
    print(f"\nExporting graph to: {output_path}")
    success = graph_builder.export_to_json(output_path)
    if success:
        print("Export completed successfully!")
    else:
        print("Export failed!")


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
    
    args = parser.parse_args()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
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
                print("Error: Please build the graph first using --build")
                return
            query_graph(graph_builder, args.query)
        
        if args.summary:
            if not graph_builder:
                print("Error: Please build the graph first using --build")
                return
            show_graph_summary(graph_builder)
        
        if args.export:
            if not graph_builder:
                print("Error: Please build the graph first using --build")
                return
            export_graph(graph_builder, args.export)
        
        if graph_builder:
            graph_builder.neo4j_manager.close()
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease make sure:")
        print("1. .env file exists with correct configuration")
        print("2. NEO4J_PASSWORD is set")
        print("3. Data file exists at the specified path")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
