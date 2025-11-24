#!/usr/bin/env python
"""
测试数据分析增强功能
包括：新配置格式、衍生指标、趋势标签等
"""
import subprocess
import json
import sys
from pathlib import Path

def run_cli(args):
    """运行 CLI 命令"""
    cmd = ["./start.sh"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    return result

def test_new_config_format():
    """测试新配置格式（每个周期独立 limit）"""
    print(">> 测试新配置格式...")
    
    result = run_cli(["analyze"])
    
    if result.returncode != 0:
        print(f"❌ 命令失败: {result.returncode}")
        print("Stderr:", result.stderr)
        return False
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ 输出不是有效的 JSON")
        print("Stdout:", result.stdout)
        return False
    
    klines = data.get("klines", {})
    
    # 验证所有周期都存在
    expected_frames = ["1m", "5m", "15m", "1H", "4H", "1D"]
    for frame in expected_frames:
        if frame not in klines:
            print(f"❌ 缺少周期: {frame}")
            return False
    
    print("✅ 新配置格式测试通过")
    return True

def test_derived_metrics():
    """测试衍生指标"""
    print(">> 测试衍生指标...")
    
    result = run_cli(["analyze", "okx", "BTC-USDT-SWAP", "--frames", "1m,5m"])
    
    if result.returncode != 0:
        print(f"❌ 命令失败: {result.returncode}")
        print("Stderr:", result.stderr)
        return False
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ 输出不是有效的 JSON")
        return False
    
    # 检查 summary 块
    if "1m" in data.get("klines", {}):
        summary = data["klines"]["1m"].get("summary", {})
        
        if "trend_label" not in summary:
            print("❌ 缺少 trend_label")
            return False
        
        if "volatility_label" not in summary:
            print("❌ 缺少 volatility_label")
            return False
        
        if "volume_label" not in summary:
            print("❌ 缺少 volume_label")
            return False
        
        print(f"✅ Summary: trend={summary['trend_label']}, vol={summary['volatility_label']}, volume={summary['volume_label']}")
    
    # 检查 derivatives 衍生指标
    derivatives = data.get("derivatives", {})
    funding = derivatives.get("funding_rate", {})
    
    if "8h_avg" in funding or "24h_avg" in funding:
        print(f"✅ Funding stats: 8h_avg={funding.get('8h_avg')}, 24h_avg={funding.get('24h_avg')}")
    
    # 检查 price basis
    price = derivatives.get("price", {})
    if "basis" in price:
        print(f"✅ Basis: {price.get('basis')}, {price.get('basis_pct')}%")
    
    print("✅ 衍生指标测试通过")
    return True

if __name__ == "__main__":
    tests = [
        ("新配置格式", test_new_config_format),
        ("衍生指标", test_derived_metrics),
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"测试总结")
    print(f"{'='*60}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    
    if failed > 0:
        sys.exit(1)
    print("\n🎉 所有测试通过！")
