"""
衍生指标计算模块
计算变化率、统计信息和标签
"""
from typing import Dict, Any, List, Optional

class DerivedMetrics:
    """衍生指标计算器"""
    
    @staticmethod
    def calculate_funding_stats(history: List[Dict]) -> Dict[str, Optional[float]]:
        """
        计算资金费率统计信息
        
        Args:
            history: 资金费率历史 [{"ts": ..., "rate": ...}, ...]
        
        Returns:
            {"8h_avg": ..., "24h_avg": ..., "24h_sum": ...}
        """
        if not history or len(history) < 1:
            return {"8h_avg": None, "24h_avg": None, "24h_sum": None}
        
        rates = [float(item['rate']) for item in history if item.get('rate')]
        
        result = {
            "8h_avg": None,
            "24h_avg": None,
            "24h_sum": None
        }
        
        if len(rates) >= 8:
            result["8h_avg"] = sum(rates[:8]) / 8
        
        if len(rates) >= 24:
            result["24h_avg"] = sum(rates[:24]) / 24
            result["24h_sum"] = sum(rates[:24])
        
        return result
    
    @staticmethod
    def calculate_oi_change(current: float, history: List[Dict]) -> Dict[str, Optional[float]]:
        """
        计算 OI 变化
        
        Args:
            current: 当前 OI
            history: OI 历史 [{"ts": ..., "oi": ...}, ...]
        
        Returns:
            {"change_24h": ..., "change_24h_pct": ...}
        """
        if not history or len(history) < 24:
            return {"change_24h": None, "change_24h_pct": None}
        
        try:
            oi_24h_ago = float(history[23]['oi'])
            change = current - oi_24h_ago
            change_pct = (change / oi_24h_ago) * 100 if oi_24h_ago != 0 else 0
            
            return {
                "change_24h": round(change, 2),
                "change_24h_pct": round(change_pct, 2)
            }
        except (KeyError, ValueError, TypeError):
            return {"change_24h": None, "change_24h_pct": None}
    
    @staticmethod
    def calculate_basis(mark_price: float, index_price: float) -> Dict[str, Optional[float]]:
        """
        计算 basis（mark - index）
        
        Args:
            mark_price: 标记价格
            index_price: 指数价格
        
        Returns:
            {"basis": ..., "basis_pct": ...}
        """
        if not mark_price or not index_price:
            return {"basis": None, "basis_pct": None}
        
        try:
            mark = float(mark_price)
            index = float(index_price)
            basis = mark - index
            basis_pct = (basis / index) * 100 if index != 0 else 0
            
            return {
                "basis": round(basis, 2),
                "basis_pct": round(basis_pct, 4)
            }
        except (ValueError, TypeError):
            return {"basis": None, "basis_pct": None}
    
    @staticmethod
    def get_trend_label(indicators: Dict) -> str:
        """
        根据 EMA 排列判断趋势
        
        Args:
            indicators: 指标数据
        
        Returns:
            "up" / "down" / "sideways"
        """
        try:
            trend = indicators.get('trend', {})
            ema9 = trend.get('ema_9')
            ema21 = trend.get('ema_21')
            ema50 = trend.get('ema_50')
            
            if not all([ema9, ema21, ema50]):
                return "unknown"
            
            # 多头排列
            if ema9 > ema21 > ema50:
                return "up"
            # 空头排列
            elif ema9 < ema21 < ema50:
                return "down"
            else:
                return "sideways"
        except (KeyError, TypeError):
            return "unknown"
    
    @staticmethod
    def get_volatility_label(indicators: Dict, current_price: float = None) -> str:
        """
        根据 ATR 或布林带宽度判断波动率
        
        Args:
            indicators: 指标数据
            current_price: 当前价格（用于计算相对波动率）
        
        Returns:
            "high" / "normal" / "low"
        """
        try:
            volatility = indicators.get('volatility', {})
            atr = volatility.get('atr_14')
            bb_upper = volatility.get('bb_upper')
            bb_lower = volatility.get('bb_lower')
            
            # 优先使用布林带宽度
            if bb_upper and bb_lower and current_price:
                bb_width = bb_upper - bb_lower
                bb_width_pct = (bb_width / current_price) * 100
                
                # 经验阈值（可调整）
                if bb_width_pct > 3:
                    return "high"
                elif bb_width_pct < 1:
                    return "low"
                else:
                    return "normal"
            
            # 备用：使用 ATR
            if atr and current_price:
                atr_pct = (atr / current_price) * 100
                
                if atr_pct > 2:
                    return "high"
                elif atr_pct < 0.5:
                    return "low"
                else:
                    return "normal"
            
            return "unknown"
        except (KeyError, TypeError, ZeroDivisionError):
            return "unknown"
    
    @staticmethod
    def get_volume_label(volume_data: Dict) -> str:
        """
        根据成交量判断量能
        
        Args:
            volume_data: 成交量数据 {"vol": ..., "vol_ma_20": ...}
        
        Returns:
            "high" / "normal" / "low"
        """
        try:
            vol = volume_data.get('vol')
            vol_ma = volume_data.get('vol_ma_20')
            
            if not vol or not vol_ma:
                return "unknown"
            
            ratio = vol / vol_ma if vol_ma != 0 else 0
            
            if ratio > 1.5:
                return "high"
            elif ratio < 0.5:
                return "low"
            else:
                return "normal"
        except (KeyError, TypeError, ZeroDivisionError):
            return "unknown"
