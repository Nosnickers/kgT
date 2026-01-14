import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from src.text_generator import TextGenerator
from src.embedding_manager import EmbeddingManager
from src.vector_store import VectorStore
from src.retriever import Retriever
from src.qa_engine import QAEngine


def configure_logging(log_file: str = None):
    """配置日志记录"""
    # 如果没有指定日志文件，生成基于时间的文件名
    if not log_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"qa_cli_{timestamp}.log"
    
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


def build_index(args):
    """构建向量索引"""
    logging.info("开始构建向量索引...")
    
    try:
        from config import Config
        from src.neo4j_manager import Neo4jManager
        
        config = Config.from_env(args.config)
        neo4j_manager = Neo4jManager(
            uri=config.neo4j.uri,
            username=config.neo4j.username,
            password=config.neo4j.password
        )
        neo4j_manager.connect()
        
        if args.csv_file:
            csv_file = args.csv_file
        else:
            csv_file = config.data.file_path.replace('.json', '.csv')
        if not Path(csv_file).exists():
            logging.error(f"CSV文件不存在: {csv_file}")
            return False
        
        text_generator = TextGenerator(neo4j_manager, csv_file)
        success = text_generator.generate_all_texts(args.output)
        
        if not success:
            logging.error("文本描述生成失败")
            return False
        
        logging.info("开始生成嵌入向量...")
        
        import json
        with open(args.output, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entities = data.get('entities', [])
        relationships = data.get('relationships', [])
        
        embedding_manager = EmbeddingManager(
            model_name=args.embedding_model,
            cache_embeddings=not args.no_cache
        )
        
        logging.info(f"为 {len(entities)} 个实体生成嵌入...")
        entities_with_embeddings = embedding_manager.embed_entities(
            entities,
            text_field='text_description'
        )
        
        logging.info(f"为 {len(relationships)} 个关系生成嵌入...")
        relationships_with_embeddings = embedding_manager.embed_relationships(
            relationships,
            text_field='relationship_text'
        )
        
        logging.info("开始初始化向量存储...")
        vector_store = VectorStore(persist_directory=args.vector_db)
        
        logging.info("开始添加实体到向量存储...")
        added_entities = vector_store.add_entities(entities_with_embeddings)
        
        logging.info("开始添加关系到向量存储...")
        added_relationships = vector_store.add_relationships(relationships_with_embeddings)
        
        logging.info("持久化向量数据...")
        vector_store.persist()
        
        logging.info(f"向量索引构建完成！")
        logging.info(f"  - 实体总数: {vector_store.get_entity_count()}")
        logging.info(f"  - 关系总数: {vector_store.get_relationship_count()}")
        
        neo4j_manager.close()
        return True
        
    except Exception as e:
        logging.error(f"构建向量索引失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def interactive_mode(args):
    """交互式问答模式"""
    logging.info("启动交互式问答模式...")
    
    try:
        from config import Config
        config = Config.from_env(args.config)
        
        use_cache = not args.no_cache and not args.use_embedding_cache
        embedding_manager = EmbeddingManager(
            model_name=args.embedding_model,
            cache_embeddings=use_cache
        )
        
        vector_store = VectorStore(persist_directory=args.vector_db)
        retriever = Retriever(vector_store, embedding_manager)
        
        qa_engine = QAEngine(
            retriever=retriever,
            llm_base_url=args.llm_base_url,
            llm_model=args.llm_model,
            llm_temperature=args.llm_temperature,
            llm_num_ctx=args.llm_num_ctx,
            deep_thought_mode=args.deep_thought
        )
        
        print("\n" + "="*60)
        print("知识图谱问答系统（交互模式）")
        print("="*60)
        print("输入 'exit' 或 'quit' 退出")
        print("输入 'clear' 清空对话历史")
        print("输入 'help' 查看帮助信息")
        print("="*60 + "\n")
        
        while True:
            try:
                query = input("请输入您的问题：").strip()
                
                if query.lower() in ['exit', 'quit']:
                    print("再见！")
                    break
                elif query.lower() == 'clear':
                    qa_engine.clear_conversation()
                    print("对话历史已清空")
                elif query.lower() == 'help':
                    print_help()
                elif not query:
                    continue
                
                print(f"\n正在分析问题...")
                result = qa_engine.answer(
                    query=query,
                    retrieval_mode=args.retrieval_mode,
                    top_k=args.top_k,
                    entity_types=args.entity_types.split(',') if args.entity_types else None,
                    relationship_types=args.relationship_types.split(',') if args.relationship_types else None,
                    min_similarity=args.min_similarity,
                    use_conversation=True
                )
                
                print(f"\n答案：")
                print(result['answer'])
                
                if result.get('sources'):
                    print(f"\n来源（{result['retrieval_count']} 个）：")
                    for i, source in enumerate(result['sources'], 1):
                        source_type = source.get('type', '')
                        if source_type == 'entity':
                            print(f"  {i}. 实体: {source.get('name', '')} ({source.get('type', '')})")
                            print(f"     相似度: {source.get('similarity', 0):.2f}")
                            print(f"     描述: {source.get('text_description', '')}")
                        elif source_type == 'relationship':
                            print(f"  {i}. 关系: {source.get('source', '')} {source.get('type', '')} {source.get('target', '')}")
                            print(f"     相似度: {source.get('similarity', 0):.2f}")
                            print(f"     描述: {source.get('relationship_text', '')}")
                
            except KeyboardInterrupt:
                print("\n\n程序已中断")
                break
            except Exception as e:
                logging.error(f"处理查询失败: {e}")
                print(f"抱歉，处理您的问题时出错了：{e}")
    
    except Exception as e:
        logging.error(f"启动交互模式失败: {e}")
        import traceback
        traceback.print_exc()


def query_mode(args):
    """单次问答模式"""
    logging.info(f"执行单次问答：{args.query}")
    
    try:
        from config import Config
        config = Config.from_env(args.config)
        
        use_cache = not args.no_cache and not args.use_embedding_cache
        embedding_manager = EmbeddingManager(
            model_name=args.embedding_model,
            cache_embeddings=use_cache
        )
        
        vector_store = VectorStore(persist_directory=args.vector_db)
        retriever = Retriever(vector_store, embedding_manager)
        
        qa_engine = QAEngine(
            retriever=retriever,
            llm_base_url=args.llm_base_url,
            llm_model=args.llm_model,
            llm_temperature=args.llm_temperature,
            llm_num_ctx=args.llm_num_ctx,
            deep_thought_mode=args.deep_thought
        )
        
        result = qa_engine.answer(
            query=args.query,
            retrieval_mode=args.retrieval_mode,
            top_k=args.top_k,
            entity_types=args.entity_types.split(',') if args.entity_types else None,
            relationship_types=args.relationship_types.split(',') if args.relationship_types else None,
            min_similarity=args.min_similarity,
            use_conversation=False
        )
        
        print(f"\n问题：{args.query}")
        print(f"答案：{result['answer']}")
        
        if result.get('sources'):
            print(f"\n来源（{result['retrieval_count']} 个）：")
            for i, source in enumerate(result['sources'], 1):
                source_type = source.get('type', '')
                if source_type == 'entity':
                    print(f"  {i}. 实体: {source.get('name', '')} ({source.get('type', '')})")
                    print(f"     相似度: {source.get('similarity', 0):.2f}")
                    print(f"     描述: {source.get('text_description', '')}")
                elif source_type == 'relationship':
                    print(f"  {i}. 关系: {source.get('source', '')} {source.get('type', '')} {source.get('target', '')}")
                    print(f"     相似度: {source.get('similarity', 0):.2f}")
                    print(f"     描述: {source.get('relationship_text', '')}")
        
        if result.get('error'):
            logging.error(f"问答失败：{result['error']}")
            sys.exit(1)
        
    except Exception as e:
        logging.error(f"执行问答失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_help():
    """打印帮助信息"""
    help_text = """
可用命令：
  help          - 显示此帮助信息
  clear         - 清空对话历史
  exit/quit    - 退出程序

检索模式说明：
  entity        - 仅检索实体
  relationship    - 仅检索关系
  hybrid         - 混合检索（实体+关系）
  contextual      - 上下文增强检索

示例问题：
  - Who is Alex Mercer?
  - What organization does Alex Mercer work for?
  - What is Paranormal Military Squad?
  - What is the relationship between Alex Mercer and Paranormal Military Squad?
  - Describe the briefing room
    """
    print(help_text)


def main():
    configure_logging()
    
    parser = argparse.ArgumentParser(
        description="""
知识图谱问答系统 - 基于向量检索和LLM的智能问答应用

该系统将Neo4j知识图谱中的实体和关系文本化，
并使用向量检索技术实现智能问答功能。
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    build_parser = subparsers.add_parser('build-index', help='构建向量索引')
    build_parser.add_argument('--config', type=str, default='.env', help='配置文件路径（默认：.env）')
    build_parser.add_argument('--csv-file', type=str, help='CSV文件路径（包含chunk数据）')
    build_parser.add_argument('--output', type=str, default='oral_kg_index.json', help='文本描述输出文件（默认：oral_kg_index.json）')
    build_parser.add_argument('--embedding-model', type=str, default='all-MiniLM-L6-v2', help='嵌入模型名称或本地路径（默认：all-MiniLM-L6-v2）')
    build_parser.add_argument('--vector-db', type=str, default='./chroma_db', help='向量数据库路径（默认：./chroma_db）')
    build_parser.add_argument('--no-cache', action='store_true', help='禁用嵌入缓存')
    
    interactive_parser = subparsers.add_parser('interactive', help='交互式问答模式')
    interactive_parser.add_argument('--config', type=str, default='.env', help='配置文件路径（默认：.env）')
    interactive_parser.add_argument('--embedding-model', type=str, default='all-MiniLM-L6-v2', help='嵌入模型名称或本地路径（默认：all-MiniLM-L6-v2）')
    interactive_parser.add_argument('--vector-db', type=str, default='./chroma_db', help='向量数据库路径（默认：./chroma_db）')
    interactive_parser.add_argument('--llm-base-url', type=str, default='http://localhost:11434', help='LLM基础URL（默认：http://localhost:11434）')
    interactive_parser.add_argument('--llm-model', type=str, default='deepseek-r1:8b', help='LLM模型名称（默认：deepseek-r1:8b）')
    interactive_parser.add_argument('--llm-temperature', type=float, default=0.7, help='LLM温度参数（默认：0.7）')
    interactive_parser.add_argument('--llm-num-ctx', type=int, default=4096, help='LLM上下文窗口大小（默认：4096）')
    interactive_parser.add_argument('--deep-thought', action='store_true', help='启用深度思考模式（默认：False）')
    interactive_parser.add_argument('--retrieval-mode', type=str, default='hybrid', choices=['entity', 'relationship', 'hybrid', 'contextual'], help='检索模式（默认：hybrid）')
    interactive_parser.add_argument('--top-k', type=int, default=5, help='返回的最相似结果数量（默认：5）')
    interactive_parser.add_argument('--entity-types', type=str, help='过滤的实体类型（逗号分隔）')
    interactive_parser.add_argument('--relationship-types', type=str, help='过滤的关系类型（逗号分隔）')
    interactive_parser.add_argument('--min-similarity', type=float, default=0.0, help='最小相似度阈值（默认：0.0）')
    interactive_parser.add_argument('--use-embedding-cache', action='store_true', default=True, help='使用嵌入缓存（默认：True）')
    interactive_parser.add_argument('--no-cache', action='store_true', help='禁用嵌入缓存')
    
    query_parser = subparsers.add_parser('query', help='单次问答')
    query_parser.add_argument('query', type=str, help='要查询的问题')
    query_parser.add_argument('--config', type=str, default='.env', help='配置文件路径（默认：.env）')
    query_parser.add_argument('--embedding-model', type=str, default='all-MiniLM-L6-v2', help='嵌入模型名称或本地路径（默认：all-MiniLM-L6-v2）')
    query_parser.add_argument('--vector-db', type=str, default='./chroma_db', help='向量数据库路径（默认：./chroma_db）')
    query_parser.add_argument('--llm-base-url', type=str, default='http://localhost:11434', help='LLM基础URL（默认：http://localhost:11434）')
    query_parser.add_argument('--llm-model', type=str, default='deepseek-r1:8b', help='LLM模型名称（默认：deepseek-r1:8b）')
    query_parser.add_argument('--llm-temperature', type=float, default=0.7, help='LLM温度参数（默认：0.7）')
    query_parser.add_argument('--llm-num-ctx', type=int, default=4096, help='LLM上下文窗口大小（默认：4096）')
    query_parser.add_argument('--deep-thought', action='store_true', help='启用深度思考模式（默认：False）')
    query_parser.add_argument('--retrieval-mode', type=str, default='hybrid', choices=['entity', 'relationship', 'hybrid', 'contextual'], help='检索模式（默认：hybrid）')
    query_parser.add_argument('--top-k', type=int, default=5, help='返回的最相似结果数量（默认：5）')
    query_parser.add_argument('--entity-types', type=str, help='过滤的实体类型（逗号分隔）')
    query_parser.add_argument('--relationship-types', type=str, help='过滤的关系类型（逗号分隔）')
    query_parser.add_argument('--min-similarity', type=float, default=0.0, help='最小相似度阈值（默认：0.0）')
    query_parser.add_argument('--use-embedding-cache', action='store_true', default=True, help='使用嵌入缓存（默认：True）')
    query_parser.add_argument('--no-cache', action='store_true', help='禁用嵌入缓存')
    
    args = parser.parse_args()
    
    if args.command == 'build-index':
        success = build_index(args)
        sys.exit(0 if success else 1)
    elif args.command == 'interactive':
        interactive_mode(args)
    elif args.command == 'query':
        query_mode(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
