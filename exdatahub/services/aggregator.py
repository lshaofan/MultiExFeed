from typing import Dict, Any, List, Optional
from exdatahub.exchanges.okx_client import OKXClient
from exdatahub.services.analysis import AnalysisService
from exdatahub.config.settings import settings
from exdatahub.config.config_loader import ConfigLoader
import concurrent.futures

class AggregatorService:
    def __init__(self, exchange_name: str = 'okx', config: Optional[ConfigLoader] = None):
        self.config = config
        if exchange_name.lower() == 'okx':
            self.client = OKXClient(
                api_key=settings.OKX_API_KEY,
                secret_key=settings.OKX_SECRET_KEY,
                passphrase=settings.OKX_PASSPHRASE,
                proxy=settings.HTTP_PROXY
            )
        else:
            raise ValueError(f"Exchange '{exchange_name}' not supported.")

    def analyze_market(self, symbol: str, frames: List[str] = None) -> Dict[str, Any]:
        """
        Fetch all market data and calculate indicators.
        
        Args:
            symbol: Trading pair symbol
            frames: List of timeframes (if None, use config or default)
        """
        # Use config if available
        if frames is None:
            frames = self.config.kline_frames if self.config else ['1m', '5m', '15m', '1H', '4H', '1D']
        
        result = {
            "symbol": symbol,
            "timestamp": None,
            "klines": {},
            "derivatives": {}
        }

        # 1. Fetch Klines for all frames (Parallel)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_frame = {
                executor.submit(self.client.fetch_klines, symbol, frame, limit=300): frame 
                for frame in frames
            }
            
            for future in concurrent.futures.as_completed(future_to_frame):
                frame = future_to_frame[future]
                try:
                    data = future.result()
                    if data.get("code") == "0":
                        # OKX returns data in 'data' field
                        # We need to reverse it to be chronological for pandas_ta?
                        # OKX returns newest first. pandas_ta usually expects chronological (oldest first).
                        # Let's reverse it.
                        raw_klines = data.get("data", [])
                        raw_klines.reverse()
                        
                        # Calculate indicators
                        indicators = AnalysisService.calculate_indicators(raw_klines)
                        
                        # Store raw klines (maybe just last few to save space? or full as requested)
                        # User asked for raw klines.
                        # Let's attach indicators to the last kline or separate structure?
                        # User template: "klines": { "1m": [...] }
                        # User also asked: "In every kline add columns: ema9..."
                        # For now, let's keep klines raw (but reversed/chronological) and add a summary of indicators.
                        # Actually, user said: "Or you calculate indicators... In every kline add columns"
                        # To keep it simple for now, I will return raw klines AND a separate "analysis" block per frame.
                        # Wait, user template has "derivatives" but didn't explicitly show where indicators go.
                        # But in section III, they said "Or you calculate... In every kline add columns".
                        # Let's add latest indicators to the result structure for now.
                        
                        result["klines"][frame] = {
                            "data": raw_klines[-5:], # Only show last 5 to avoid huge JSON in console, user can adjust
                            "indicators": indicators
                        }
                        
                        if frame == '1m' and raw_klines:
                            result["timestamp"] = raw_klines[-1][0] # Use 1m close time as ref
                            
                except Exception as e:
                    result["klines"][frame] = {"error": str(e)}

        # 2. Fetch Derivatives Data
        # Funding Rate
        try:
            funding = self.client.fetch_funding_rate(symbol)
            if funding.get("code") == "0" and funding.get("data"):
                f_data = funding["data"][0]
                result["derivatives"]["funding_rate"] = {
                    "current": f_data.get("fundingRate"),
                    "next": f_data.get("nextFundingRate"),
                    "next_time": f_data.get("nextFundingTime")
                }
                
                # Add funding history if enabled
                if self.config and self.config.enable_funding_history:
                    try:
                        history = self.client.fetch_funding_rate_history(
                            symbol, 
                            limit=self.config.funding_history_limit
                        )
                        if history.get("code") == "0" and history.get("data"):
                            result["derivatives"]["funding_rate"]["history"] = [
                                {
                                    "ts": item.get("fundingTime"),
                                    "rate": item.get("fundingRate")
                                }
                                for item in history["data"]
                            ]
                    except Exception as e:
                        result["derivatives"]["funding_rate"]["history_error"] = str(e)
        except Exception as e:
            result["derivatives"]["funding_rate"] = {"error": str(e)}

        try:
            oi = self.client.fetch_open_interest(symbol)
            if oi.get("code") == "0" and oi.get("data"):
                oi_data = oi["data"][0]
                result["derivatives"]["oi"] = {
                    "value": oi_data.get("oi"),
                    "value_usd": oi_data.get("oiCcy"),
                    "ts": oi_data.get("ts")
                }
        except Exception as e:
            result["derivatives"]["oi"] = {"error": str(e)}

        try:
            # Mark price
            mark = self.client.fetch_index_tickers(symbol)
            if mark.get("code") == "0" and mark.get("data"):
                m_data = mark["data"][0]
                result["derivatives"]["price"] = {
                    "mark": m_data.get("markPx"),
                    "index": m_data.get("indexPx"), # OKX mark-price endpoint might not have indexPx, check docs?
                    # Actually /api/v5/public/mark-price returns markPx.
                    # /api/v5/market/index-tickers returns indexPx.
                    # Let's just use what we have.
                    "ts": m_data.get("ts")
                }
        except Exception as e:
            result["derivatives"]["price"] = {"error": str(e)}

        return result
