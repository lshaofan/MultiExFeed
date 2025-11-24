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
            future_to_frame = {}
            for frame in frames:
                # 获取每个周期的 limit
                limit = self.config.get_kline_limit(frame) if self.config else 300
                future_to_frame[executor.submit(self.client.fetch_klines, symbol, frame, limit=limit)] = frame
            
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
                        
                        # Calculate derived metrics (labels)
                        from exdatahub.services.derived_metrics import DerivedMetrics
                        
                        # 获取当前价格（最新K线的收盘价）
                        current_price = None
                        if raw_klines:
                            try:
                                current_price = float(raw_klines[-1][4])  # close price
                            except (IndexError, ValueError, TypeError):
                                pass
                        
                        summary = {
                            "trend_label": DerivedMetrics.get_trend_label(indicators),
                            "volatility_label": DerivedMetrics.get_volatility_label(indicators, current_price),
                            "volume_label": DerivedMetrics.get_volume_label(indicators.get('volume', {}))
                        }
                        
                        result["klines"][frame] = {
                            "data": raw_klines[-5:], # Only show last 5 to avoid huge JSON in console, user can adjust
                            "indicators": indicators,
                            "summary": summary
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
                            
                            # Calculate funding stats
                            from exdatahub.services.derived_metrics import DerivedMetrics
                            stats = DerivedMetrics.calculate_funding_stats(
                                result["derivatives"]["funding_rate"]["history"]
                            )
                            result["derivatives"]["funding_rate"].update(stats)
                    except Exception as e:
                        result["derivatives"]["funding_rate"]["history_error"] = str(e)
        except Exception as e:
            result["derivatives"]["funding_rate"] = {"error": str(e)}

        try:
            oi = self.client.fetch_open_interest(symbol)
            if oi.get("code") == "0" and oi.get("data"):
                oi_data = oi["data"][0]
                current_oi = float(oi_data.get("oi", 0))
                result["derivatives"]["oi"] = {
                    "value": oi_data.get("oi"),
                    "value_usd": oi_data.get("oiCcy"),
                    "ts": oi_data.get("ts")
                }
                
                # Add OI change if history is available
                if self.config and self.config.enable_oi_history:
                    try:
                        oi_history = self.client.fetch_oi_history(
                            symbol,
                            limit=self.config.oi_history_limit
                        )
                        if oi_history.get("code") == "0" and oi_history.get("data"):
                            result["derivatives"]["oi"]["history"] = oi_history["data"]
                            
                            # Calculate OI change
                            from exdatahub.services.derived_metrics import DerivedMetrics
                            change = DerivedMetrics.calculate_oi_change(current_oi, oi_history["data"])
                            result["derivatives"]["oi"].update(change)
                    except Exception as e:
                        result["derivatives"]["oi"]["history_error"] = str(e)
        except Exception as e:
            result["derivatives"]["oi"] = {"error": str(e)}

        try:
            # Mark price and index price
            mark = self.client.fetch_index_tickers(symbol)
            ticker = self.client.fetch_ticker(symbol)
            
            mark_price = None
            index_price = None
            
            if mark.get("code") == "0" and mark.get("data"):
                m_data = mark["data"][0]
                mark_price = m_data.get("markPx")
            
            if ticker.get("code") == "0" and ticker.get("data"):
                t_data = ticker["data"][0]
                index_price = t_data.get("indexPrice") or t_data.get("idxPx")
            
            result["derivatives"]["price"] = {
                "mark": mark_price,
                "index": index_price,
                "ts": m_data.get("ts") if mark.get("data") else None
            }
            
            # Calculate basis
            if mark_price and index_price:
                from exdatahub.services.derived_metrics import DerivedMetrics
                basis = DerivedMetrics.calculate_basis(mark_price, index_price)
                result["derivatives"]["price"].update(basis)
        except Exception as e:
            result["derivatives"]["price"] = {"error": str(e)}

        return result
