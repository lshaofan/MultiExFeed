#!/usr/bin/env python
"""
集成测试脚本 - TDD
测试配置文件、文件输出、增强数据功能
"""
import subprocess
import json
import sys
import os
from pathlib import Path

def run_cli(args):
    """运行 CLI 命令并返回结果"""
    cmd = ["./start.sh"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    return result

def test_config_with_file_output():
    """测试配置文件 + 文件输出"""
    print(">> 测试配置文件 + 文件输出...")
    
    # 使用默认配置
    result = run_cli(["analyze", "--output-mode", "file"])
    
    if result.returncode != 0:
        print(f"❌ 命令失败: {result.returncode}")
        print("Stderr:", result.stderr)
        return False
    
    # 检查是否生成了文件
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ 输出目录不存在")
        return False
    
    json_files = list(output_dir.glob("*.json"))
    if not json_files:
        print("❌ 没有生成 JSON 文件")
        return False
    
    # 读取最新的文件
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"✅ 成功生成文件: {latest_file}")
    
    # 验证文件内容
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查结构
    required_keys = ["symbol", "klines", "derivatives"]
    for key in required_keys:
        if key not in data:
            print(f"❌ 缺少键: {key}")
            return False
    
    print("✅ 配置文件 + 文件输出测试通过")
    return True

def test_bollinger_bands():
    """测试布林带是否修复"""
    print(">> 测试布林带修复...")
    
    result = run_cli(["analyze", "okx", "BTC-USDT-SWAP", "--frames", "1m"])
    
    if result.returncode != 0:
        print(f"❌ 命令失败: {result.returncode}")
        print("Stderr:", result.stderr)
        return False
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ 输出不是有效的 JSON")
        return False
    
    # 检查布林带
    if "1m" in data.get("klines", {}):
        indicators = data["klines"]["1m"].get("indicators", {})
        volatility = indicators.get("volatility", {})
        
        bb_upper = volatility.get("bb_upper")
        bb_lower = volatility.get("bb_lower")
        
        if bb_upper is None or bb_lower is None:
            print(f"❌ 布林带仍然为 null (bb_upper={bb_upper}, bb_lower={bb_lower})")
            return False
        
        print(f"✅ 布林带修复成功 (bb_upper={bb_upper:.2f}, bb_lower={bb_lower:.2f})")
        return True
    else:
        print("❌ 缺少 1m K线数据")
        return False

def test_high_timeframe_klines():
    """测试高周期 K 线 (1H, 4H, 1D)"""
    print(">> 测试高周期 K 线...")
    
    result = run_cli(["analyze", "okx", "BTC-USDT-SWAP", "--frames", "1H,4H,1D"])
    
    if result.returncode != 0:
        print(f"❌ 命令失败: {result.returncode}")
        print("Stderr:", result.stderr)
        return False
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ 输出不是有效的 JSON")
        return False
    
    klines = data.get("klines", {})
    
    # 检查是否有错误
    for frame in ["1H", "4H", "1D"]:
        if frame not in klines:
            print(f"❌ 缺少 {frame} 数据")
            return False
        
        if "error" in klines[frame]:
            print(f"❌ {frame} 有错误: {klines[frame]['error']}")
            return False
        
        if "data" in klines[frame] and isinstance(klines[frame]["data"], list):
            print(f"✅ {frame} 数据正常 ({len(klines[frame]['data'])} 条 K线)")
        else:
            print(f"❌ {frame} 数据格式不正确")
            return False
    
    print("✅ 高周期 K 线测试通过")
    return True

if __name__ == "__main__":
    tests = [
        ("配置文件与文件输出", test_config_with_file_output),
        ("布林带修复", test_bollinger_bands),
        ("高周期K线", test_high_timeframe_klines),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"测试: {name}")
        print(f"{'='*60}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"测试总结")
    print(f"{'='*60}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed > 0:
        sys.exit(1)
    print("\n🎉 所有测试通过！")
