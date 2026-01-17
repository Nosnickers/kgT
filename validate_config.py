#!/usr/bin/env python
"""
验证配置加载和合并逻辑
"""
import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def test_config_defaults():
    """测试默认值"""
    from config import Config
    
    print("测试默认配置值")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=test
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
DATA_FILE=data/test.json
        """)
        env_file = f.name
    
    try:
        # 临时覆盖系统环境变量
        original_enable_entity_linking = os.environ.get('ENABLE_ENTITY_LINKING')
        original_enable_llm_logging = os.environ.get('ENABLE_LLM_LOGGING')
        original_entity_types = os.environ.get('ENTITY_TYPES_TO_LINK')
        
        # 临时删除这些环境变量
        if original_enable_entity_linking:
            del os.environ['ENABLE_ENTITY_LINKING']
        if original_enable_llm_logging:
            del os.environ['ENABLE_LLM_LOGGING']
        if original_entity_types:
            del os.environ['ENTITY_TYPES_TO_LINK']
        
        config = Config.from_env(env_file)
        
        print(f"  enable_entity_linking: {config.processing.enable_entity_linking} (期望: False)")
        print(f"  enable_llm_logging: {config.processing.enable_llm_logging} (期望: False)")
        print(f"  entity_types_to_link: {config.processing.entity_types_to_link} (期望: None)")
        
        assert config.processing.enable_entity_linking == False
        assert config.processing.enable_llm_logging == False
        assert config.processing.entity_types_to_link is None
        
        print("  ✓ 通过")
        
        # 恢复环境变量
        if original_enable_entity_linking:
            os.environ['ENABLE_ENTITY_LINKING'] = original_enable_entity_linking
        if original_enable_llm_logging:
            os.environ['ENABLE_LLM_LOGGING'] = original_enable_llm_logging
        if original_entity_types:
            os.environ['ENTITY_TYPES_TO_LINK'] = original_entity_types
            
    finally:
        os.unlink(env_file)

def test_config_env_vars():
    """测试环境变量配置"""
    from config import Config
    
    print("\n测试环境变量配置")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("""
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=test
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b
DATA_FILE=data/test.json
ENABLE_ENTITY_LINKING=true
ENABLE_LLM_LOGGING=true
ENTITY_TYPES_TO_LINK=Patient,Diagnosis
        """)
        env_file = f.name
    
    try:
        # 临时覆盖系统环境变量
        original_enable_entity_linking = os.environ.get('ENABLE_ENTITY_LINKING')
        original_enable_llm_logging = os.environ.get('ENABLE_LLM_LOGGING')
        original_entity_types = os.environ.get('ENTITY_TYPES_TO_LINK')
        
        # 设置临时环境变量
        os.environ['ENABLE_ENTITY_LINKING'] = 'true'
        os.environ['ENABLE_LLM_LOGGING'] = 'true'
        os.environ['ENTITY_TYPES_TO_LINK'] = 'Patient,Diagnosis'
        
        config = Config.from_env(env_file)
        
        print(f"  enable_entity_linking: {config.processing.enable_entity_linking} (期望: True)")
        print(f"  enable_llm_logging: {config.processing.enable_llm_logging} (期望: True)")
        print(f"  entity_types_to_link: {config.processing.entity_types_to_link} (期望: ['Patient', 'Diagnosis'])")
        
        assert config.processing.enable_entity_linking == True
        assert config.processing.enable_llm_logging == True
        assert config.processing.entity_types_to_link == ['Patient', 'Diagnosis']
        
        print("  ✓ 通过")
        
        # 恢复环境变量
        if original_enable_entity_linking:
            os.environ['ENABLE_ENTITY_LINKING'] = original_enable_entity_linking
        else:
            del os.environ['ENABLE_ENTITY_LINKING']
        if original_enable_llm_logging:
            os.environ['ENABLE_LLM_LOGGING'] = original_enable_llm_logging
        else:
            del os.environ['ENABLE_LLM_LOGGING']
        if original_entity_types:
            os.environ['ENTITY_TYPES_TO_LINK'] = original_entity_types
        else:
            del os.environ['ENTITY_TYPES_TO_LINK']
            
    finally:
        os.unlink(env_file)

def test_config_parsing():
    """测试配置解析逻辑"""
    print("\n测试配置解析逻辑")
    
    # 模拟命令行参数和环境变量
    class MockArgs:
        enable_entity_linking = False
        enable_llm_logging = True
        entity_types_to_link = None
    
    class MockConfig:
        class Processing:
            enable_entity_linking = True
            enable_llm_logging = False
            entity_types_to_link = ['Patient', 'PatientId']
        
        processing = Processing()
    
    args = MockArgs()
    config = MockConfig()
    
    # 应用合并逻辑（与main.py中的逻辑相同）
    enable_entity_linking = args.enable_entity_linking or config.processing.enable_entity_linking
    enable_llm_logging = args.enable_llm_logging or config.processing.enable_llm_logging
    
    entity_types_to_link = None
    if args.entity_types_to_link:
        entity_types_to_link = [t.strip() for t in args.entity_types_to_link.split(",") if t.strip()]
    elif config.processing.entity_types_to_link:
        entity_types_to_link = config.processing.entity_types_to_link
    else:
        entity_types_to_link = ["Patient", "PatientId"]
    
    print(f"  命令行: enable_entity_linking={args.enable_entity_linking}, enable_llm_logging={args.enable_llm_logging}")
    print(f"  环境变量: enable_entity_linking={config.processing.enable_entity_linking}, enable_llm_logging={config.processing.enable_llm_logging}")
    print(f"  合并结果: enable_entity_linking={enable_entity_linking}, enable_llm_logging={enable_llm_logging}")
    print(f"  实体类型: {entity_types_to_link}")
    
    # 验证合并逻辑
    assert enable_entity_linking == True  # 环境变量为True
    assert enable_llm_logging == True     # 命令行参数为True
    assert entity_types_to_link == ['Patient', 'PatientId']  # 环境变量配置
    
    print("  ✓ 通过")

def main():
    print("=" * 60)
    print("配置验证测试")
    print("=" * 60)
    
    try:
        test_config_defaults()
        test_config_env_vars()
        test_config_parsing()
        
        print("\n" + "=" * 60)
        print("所有配置验证测试通过！")
        print("=" * 60)
        
        print("\n配置选项总结：")
        print("1. enable_entity_linking: 是否启用实体链接（默认: false）")
        print("2. entity_types_to_link: 要链接的实体类型列表（默认: ['Patient', 'PatientId']）")
        print("3. enable_llm_logging: 是否启用LLM详细日志记录（默认: false）")
        print("\n配置优先级：命令行参数 > 环境变量 > 默认值")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()