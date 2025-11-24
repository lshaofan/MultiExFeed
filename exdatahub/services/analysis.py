import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Any

class AnalysisService:
    @staticmethod
    def calculate_indicators(klines: List[List[str]]) -> Dict[str, Any]:
        """
        Calculate technical indicators from raw kline data.
        
        Args:
            klines: List of kline data [ts, open, high, low, close, vol, ...]
            
        Returns:
            Dict containing the last values of calculated indicators.
        """
        if not klines:
            return {}

        # Convert to DataFrame
        # OKX Kline format: [ts, open, high, low, close, vol, volCcy, volCcyQuote, confirm]
        df = pd.DataFrame(klines, columns=['ts', 'open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcyQuote', 'confirm'])
        
        # Convert types
        numeric_cols = ['open', 'high', 'low', 'close', 'vol']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])
            
        # Calculate Indicators
        
        # 1. Trend
        df['EMA_9'] = ta.ema(df['close'], length=9)
        df['EMA_21'] = ta.ema(df['close'], length=21)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['MA_100'] = ta.ma('sma', df['close'], length=100)
        df['MA_200'] = ta.ma('sma', df['close'], length=200)

        # 2. Volatility
        # Bollinger Bands (20, 2)
        bb = ta.bbands(df['close'], length=20, std=2)
        if bb is not None:
            df = pd.concat([df, bb], axis=1)
            # pandas_ta column names: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
            # But sometimes it might be BBL_20_2, BBU_20_2 (without .0)
            # Let's find the actual column names
            bb_cols = [col for col in df.columns if 'BB' in col]

        # ATR (14)
        df['ATR_14'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        # 3. Momentum
        # RSI (14)
        df['RSI_14'] = ta.rsi(df['close'], length=14)
        
        # MACD (12, 26, 9)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df = pd.concat([df, macd], axis=1)

        # 4. Volume
        df['VOL_MA_20'] = ta.sma(df['vol'], length=20)

        # Get the last row (latest data)
        last_row = df.iloc[-1]
        
        # Helper to safely get value
        def get_val(row, key):
            val = row.get(key)
            return float(val) if pd.notna(val) else None
        
        # Helper to find BB columns (handle different naming conventions)
        def find_bb_col(prefix):
            cols = [col for col in df.columns if col.startswith(prefix)]
            if cols:
                return cols[0]
            return None
        
        bb_upper_col = find_bb_col('BBU')
        bb_lower_col = find_bb_col('BBL')
        
        # Construct result
        return {
            "trend": {
                "ema_9": get_val(last_row, 'EMA_9'),
                "ema_21": get_val(last_row, 'EMA_21'),
                "ema_50": get_val(last_row, 'EMA_50'),
                "ma_100": get_val(last_row, 'MA_100'),
                "ma_200": get_val(last_row, 'MA_200'),
            },
            "volatility": {
                "bb_upper": get_val(last_row, bb_upper_col) if bb_upper_col else None,
                "bb_lower": get_val(last_row, bb_lower_col) if bb_lower_col else None,
                "atr_14": get_val(last_row, 'ATR_14'),
            },
            "momentum": {
                "rsi_14": get_val(last_row, 'RSI_14'),
                "macd": get_val(last_row, 'MACD_12_26_9'),
                "macd_signal": get_val(last_row, 'MACDs_12_26_9'),
                "macd_hist": get_val(last_row, 'MACDh_12_26_9'),
            },
            "volume": {
                "vol": get_val(last_row, 'vol'),
                "vol_ma_20": get_val(last_row, 'VOL_MA_20'),
            }
        }
