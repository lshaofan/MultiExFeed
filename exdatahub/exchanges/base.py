from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseExchangeClient(ABC):
    """Abstract base class for all exchange clients."""
    
    def __init__(self, api_key: str = "", secret_key: str = "", passphrase: str = "", proxy: Optional[str] = None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.proxy = proxy

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Fetch ticker data for a symbol."""
        pass

    @abstractmethod
    def fetch_klines(self, symbol: str, interval: str, limit: int = 100) -> Dict[str, Any]:
        """Fetch kline (candlestick) data."""
        pass

    @abstractmethod
    def fetch_orderbook(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """Fetch orderbook data."""
        pass
