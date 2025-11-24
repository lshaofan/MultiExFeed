import subprocess
import json
import sys

def run_cli(args):
    """Run the CLI command and return output."""
    cmd = ["./start.sh"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def test_analyze_command():
    print(">> Testing 'analyze' command...")
    # Test with a known symbol
    result = run_cli(["analyze", "okx", "BTC-USDT-SWAP", "--frames", "1m,5m"])
    
    if result.returncode != 0:
        print(f"❌ Command failed with code {result.returncode}")
        print("Stderr:", result.stderr)
        return False

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ Output is not valid JSON")
        print("Stdout:", result.stdout)
        return False

    # Verify structure
    required_keys = ["symbol", "timestamp", "klines", "derivatives"]
    for key in required_keys:
        if key not in data:
            print(f"❌ Missing key: {key}")
            return False

    # Verify derivatives
    derivs = data.get("derivatives", {})
    if "funding_rate" not in derivs or "oi" not in derivs or "price" not in derivs:
        print("❌ Missing derivative data")
        return False

    # Verify indicators in klines
    klines = data.get("klines", {})
    if "1m" not in klines:
        print("❌ Missing 1m kline data")
        return False
    
    kline_1m = klines["1m"]
    if "indicators" not in kline_1m:
        print("❌ Missing indicators in 1m kline")
        return False
        
    indicators = kline_1m["indicators"]
    # Check for some expected indicators
    if "trend" not in indicators or "rsi_14" not in indicators.get("momentum", {}):
        print("❌ Missing specific indicators (trend or rsi)")
        return False

    print("✅ 'analyze' command structure verified.")
    return True

if __name__ == "__main__":
    success = test_analyze_command()
    if not success:
        sys.exit(1)
    print(">> All tests passed!")
