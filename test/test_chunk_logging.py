#!/usr/bin/env python3
"""
快速测试脚本：验证chunk日志记录功能
"""

import subprocess
import sys
from pathlib import Path

def test_chunk_logging():
    """测试chunk日志记录功能"""
    print("正在测试chunk日志记录功能...")
    
    # 检查必要的文件是否存在
    test_script = Path("test_chunk_22_logging.py")
    csv_file = Path("kg_build_20260110_182346.csv")
    
    if not test_script.exists():
        print(f"错误: 测试脚本不存在: {test_script}")
        return False
    
    if not csv_file.exists():
        print(f"错误: CSV文件不存在: {csv_file}")
        return False
    
    # 运行测试命令
    cmd = [
        sys.executable, 
        "test_chunk_22_logging.py",
        "--chunk-id", "22",
        "--csv-file", "kg_build_20260110_182346.csv",
        "--config", ".env"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print("\n=== 标准输出 ===")
        print(result.stdout)
        
        if result.stderr:
            print("\n=== 错误输出 ===")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✓ 测试执行成功！")
            return True
        else:
            print(f"\n✗ 测试执行失败，返回码: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n✗ 测试超时 (60秒)")
        return False
    except Exception as e:
        print(f"\n✗ 测试执行出错: {e}")
        return False

if __name__ == "__main__":
    print("Chunk日志记录测试工具")
    print("=" * 50)
    
    success = test_chunk_logging()
    
    if success:
        print("\n测试完成！请检查 logs/ 目录下的日志文件获取详细分析结果。")
    else:
        print("\n测试失败，请检查错误信息。")
        sys.exit(1)