import click
import json
import sys
from exdatahub.config.settings import settings

@click.group()
def cli():
    """ExDataHub CLI - Multi-Exchange Data Gateway"""
    pass

@click.command()
@click.argument('exchange')
@click.argument('data_type')
@click.argument('symbol')
@click.option('--interval', default='1m', help='Kline interval (e.g., 1m, 1h, 1d)')
@click.option('--limit', default=100, help='Number of data points to fetch')
def fetch(exchange, data_type, symbol, interval, limit):
    """Fetch market data from an exchange.
    
    EXCHANGE: Exchange name (e.g., okx)
    DATA_TYPE: Data type (ticker, kline, orderbook)
    SYMBOL: Trading pair (e.g., BTC-USDT)
    """
    try:
        client = None
        if exchange.lower() == 'okx':
            from exdatahub.exchanges.okx_client import OKXClient
            client = OKXClient(
                api_key=settings.OKX_API_KEY,
                secret_key=settings.OKX_SECRET_KEY,
                passphrase=settings.OKX_PASSPHRASE,
                proxy=settings.HTTP_PROXY
            )
        else:
            raise ValueError(f"Exchange '{exchange}' not supported.")

        data = {}
        if data_type == 'ticker':
            data = client.fetch_ticker(symbol)
        elif data_type == 'kline':
            data = client.fetch_klines(symbol, interval, limit)
        elif data_type == 'orderbook':
            data = client.fetch_orderbook(symbol, limit)
        else:
            raise ValueError(f"Data type '{data_type}' not supported.")
        
        # Output JSON
        click.echo(json.dumps(data, indent=2))
        
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

@cli.command()
@click.argument('exchange', required=False)
@click.argument('symbol', required=False)
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径 (YAML)')
@click.option('--frames', default=None, help='K线周期 (逗号分隔)')
@click.option('--output-mode', type=click.Choice(['console', 'file']), help='输出模式')
def analyze(exchange, symbol, config, frames, output_mode):
    """分析市场数据并计算技术指标
    
    示例:
        使用配置文件: analyze --config config/my_strategy.yaml
        直接指定参数: analyze okx BTC-USDT-SWAP
    """
    try:
        from exdatahub.services.aggregator import AggregatorService
        from exdatahub.config.config_loader import ConfigLoader
        from exdatahub.utils.output import OutputHandler
        
        # 加载配置
        cfg = ConfigLoader(config) if config else None
        
        # 从配置或参数获取交易所和交易对
        exchange_name = exchange or (cfg.exchange if cfg else 'okx')
        trading_symbol = symbol or (cfg.symbol if cfg else 'BTC-USDT-SWAP')
        
        # 获取输出模式
        mode = output_mode or (cfg.output_mode if cfg else 'console')
        output_dir = cfg.output_directory if cfg else 'output'
        
        # 创建聚合器
        aggregator = AggregatorService(exchange_name, config=cfg)
        
        # 解析周期
        frame_list = None
        if frames:
            frame_list = [f.strip() for f in frames.split(',')]
        
        # 获取数据
        result = aggregator.analyze_market(trading_symbol, frame_list)
        
        # 输出
        OutputHandler.output(result, mode=mode, directory=output_dir)
        
    except Exception as e:
        error_data = {"error": str(e)}
        click.echo(json.dumps(error_data), err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()
