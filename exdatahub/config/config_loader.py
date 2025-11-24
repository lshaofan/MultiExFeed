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
        return self.get('klines.frames', ['1m', '5m', '15m', '1H', '4H', '1D'])
    
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
