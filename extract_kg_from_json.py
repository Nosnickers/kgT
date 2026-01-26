#!/usr/bin/env python3
"""
使用Dulce.json文件提取知识图谱
"""

import sys
import os
import logging
from dotenv import load_dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import DataLoader
from src.neo4j_manager import Neo4jManager
from src.entity_extractor import EntityExtractor
from src.graph_builder import GraphBuilder

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('kg_extraction.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """主函数：从Dulce.json提取知识图谱"""
    print("=== 从Dulce.json提取知识图谱 ===")
    
    # 设置日志
    setup_logging()
    
    # 加载环境变量
    load_dotenv()
    
    # 配置文件路径
    json_file = "data/Dulce.json"
    
    if not os.path.exists(json_file):
        logging.error(f"JSON文件不存在: {json_file}")
        return
    
    try:
        # 1. 创建数据加载器
        logging.info("创建数据加载器...")
        data_loader = DataLoader(json_file, chunk_size=1000, chunk_overlap=100)
        
        # 2. 加载并分块数据
        logging.info("加载并分块JSON数据...")
        chunks = data_loader.load_and_chunk()
        
        logging.info(f"成功加载 {len(chunks)} 个数据块")
        
        # 显示数据统计
        stats = data_loader.get_stats(chunks)
        logging.info(f"数据统计: {stats}")
        
        # 3. 创建Neo4j管理器
        logging.info("创建Neo4j管理器...")
        neo4j_manager = Neo4jManager(
            uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            username=os.getenv('NEO4J_USERNAME', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD', '')
        )
        
        # 4. 创建实体提取器
        logging.info("创建实体提取器...")
        entity_extractor = EntityExtractor(
            model_name="mistral",
            base_url="http://localhost:11434"
        )
        
        # 5. 创建知识图谱构建器
        logging.info("创建知识图谱构建器...")
        graph_builder = GraphBuilder(
            data_loader=data_loader,
            neo4j_manager=neo4j_manager,
            entity_extractor=entity_extractor,
            max_retries=3,
            retry_delay=2
        )
        
        # 6. 构建知识图谱
        logging.info("开始构建知识图谱...")
        
        # 使用已有的chunks，不重新加载数据
        result_stats = graph_builder.build_graph(
            chunks=chunks,
            show_progress=True,
            clear_database=True,
            batch_process_size=5,
            csv_output_prefix="dulce_kg_extraction"
        )
        
        # 7. 输出结果统计
        logging.info("=== 知识图谱提取完成 ===")
        logging.info(f"处理的数据块数量: {result_stats['chunks_processed']}")
        logging.info(f"提取的实体数量: {result_stats['entities_extracted']}")
        logging.info(f"提取的关系数量: {result_stats['relationships_extracted']}")
        logging.info(f"创建的实体数量: {result_stats['entities_created']}")
        logging.info(f"创建的关系数量: {result_stats['relationships_created']}")
        
        # 显示提取统计
        extraction_stats = result_stats['extraction_stats']
        logging.info(f"提取统计: {extraction_stats}")
        
        print("\n✅ 知识图谱提取完成！")
        print(f"📊 结果统计:")
        print(f"   数据块: {result_stats['chunks_processed']}")
        print(f"   实体: {result_stats['entities_created']}")
        print(f"   关系: {result_stats['relationships_created']}")
        
        # 保存CSV文件用于后续分析
        if os.path.exists("dulce_kg_extraction.csv"):
            print(f"📁 数据块已保存到: dulce_kg_extraction.csv")
        
    except Exception as e:
        logging.error(f"知识图谱提取失败: {e}")
        import traceback
        traceback.print_exc()

def test_data_loading():
    """测试数据加载功能"""
    print("\n=== 测试数据加载 ===")
    
    json_file = "data/Dulce.json"
    
    if not os.path.exists(json_file):
        print(f"❌ JSON文件不存在: {json_file}")
        return
    
    try:
        # 创建数据加载器
        data_loader = DataLoader(json_file, chunk_size=1000, chunk_overlap=100)
        
        # 测试文件格式检测
        file_format = data_loader.detect_file_format()
        print(f"文件格式: {file_format}")
        
        # 加载数据
        chunks = data_loader.load_and_chunk()
        print(f"数据块数量: {len(chunks)}")
        
        # 显示统计信息
        stats = data_loader.get_stats(chunks)
        print(f"数据统计: {stats}")
        
        # 显示前3个chunks的信息
        print("\n前3个数据块:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"  Chunk {i+1}: ID={chunk.metadata.get('chunk_id')}, "
                  f"标题='{chunk.metadata.get('title')}', "
                  f"字数={chunk.metadata.get('word_count')}")
            print(f"      内容预览: {chunk.content[:100]}...")
            print()
        
        print("✅ 数据加载测试通过")
        
    except Exception as e:
        print(f"❌ 数据加载测试失败: {e}")

if __name__ == "__main__":
    # 首先测试数据加载
    test_data_loading()
    
    # 询问用户是否继续提取知识图谱
    print("\n是否继续提取知识图谱？(y/n): ")
    user_input = input().strip().lower()
    
    if user_input in ['y', 'yes', '是']:
        main()
    else:
        print("程序结束")