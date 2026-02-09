import logging
import sys
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from config import Config
from src.embedding_manager import EmbeddingManager
from src.vector_store import VectorStore
from src.retriever import Retriever
from src.qa_engine import QAEngine
from src.llm_client import create_llm_client, LLMConfig, LLMClient

app = Flask(__name__)
CORS(app)

def configure_logging():
    """配置日志记录"""
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = logs_dir / f'web_server_{timestamp}.log'
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logging.info(f"日志系统初始化完成，日志文件: {log_file}")
    return logger

logger = configure_logging()

embedding_manager = None
vector_store = None
retriever = None
qa_engine = None

def initialize_components():
    global embedding_manager, vector_store, retriever, qa_engine
    
    try:
        logger.info("加载配置文件...")
        config = Config.from_env()
        
        logger.info("初始化嵌入管理器...")
        
        embedding_config = config.embedding
        model_name = embedding_config.model_name
        local_model_path = embedding_config.local_model_path
        
        if local_model_path:
            logger.info(f"尝试使用本地模型路径: {local_model_path}")
            local_path = Path(local_model_path)
            if local_path.exists():
                logger.info(f"本地模型路径存在，使用本地模型")
                model_name = str(local_path)
            else:
                logger.warning(f"本地模型路径不存在: {local_model_path}，将使用 Hugging Face Hub 下载模型: {model_name}")
        
        embedding_manager = EmbeddingManager(
            model_name=model_name,
            cache_embeddings=embedding_config.cache_embeddings
        )
        
        logger.info("初始化向量存储...")
        vector_store = VectorStore(persist_directory='./chroma_db')
        
        logger.info("初始化检索器...")
        retriever = Retriever(vector_store, embedding_manager)
        
        logger.info("初始化问答引擎...")
        # 创建统一的LLM客户端
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
        
        qa_engine = QAEngine(
            retriever=retriever,
            llm_base_url=config.ollama.base_url,  # 向后兼容，但会被llm_client覆盖
            llm_model=config.ollama.model,
            llm_temperature=config.ollama.temperature,
            llm_num_ctx=config.ollama.num_ctx,
            deep_thought_mode=config.ollama.deep_thought_mode,
            llm_client=llm_client
        )
        
        logger.info("所有组件初始化完成")
        return True
    except Exception as e:
        logger.error(f"组件初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'components': {
            'embedding_manager': embedding_manager is not None,
            'vector_store': vector_store is not None,
            'retriever': retriever is not None,
            'qa_engine': qa_engine is not None
        }
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        if vector_store:
            entity_count = vector_store.get_entity_count()
            relationship_count = vector_store.get_relationship_count()
            return jsonify({
                'status': 'success',
                'entity_count': entity_count,
                'relationship_count': relationship_count
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '向量存储未初始化'
            }), 500
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/query', methods=['POST'])
def query():
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            logger.warning("收到无效请求：缺少查询参数")
            return jsonify({
                'status': 'error',
                'message': '缺少查询参数'
            }), 400
        
        query = data['query']
        retrieval_mode = data.get('retrieval_mode', 'hybrid')
        top_k = data.get('top_k', 5)
        min_similarity = data.get('min_similarity', 0.0)
        entity_types = data.get('entity_types', [])
        relationship_types = data.get('relationship_types', [])
        use_conversation = data.get('use_conversation', False)
        
        logger.info(f"收到查询请求")
        logger.info(f"  - 问题: {query}")
        logger.info(f"  - 检索模式: {retrieval_mode}")
        logger.info(f"  - Top-K: {top_k}")
        logger.info(f"  - 最小相似度: {min_similarity}")
        logger.info(f"  - 实体类型过滤: {entity_types if entity_types else '无'}")
        logger.info(f"  - 关系类型过滤: {relationship_types if relationship_types else '无'}")
        logger.info(f"  - 使用对话历史: {use_conversation}")
        
        if not qa_engine:
            logger.error("问答引擎未初始化")
            return jsonify({
                'status': 'error',
                'message': '问答引擎未初始化'
            }), 500
        
        result = qa_engine.answer(
            query=query,
            retrieval_mode=retrieval_mode,
            top_k=top_k,
            entity_types=entity_types if entity_types else None,
            relationship_types=relationship_types if relationship_types else None,
            min_similarity=min_similarity,
            use_conversation=use_conversation
        )
        
        if result.get('error'):
            logger.error(f"查询执行失败: {result['error']}")
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 500
        
        logger.info(f"查询成功完成")
        logger.info(f"  - 答案长度: {len(result.get('answer', ''))}")
        logger.info(f"  - 检索来源数量: {result.get('retrieval_count', 0)}")
        
        if result.get('sources'):
            logger.info(f"  - 来源详情:")
            for i, source in enumerate(result['sources'][:3], 1):
                if source.get('type') == 'entity':
                    logger.info(f"    {i}. 实体: {source.get('name')} ({source.get('entity_type')}) - 相似度: {source.get('similarity', 0):.3f}")
                elif source.get('type') == 'relationship':
                    logger.info(f"    {i}. 关系: {source.get('source')} -> {source.get('target')} ({source.get('rel_type')}) - 相似度: {source.get('similarity', 0):.3f}")
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"查询处理异常: {e}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/clear-conversation', methods=['POST'])
def clear_conversation():
    try:
        if qa_engine:
            qa_engine.clear_conversation()
            return jsonify({
                'status': 'success',
                'message': '对话历史已清空'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '问答引擎未初始化'
            }), 500
    except Exception as e:
        logger.error(f"清空对话历史失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/conversation-history', methods=['GET'])
def get_conversation_history():
    try:
        if qa_engine:
            history = qa_engine.get_conversation_history()
            return jsonify({
                'status': 'success',
                'data': history
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '问答引擎未初始化'
            }), 500
    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/data-source', methods=['GET'])
def get_data_source():
    try:
        data_file = Path('data/Dulce.json')
        if not data_file.exists():
            return jsonify({
                'status': 'error',
                'message': '数据源文件不存在'
            }), 404
        
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify({
            'status': 'success',
            'data': data
        })
    except Exception as e:
        logger.error(f"加载数据源失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    if initialize_components():
        logger.info("启动 Web 服务器...")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        logger.error("组件初始化失败，无法启动服务器")
        exit(1)
