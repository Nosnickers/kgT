"""
测试本地嵌入模型路径配置
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from config import Config
from src.embedding_manager import EmbeddingManager

def test_local_model_path():
    """测试本地模型路径配置"""
    print("=" * 60)
    print("测试本地嵌入模型路径配置")
    print("=" * 60)
    
    # 加载配置
    config = Config.from_env()
    print(f"\n配置加载成功")
    print(f"  - 默认模型名称: {config.embedding.model_name}")
    print(f"  - 本地模型路径: {config.embedding.local_model_path}")
    
    # 确定使用的模型路径
    model_name = config.embedding.model_name
    if config.embedding.local_model_path:
        local_path = Path(config.embedding.local_model_path)
        if local_path.exists():
            print(f"\n✓ 本地模型路径存在: {local_path}")
            model_name = str(local_path)
        else:
            print(f"\n✗ 本地模型路径不存在: {local_path}")
            print(f"  将使用 Hugging Face Hub 下载模型: {model_name}")
    else:
        print(f"\n未配置本地模型路径")
        print(f"  将使用 Hugging Face Hub 下载模型: {model_name}")
    
    # 尝试加载模型
    print(f"\n正在加载嵌入模型...")
    try:
        embedding_manager = EmbeddingManager(
            model_name=model_name,
            cache_embeddings=config.embedding.cache_embeddings
        )
        print(f"✓ 嵌入模型加载成功")
        print(f"  - 向量维度: {embedding_manager.get_embedding_dimension()}")
        
        # 测试嵌入生成
        test_text = "这是一个测试文本"
        print(f"\n正在测试嵌入生成...")
        embedding = embedding_manager.embed_text(test_text)
        print(f"✓ 嵌入生成成功")
        print(f"  - 文本: {test_text}")
        print(f"  - 向量维度: {len(embedding)}")
        print(f"  - 前5个值: {embedding[:5]}")
        
        print(f"\n" + "=" * 60)
        print("测试通过！本地模型路径配置正常工作")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_local_model_path()
    sys.exit(0 if success else 1)
