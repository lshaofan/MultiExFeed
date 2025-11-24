import requests
import hmac
import base64
import datetime
import json
from typing import Dict, Any, Optional
from exdatahub.exchanges.base import BaseExchangeClient
from exdatahub.core.exceptions import APIError

class OKXClient(BaseExchangeClient):
    """OKX V5 API Client."""
    
    BASE_URL = "https://www.okx.com"
    
    def __init__(self, api_key: str = "", secret_key: str = "", passphrase: str = "", proxy: Optional[str] = None):
        super().__init__(api_key, secret_key, passphrase, proxy)
        self.proxies = {"http": proxy, "https": proxy} if proxy else None

    def _get_timestamp(self) -> str:
        return datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z'

    def _sign(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        if not self.secret_key:
            return ""
        message = f"{timestamp}{method}{request_path}{body}"
        mac = hmac.new(
            bytes(self.secret_key, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()

    def _request(self, method: str, path: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"
        
        # Public endpoints don't strictly need auth for market data, 
        # but good to have if we extend to private later.
        # For now, we'll skip auth headers if keys aren't provided.
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.api_key and self.secret_key and self.passphrase:
            timestamp = self._get_timestamp()
            # For GET requests, params are in query string, body is empty
            # If we had POST, we'd need to handle body
            sign_path = path
            if params:
                query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                sign_path = f"{path}?{query_string}"
                
            signature = self._sign(timestamp, method, sign_path)
            headers.update({
                "OK-ACCESS-KEY": self.api_key,
                "OK-ACCESS-SIGN": signature,
                "OK-ACCESS-TIMESTAMP": timestamp,
                "OK-ACCESS-PASSPHRASE": self.passphrase,
            })

        try:
            response = requests.request(
                method, 
                url, 
                params=params, 
                headers=headers, 
                proxies=self.proxies,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != "0":
                raise APIError(f"OKX API Error: {data.get('msg')} (code: {data.get('code')})")
                
            return data
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network Error: {str(e)}")

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch ticker.
        OKX API: GET /api/v5/market/ticker?instId={symbol}
        """
        path = "/api/v5/market/ticker"
        params = {"instId": symbol}
        return self._request("GET", path, params)

    def fetch_klines(self, symbol: str, interval: str, limit: int = 100) -> Dict[str, Any]:
        """
        Fetch klines.
        OKX API: GET /api/v5/market/candles?instId={symbol}&bar={interval}&limit={limit}
        
        Note: OKX bar parameter is case-sensitive:
        - Lowercase for minutes: 1m, 5m, 15m, 30m
        - Uppercase for hours/days: 1H, 4H, 1D, 1W, etc.
        """
        path = "/api/v5/market/candles"
        params = {
            "instId": symbol,
            "bar": interval,  # Keep the interval as-is, it should already be correct
            "limit": str(limit)
        }
        return self._request("GET", path, params)

    def fetch_orderbook(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch orderbook.
        OKX API: GET /api/v5/market/books?instId={symbol}&sz={limit}
        """
        path = "/api/v5/market/books"
        params = {
            "instId": symbol,
            "sz": str(limit)
        }
        return self._request("GET", path, params)

    def fetch_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch funding rate.
        OKX API: GET /api/v5/public/funding-rate?instId={symbol}
        """
        path = "/api/v5/public/funding-rate"
        params = {"instId": symbol}
        return self._request("GET", path, params)

    def fetch_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch open interest.
        OKX API: GET /api/v5/public/open-interest?instId={symbol}
        """
        path = "/api/v5/public/open-interest"
        params = {"instId": symbol}
        return self._request("GET", path, params)

    def fetch_index_tickers(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch index tickers (mark price, index price).
        OKX API: GET /api/v5/public/mark-price?instId={symbol}
        Note: OKX separates mark price and index price. 
        Mark price: /api/v5/public/mark-price
        Index price: /api/v5/market/index-tickers (requires index symbol, e.g. BTC-USD)
        For simplicity, we'll fetch mark price here which often includes index price or we can fetch ticker.
        Actually, 'ticker' endpoint already has last, open, high, low, vol.
        Let's fetch mark price specifically.
        """
        path = "/api/v5/public/mark-price"
        params = {"instId": symbol}
        return self._request("GET", path, params)

    def fetch_funding_rate_history(self, symbol: str, limit: int = 24) -> Dict[str, Any]:
        """
        Fetch funding rate history.
        OKX API: GET /api/v5/public/funding-rate-history?instId={symbol}&limit={limit}
        """
        path = "/api/v5/public/funding-rate-history"
        params = {
            "instId": symbol,
            "limit": str(limit)
        }
        return self._request("GET", path, params)

    def fetch_oi_history(self, symbol: str, period: str = "5m", limit: int = 24) -> Dict[str, Any]:
        """
        Fetch open interest history.
        OKX API: GET /api/v5/rubik/stat/contracts/open-interest-history
        Note: This might require special permissions
        """
        path = "/api/v5/rubik/stat/contracts/open-interest-history"
        params = {
            "instId": symbol,
            "period": period,
            "limit": str(limit)
        }
        return self._request("GET", path, params)

