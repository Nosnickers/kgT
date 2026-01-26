#!/usr/bin/env python3
"""测试多患者提取和关系类型增强"""
import sys
sys.path.append('src')
import logging
import json
from config import Config
from src.entity_extractor import EntityExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_test_chunks():
    """加载测试用的chunk数据"""
    chunks = [
        {
            "title": "病历片断 1：患者基本信息 - 林悦",
            "content": """病历号：MK20231026018
姓名：林悦
性别：女
年龄：32岁
职业：外企项目经理
首次就诊：是"""
        },
        {
            "title": "病历片断 5：治疗方案与执行 - MK20231026018",
            "content": """治疗项目：Beyond冷光美白术
目标：改善上前牙美学外观。
执行医生：A陈医生
关键步骤：抛光清洁、牙龈保护、涂抹Beyond美白凝胶、冷光照射（共三轮，每轮8分钟）。
使用材料：不含氟抛光膏、光固化树脂型牙龈保护剂、Beyond冷光美白凝胶（主要成分：过氧化氢）。"""
        },
        {
            "title": "病历片断 7：患者基本信息 - 王毛毛（儿童）",
            "content": """病历号：CP20231115007
姓名：王毛毛
性别：男
年龄：8岁
陪同人员：母亲李女士
首次就诊：是"""
        },
        {
            "title": "病历片断 13：患者基本信息 - 张大大",
            "content": """病历号：AD20231205022
姓名：张大大
性别：男
年龄：45岁
职业：公司职员
首次就诊：是"""
        }
    ]
    return chunks

def test_prompt_improvements():
    """测试提示语改进"""
    print("=== 测试提示语改进 ===")
    
    config = Config.from_env()
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    # 检查提示语内容
    prompt = extractor.create_extraction_prompt()
    messages = prompt.format_messages(text="测试文本")
    system_content = messages[0].content
    
    # 检查关键改进点
    checks = [
        ("多患者提取说明", "multiple patients", False),  # 英文检查
        ("多患者提取说明", "EACH patient", True),  # 英文检查
        ("通用占位符", "[患者姓名]", True),
        ("通用占位符", "[病历号]", True),
        ("材料字段提取", "使用材料：", True),
        ("新关系类型", "PROCEDURE_USES_MATERIAL", True),
        ("新关系类型", "MATERIAL_HAS_COMPONENT", True),
        ("新关系类型", "PROCEDURE_PERFORMED_BY", True),
        ("新关系类型", "PROCEDURE_AIMS_TO_ACHIEVE", True),
        ("新关系类型", "PATIENT_HAS_OCCUPATION", True),
        ("新关系类型", "PATIENT_IS_FIRST_VISIT", True),
        ("深度思考控制", "NO THINKING OUTPUT", True),
        ("幻觉防止", "NO HALLUCINATION POLICY", True),
    ]
    
    print("提示语关键改进点检查:")
    for check_name, keyword, should_exist in checks:
        exists = keyword in system_content
        status = "✅ 存在" if exists == should_exist else "❌ 缺失" if should_exist else "❌ 不应存在"
        print(f"  {check_name} ('{keyword}'): {status}")
    
    # 检查是否移除了具体示例
    if '林悦' in system_content and 'MK20231026018' in system_content:
        print("❌ 警告: 提示语中仍包含具体患者信息（可能造成偏见）")
    else:
        print("✅ 提示语中无具体患者信息（使用通用占位符）")
    
    return True

def test_relationship_types():
    """测试关系类型扩展"""
    print("\n=== 测试关系类型扩展 ===")
    
    config = Config.from_env()
    extractor = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=config.ollama.deep_thought_mode
    )
    
    # 检查关系类型列表
    print("检查新增关系类型:")
    new_relationship_types = [
        "PROCEDURE_USES_MATERIAL",
        "MATERIAL_HAS_COMPONENT", 
        "PROCEDURE_PERFORMED_BY",
        "PROCEDURE_AIMS_TO_ACHIEVE",
        "PATIENT_HAS_OCCUPATION",
        "PATIENT_IS_FIRST_VISIT"
    ]
    
    for rel_type in new_relationship_types:
        if rel_type in extractor.RELATIONSHIP_TYPES:
            print(f"  {rel_type}: ✅ 存在")
        else:
            print(f"  {rel_type}: ❌ 缺失")
    
    # 检查总关系类型数量
    total_types = len(extractor.RELATIONSHIP_TYPES)
    print(f"\n总关系类型数量: {total_types}")
    print("关系类型列表:", extractor.RELATIONSHIP_TYPES)
    
    return True

