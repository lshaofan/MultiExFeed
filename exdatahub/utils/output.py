import os
import json
import datetime
import random
import string
from pathlib import Path
from typing import Dict, Any

class OutputHandler:
    """输出处理器"""
    
    @staticmethod
    def generate_filename(prefix: str = "") -> str:
        """
        生成文件名：2025-11-24-23-02_abc123.json
        如果同一分钟内有多次调用，通过随机字符串区分
        """
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d-%H-%M")
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        if prefix:
            return f"{prefix}_{timestamp}_{random_str}.json"
        return f"{timestamp}_{random_str}.json"
    
    @staticmethod
    def save_to_file(data: Dict[str, Any], directory: str = "output", filename: str = None) -> str:
        """
        保存数据到 JSON 文件
        
        Args:
            data: 要保存的数据
            directory: 输出目录
            filename: 文件名（如果为 None 则自动生成）
        
        Returns:
            保存的文件路径
        """
        # 创建输出目录
        output_dir = Path(directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        if filename is None:
            filename = OutputHandler.generate_filename()
        
        # 完整路径
        filepath = output_dir / filename
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    @staticmethod
    def output(data: Dict[str, Any], mode: str = "console", directory: str = "output") -> str:
        """
        统一输出接口
        
        Args:
            data: 数据
            mode: 输出模式 (console 或 file)
            directory: 文件输出目录
        
        Returns:
            如果是 file 模式，返回文件路径；否则返回空字符串
        """
        if mode == "file":
            filepath = OutputHandler.save_to_file(data, directory)
            print(f"✅ Data saved to: {filepath}")
            return filepath
        else:
            # console 模式
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return ""
