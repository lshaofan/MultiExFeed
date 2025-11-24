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
@click.argument('exchange')
@click.argument('symbol')
@click.option('--frames', default='1m,5m,15m,1h,4h,1d', help='Comma-separated kline intervals')
def analyze(exchange, symbol, frames):
    """Analyze market data with indicators.
    
    EXCHANGE: Exchange name (e.g., okx)
    SYMBOL: Trading pair (e.g., BTC-USDT-SWAP)
    """
    try:
        from exdatahub.services.aggregator import AggregatorService
        
        aggregator = AggregatorService(exchange)
        frame_list = [f.strip() for f in frames.split(',')]
        
        result = aggregator.analyze_market(symbol, frame_list)
        
        # Output JSON
        click.echo(json.dumps(result, indent=2))
        
    except Exception as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()
