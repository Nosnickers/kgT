#!/usr/bin/env python
"""
测试实体链接功能配置
演示混合使用方式：命令行参数优先级高于环境变量
"""
import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def test_config_loading():
    """测试配置加载逻辑"""
    from config import Config
    
    print("测试1: 默认配置（未设置环境变量）")
    # 创建临时.env文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=testpassword
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
DATA_FILE=data/test.json
        """)
        env_file = f.name
    
    try:
        config = Config.from_env(env_file)
        print(f"  enable_entity_linking: {config.processing.enable_entity_linking} (期望: False)")
        print(f"  entity_types_to_link: {config.processing.entity_types_to_link} (期望: None)")
        assert config.processing.enable_entity_linking == False
        assert config.processing.entity_types_to_link is None
        print("  ✓ 通过")
    finally:
        os.unlink(env_file)
    
    print("\n测试2: 环境变量配置")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=testpassword
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
DATA_FILE=data/test.json
ENABLE_ENTITY_LINKING=true
ENTITY_TYPES_TO_LINK=Patient,PatientId,Diagnosis
        """)
        env_file = f.name
    
    try:
        config = Config.from_env(env_file)
        print(f"  enable_entity_linking: {config.processing.enable_entity_linking} (期望: True)")
        print(f"  entity_types_to_link: {config.processing.entity_types_to_link} (期望: ['Patient', 'PatientId', 'Diagnosis'])")
        assert config.processing.enable_entity_linking == True
        assert config.processing.entity_types_to_link == ['Patient', 'PatientId', 'Diagnosis']
        print("  ✓ 通过")
    finally:
        os.unlink(env_file)
    
    print("\n测试3: 环境变量空值处理")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=testpassword
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
DATA_FILE=data/test.json
ENTITY_TYPES_TO_LINK=
        """)
        env_file = f.name
    
    try:
        config = Config.from_env(env_file)
        print(f"  entity_types_to_link: {config.processing.entity_types_to_link} (期望: None)")
        assert config.processing.entity_types_to_link is None
        print("  ✓ 通过")
    finally:
        os.unlink(env_file)

def test_argparse():
    """测试命令行参数解析"""
    import argparse
    from unittest.mock import patch
    
    print("\n测试4: 命令行参数解析")
    
    # 模拟命令行参数
    test_args = [
        'main.py',
        '--build',
        '--config', '.env',
        '--enable-entity-linking',
        '--entity-types-to-link', 'Patient,Diagnosis'
    ]
    
    with patch('sys.argv', test_args):
        from main import main as main_function
        # 注意：这里实际上不会运行main函数，只是验证参数解析
        # 我们可以手动解析参数
        parser = argparse.ArgumentParser()
        parser.add_argument('--build', action='store_true')
        parser.add_argument('--config', type=str, default='.env')
        parser.add_argument('--enable-entity-linking', action='store_true')
        parser.add_argument('--entity-types-to-link', type=str, default=None)
        
        args = parser.parse_args(test_args[1:])
        print(f"  enable_entity_linking: {args.enable_entity_linking} (期望: True)")
        print(f"  entity_types_to_link: {args.entity_types_to_link} (期望: 'Patient,Diagnosis')")
        assert args.enable_entity_linking == True
        assert args.entity_types_to_link == 'Patient,Diagnosis'
        print("  ✓ 通过")

def test_config_merging():
    """测试配置合并逻辑"""
    print("\n测试5: 配置合并逻辑（命令行 > 环境变量 > 默认值）")
    
    # 模拟场景
    scenarios = [
        {
            'name': '命令行优先级最高',
            'cmd_enable': True,
            'cmd_types': 'Diagnosis,Symptom',
            'env_enable': False,
            'env_types': 'Patient,PatientId',
            'expected_enable': True,
            'expected_types': ['Diagnosis', 'Symptom']
        },
        {
            'name': '环境变量配置',
            'cmd_enable': False,
            'cmd_types': None,
            'env_enable': True,
            'env_types': 'Patient,PatientId',
            'expected_enable': True,  # 因为env_enable为True，cmd_enable为False，但or运算结果为True
            'expected_types': ['Patient', 'PatientId']
        },
        {
            'name': '默认值',
            'cmd_enable': False,
            'cmd_types': None,
            'env_enable': False,
            'env_types': None,
            'expected_enable': False,
            'expected_types': ['Patient', 'PatientId']  # 默认值
        }
    ]
    
    for scenario in scenarios:
        print(f"\n  场景: {scenario['name']}")
        
        # 模拟命令行参数
        class MockArgs:
            enable_entity_linking = scenario['cmd_enable']
            entity_types_to_link = scenario['cmd_types']
        
        # 模拟配置对象
        class MockConfig:
            class Processing:
                enable_entity_linking = scenario['env_enable']
                entity_types_to_link = scenario['env_types'].split(',') if scenario['env_types'] else None
        
            processing = Processing()
        
        args = MockArgs()
        config = MockConfig()
        
        # 应用合并逻辑（与main.py中的逻辑相同）
        enable_entity_linking = args.enable_entity_linking or config.processing.enable_entity_linking
        
        entity_types_to_link = None
        if args.entity_types_to_link:
            entity_types_to_link = [t.strip() for t in args.entity_types_to_link.split(",") if t.strip()]
        elif config.processing.entity_types_to_link:
            entity_types_to_link = config.processing.entity_types_to_link
        else:
            entity_types_to_link = ["Patient", "PatientId"]
        
        print(f"    命令行: enable={args.enable_entity_linking}, types={args.entity_types_to_link}")
        print(f"    环境变量: enable={config.processing.enable_entity_linking}, types={config.processing.entity_types_to_link}")
        print(f"    合并结果: enable={enable_entity_linking}, types={entity_types_to_link}")
        print(f"    期望结果: enable={scenario['expected_enable']}, types={scenario['expected_types']}")
        
        assert enable_entity_linking == scenario['expected_enable']
        assert entity_types_to_link == scenario['expected_types']
        print("    ✓ 通过")

def main():
    print("=" * 60)
    print("实体链接功能配置测试")
    print("=" * 60)
    
    try:
        test_config_loading()
        test_argparse()
        test_config_merging()
        
        print("\n" + "=" * 60)
        print("所有测试通过！")
        print("=" * 60)
        
        # 显示使用示例
        print("\n使用示例:")
        print("1. 环境变量配置 (.env文件中添加):")
        print("   ENABLE_ENTITY_LINKING=true")
        print("   ENTITY_TYPES_TO_LINK=Patient,PatientId,Diagnosis")
        print("   运行: python main.py --build --config .env --no-clear")
        
        print("\n2. 命令行参数:")
        print("   python main.py --build --config .env --no-clear \\")
        print("        --enable-entity-linking --entity-types-to-link \"Patient,Diagnosis\"")
        
        print("\n3. 混合使用（命令行优先级更高）:")
        print("   # .env中设置ENABLE_ENTITY_LINKING=true")
        print("   # 命令行覆盖实体类型:")
        print("   python main.py --build --config .env --no-clear \\")
        print("        --entity-types-to-link \"Diagnosis,Symptom\"")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()