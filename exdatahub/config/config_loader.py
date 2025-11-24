import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigLoader:
    """配置文件加载器"""
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "default.yaml"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号分隔的嵌套键）"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            
            if value is None:
                return default
        
        return value
    
    @property
    def exchange(self) -> str:
        return self.get('exchange', 'okx')
    
    @property
    def symbol(self) -> str:
        return self.get('symbol', 'BTC-USDT-SWAP')
    
    @property
    def kline_frames(self) -> list:
        """
        获取 K 线周期列表
        支持两种格式：
        1. 旧格式: frames: [1m, 5m, ...]
        2. 新格式: frames: [{frame: 1m, limit: 200}, ...]
        """
        frames_config = self.get('klines.frames', ['1m', '5m', '15m', '1H', '4H', '1D'])
        
        # 检查是否是新格式
        if frames_config and isinstance(frames_config[0], dict):
            # 新格式：返回 frame 字段列表
            return [item['frame'] for item in frames_config]
        else:
            # 旧格式：直接返回
            return frames_config
    
    def get_kline_limit(self, frame: str) -> int:
        """
        获取指定周期的 limit
        
        Args:
            frame: 周期（如 1m, 5m）
        
        Returns:
            limit 数量
        """
        frames_config = self.get('klines.frames', [])
        
        # 检查是否是新格式
        if frames_config and isinstance(frames_config[0], dict):
            # 新格式：查找对应 frame 的 limit
            for item in frames_config:
                if item.get('frame') == frame:
                    return item.get('limit', 300)
            return 300  # 默认值
        else:
            # 旧格式：使用全局 limit
            return self.get('klines.limit', 300)
    
    @property
    def kline_limit(self) -> int:
        return self.get('klines.limit', 300)
    
    @property
    def output_mode(self) -> str:
        return self.get('output.mode', 'console')
    
    @property
    def output_directory(self) -> str:
        return self.get('output.directory', 'output')
    
    @property
    def enable_funding_history(self) -> bool:
        return self.get('derivatives.enable_funding_history', False)
    
    @property
    def funding_history_limit(self) -> int:
        return self.get('derivatives.funding_history_limit', 24)
    
    @property
    def enable_oi_history(self) -> bool:
        return self.get('derivatives.enable_oi_history', False)
    
    @property
    def oi_history_limit(self) -> int:
        return self.get('derivatives.oi_history_limit', 24)