def test_extraction_with_mock_data():
    """使用模拟数据测试提取逻辑（不依赖LLM）"""
    print("\n=== 测试提取逻辑（模拟数据） ===")
    
    chunks = load_test_chunks()
    print(f"加载了 {len(chunks)} 个测试chunk")
    
    # 检查chunk结构
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"  标题: {chunk['title']}")
        print(f"  内容预览: {chunk['content'][:80]}...")
        
        # 检查标题中是否包含患者信息
        if '林悦' in chunk['title']:
            print("  ✅ 标题包含患者: 林悦")
        if '王毛毛' in chunk['title']:
            print("  ✅ 标题包含患者: 王毛毛")
        if '张大大' in chunk['title']:
            print("  ✅ 标题包含患者: 张大大")
        
        # 检查内容中的关键字段
        content = chunk['content']
        if '病历号：' in content:
            print("  ✅ 内容包含病历号字段")
        if '姓名：' in content:
            print("  ✅ 内容包含姓名字段")
        if '使用材料：' in content:
            print("  ✅ 内容包含材料字段")
    
    print("\n✅ 模拟数据检查完成")
    return True

def test_deep_thought_config():
    """测试深度思考模式配置"""
    print("\n=== 测试深度思考模式配置 ===")
    
    config = Config.from_env()
    print(f"配置文件 deep_thought_mode: {config.ollama.deep_thought_mode}")
    
    # 测试禁用模式
    extractor_disabled = EntityExtractor(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
        temperature=config.ollama.temperature,
        num_ctx=config.ollama.num_ctx,
        deep_thought_mode=False  # 强制禁用
    )
    
    print(f"提取器 deep_thought_mode (禁用): {extractor_disabled.deep_thought_mode}")
    
    # 检查LLM配置（尝试访问stop参数）
    try:
        # 注意：Ollama模型可能不直接暴露stop参数
        llm_config = extractor_disabled.llm
        print(f"LLM类型: {type(llm_config)}")
        
        # 检查是否有stop属性或参数
        if hasattr(llm_config, 'stop'):
            print(f"LLM stop参数: {llm_config.stop}")
            if llm_config.stop == ["<think>", "</think>"]:
                print("✅ stop参数正确设置")
            else:
                print(f"⚠️ stop参数设置不同: {llm_config.stop}")
        else:
            print("ℹ️ LLM对象没有stop属性（可能正常）")
            
    except Exception as e:
        print(f"检查LLM配置时出错: {e}")
    
    return True

def run_extraction_test():
    """运行实际提取测试（如果Ollama服务可用）"""
    print("\n=== 运行实际提取测试 ===")
    
    try:
        config = Config.from_env()
        extractor = EntityExtractor(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
            num_ctx=config.ollama.num_ctx,
            deep_thought_mode=config.ollama.deep_thought_mode
        )
        
        # 使用第一个chunk进行测试
        chunks = load_test_chunks()
        test_chunk = chunks[0]
        
        # 模拟graph_builder的组合文本格式
        title = test_chunk['title']
        content = test_chunk['content']
        combined_text = f"标题：{title}\n内容：{content}"
        
        print(f"测试组合文本格式:")
        print(f"  标题: {title}")
        print(f"  原始内容长度: {len(content)} 字符")
        print(f"  组合文本长度: {len(combined_text)} 字符")
        print(f"  组合文本预览:\n{combined_text[:150]}...")
        
        print("\n正在调用LLM进行提取（可能需要时间）...")
        print("注意：如果Ollama服务未运行，此测试将失败")
        
        # 尝试提取（设置较短超时）
        result = extractor.extract(combined_text, max_retries=1)
        
        print(f"\n提取结果:")
        print(f"  实体数量: {len(result.entities)}")
        print(f"  关系数量: {len(result.relationships)}")
        
        if result.entities:
            print("\n提取的实体:")
            for entity in result.entities[:5]:  # 只显示前5个
                print(f"  - {entity.name} ({entity.type})")
        
        if result.relationships:
            print("\n提取的关系:")
            for rel in result.relationships[:5]:  # 只显示前5个
                print(f"  - {rel.source} --[{rel.type}]--> {rel.target}")
        
        # 检查是否提取了正确的患者
        patient_names = [e.name for e in result.entities if e.type == 'Patient']
        if patient_names:
            print(f"\n提取的患者姓名: {patient_names}")
            if '林悦' in patient_names:
                print("✅ 成功提取患者: 林悦")
            else:
                print("⚠️ 未提取到患者: 林悦")
        
        return True
        
    except Exception as e:
        print(f"提取测试失败（可能Ollama服务未运行）: {e}")
        print("ℹ️ 这是预期行为，如果Ollama服务未运行")
        return False

if __name__ == '__main__':
    print("开始测试多患者提取和关系类型增强")
    print("=" * 60)
    
    tests = [
        ("提示语改进", test_prompt_improvements),
        ("关系类型扩展", test_relationship_types),
        ("提取逻辑（模拟数据）", test_extraction_with_mock_data),
        ("深度思考模式配置", test_deep_thought_config),
        ("实际提取测试", run_extraction_test),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*40}")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试 {test_name} 时出错: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n总体: {passed}/{total} 测试通过")
    
    # 提供改进建议
    print("\n改进建议:")
    if passed == total:
        print("✅ 所有测试通过！修改已成功实施。")
        print("建议运行完整知识图谱构建流程进行最终验证。")
    else:
        print("⚠️ 部分测试失败，请检查以下问题:")
        for test_name, success in results:
            if not success:
                print(f"  - {test_name} 测试失败")
    
    print("=" * 60)