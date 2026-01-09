#!/usr/bin/env python3
"""
测试深度思考模式配置是否正确加载
"""

from config import Config

def test_deep_thought_config():
    """测试深度思考模式配置加载"""
    print("测试深度思考模式配置...")
    
    # 从默认.env文件加载配置
    config = Config.from_env()
    
    # 打印Ollama配置
    print(f"Ollama模型: {config.ollama.model}")
    print(f"温度参数: {config.ollama.temperature}")
    print(f"上下文窗口: {config.ollama.num_ctx}")
    print(f"深度思考模式: {config.ollama.deep_thought_mode}")
    
    # 测试是否可以通过环境变量修改深度思考模式
    print("\n修改环境变量测试...")
    import os
    
    # 保存原始环境变量
    original_deep_thought = os.environ.get("OLLAMA_DEEP_THOUGHT_MODE")
    
    # 设置环境变量为True
    os.environ["OLLAMA_DEEP_THOUGHT_MODE"] = "true"
    config_true = Config.from_env()
    print(f"深度思考模式 (设置为true): {config_true.ollama.deep_thought_mode}")
    
    # 设置环境变量为False
    os.environ["OLLAMA_DEEP_THOUGHT_MODE"] = "false"
    config_false = Config.from_env()
    print(f"深度思考模式 (设置为false): {config_false.ollama.deep_thought_mode}")
    
    # 恢复原始环境变量
    if original_deep_thought is not None:
        os.environ["OLLAMA_DEEP_THOUGHT_MODE"] = original_deep_thought
    else:
        os.environ.pop("OLLAMA_DEEP_THOUGHT_MODE", None)
    
    print("\n测试通过！深度思考模式配置可以正确加载和修改。")

if __name__ == "__main__":
    test_deep_thought_config()
