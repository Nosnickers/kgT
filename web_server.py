import logging
import sys
import os
import json
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.embedding_manager import EmbeddingManager
from src.vector_store import VectorStore
from src.retriever import Retriever
from src.qa_engine import QAEngine

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

embedding_manager = None
vector_store = None
retriever = None
qa_engine = None

def initialize_components():
    global embedding_manager, vector_store, retriever, qa_engine
    
    try:
        logger.info("初始化嵌入管理器...")
        embedding_manager = EmbeddingManager(
            model_name='all-MiniLM-L6-v2',
            cache_embeddings=True
        )
        
        logger.info("初始化向量存储...")
        vector_store = VectorStore(persist_directory='./chroma_db')
        
        logger.info("初始化检索器...")
        retriever = Retriever(vector_store, embedding_manager)
        
        logger.info("初始化问答引擎...")
        qa_engine = QAEngine(
            retriever=retriever,
            llm_base_url='http://localhost:11434',
            llm_model='deepseek-r1:8b',
            llm_temperature=0.7,
            llm_num_ctx=4096,
            deep_thought_mode=True
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
        
        logger.info(f"收到查询: {query}, 模式: {retrieval_mode}, top_k: {top_k}")
        
        if not qa_engine:
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
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        traceback.print_exc()
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
