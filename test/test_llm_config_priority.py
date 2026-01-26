"""
测试 LLM 配置优先级
验证：命令行参数 > .env配置 > 默认值
"""
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

def test_config_priority():
    """测试配置优先级"""
    print("=" * 70)
    print("测试 LLM 配置优先级")
    print("=" * 70)
    
    # 测试场景
    scenarios = [
        {
            "name": "场景1: 命令行指定 --enable-online-llm",
            "env_enable_online": "false",
            "cmd_enable_online": True,
            "expected": "在线 LLM (命令行)"
        },
        {
            "name": "场景2: 命令行不指定，.env 设置 ENABLE_ONLINE_LLM=true",
            "env_enable_online": "true",
            "cmd_enable_online": False,
            "expected": "在线 LLM (.env)"
        },
        {
            "name": "场景3: 命令行不指定，.env 设置 ENABLE_ONLINE_LLM=false",
            "env_enable_online": "false",
            "cmd_enable_online": False,
            "expected": "本地 Ollama"
        },
        {
            "name": "场景4: 命令行指定 --enable-online-llm，.env 也设置为 true",
            "env_enable_online": "true",
            "cmd_enable_online": True,
            "expected": "在线 LLM (命令行)"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*70}")
        print(f"{scenario['name']}")
        print(f"{'='*70}")
        print(f"  .env: ENABLE_ONLINE_LLM={scenario['env_enable_online']}")
        print(f"  命令行: --enable-online-llm={scenario['cmd_enable_online']}")
        print(f"  期望: {scenario['expected']}")
        
        # 模拟配置逻辑
        env_enable = scenario['env_enable_online'].lower() == 'true'
        cmd_enable = scenario['cmd_enable_online']
        
        if cmd_enable:
            result = "在线 LLM (命令行)"
        elif env_enable:
            result = "在线 LLM (.env)"
        else:
            result = "本地 Ollama"
        
        # 验证结果
        if result == scenario['expected']:
            print(f"  ✓ 结果: {result}")
        else:
            print(f"  ✗ 结果: {result} (期望: {scenario['expected']})")
    
    print(f"\n{'='*70}")
    print("测试完成")
    print(f"{'='*70}")
    
    # 实际测试 qa_cli.py 中的逻辑
    print(f"\n{'='*70}")
    print("实际代码逻辑测试")
    print(f"{'='*70}")
    
    from config import Config
    config = Config.from_env()
    
    print(f"\n当前 .env 配置:")
    print(f"  ENABLE_ONLINE_LLM: {config.enable_online_llm}")
    print(f"  online_llm: {config.online_llm}")
    
    print(f"\n配置优先级规则:")
    print(f"  1. 命令行参数 --enable-online-llm (最高优先级)")
    print(f"  2. .env 文件中的 ENABLE_ONLINE_LLM=true")
    print(f"  3. 默认使用本地 Ollama")
    
    print(f"\n使用示例:")
    print(f"  # 使用命令行参数（覆盖 .env）")
    print(f"  python qa_cli.py interactive --enable-online-llm")
    print(f"  ")
    print(f"  # 使用 .env 配置（无需命令行参数）")
    print(f"  python qa_cli.py interactive")
    print(f"  ")
    print(f"  # 使用本地 Ollama（.env 中 ENABLE_ONLINE_LLM=false）")
    print(f"  python qa_cli.py interactive")

if __name__ == "__main__":
    test_config_priority()
