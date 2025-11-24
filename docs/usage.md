# ExDataHub 使用文档

ExDataHub 是一个多交易所行情数据网关，目前支持 OKX 交易所。

## 安装与配置

1. **环境准备**
   确保已安装 `uv` (Python 虚拟环境管理工具)。

   ```bash
   # 如果未安装 uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **配置环境变量**
   复制示例配置并填入你的 API Key（获取公共行情数据可留空）。

   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   vim .env
   ```

3. **依赖安装**
   首次运行脚本时，`uv` 会自动处理依赖。

## CLI 使用方法

使用 `start.sh` 脚本调用 CLI。

### 基本语法

```bash
./start.sh fetch [EXCHANGE] [DATA_TYPE] [SYMBOL] [OPTIONS]
```

- `EXCHANGE`: 交易所名称 (目前支持 `okx`)
- `DATA_TYPE`: 数据类型 (`ticker`, `kline`, `orderbook`)
- `SYMBOL`: 交易对 (例如 `BTC-USDT`)

### 示例

#### 1. 获取 Ticker (最新成交价)

```bash
./start.sh fetch okx ticker BTC-USDT
```

#### 2. 获取 K 线数据 (Candlesticks)

支持 `--interval` (默认 1m) 和 `--limit` (默认 100) 参数。

```bash
# 获取最近 100 条 1 小时 K 线
./start.sh fetch okx kline BTC-USDT --interval 1H --limit 100
```

#### 3. 获取深度数据 (Orderbook)

```bash
./start.sh fetch okx orderbook BTC-USDT --limit 5
```

## 输出格式

所有命令均输出标准 JSON 格式，方便通过管道 (`|`) 传递给其他工具（如 `jq`）。

```bash
./start.sh fetch okx orderbook BTC-USDT --limit 5
```

#### 4. 分析市场数据（综合数据 + 指标）

**新增**: `analyze` 命令一次性获取多周期 K 线、衍生品数据和技术指标。

```bash
# 默认获取 1m,5m,15m,1h,4h,1d 所有周期
./start.sh analyze okx BTC-USDT-SWAP

# 自定义周期
./start.sh analyze okx BTC-USDT-SWAP --frames 1m,5m,15m
```

**返回数据包含**：
- 多周期 K 线数据
- 衍生品数据（资金费率、OI、标记价/指数价）
- 技术指标（EMA, RSI, MACD, ATR, BB 等）

## 输出格式

所有命令均输出标准 JSON 格式，方便通过管道 (`|`) 传递给其他工具（如 `jq`）。

```json
{
  "code": "0",
  "msg": "",
  "data": [
    {
      "instId": "BTC-USDT",
      "last": "98000.5",
      ...
    }
  ]
}
```

## 技术指标说明

`analyze` 命令计算的技术指标包括：

- **趋势类**: EMA(9, 21, 50), MA(100, 200)
- **波动率**: Bollinger Bands(20, 2), ATR(14)
- **动量类**: RSI(14), MACD(12, 26, 9)
- **成交量**: Volume MA(20)

## 镜像源配置

项目已配置清华大学 PyPI 镜像源以加速依赖下载。配置位于 `pyproject.toml`：

```toml
[tool.uv]
index-url = "https://pypi.tuna.tsinghua.edu.cn/simple"
```

