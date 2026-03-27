#!/usr/bin/env python3
"""
Multimodal Package - 多模态记忆支持

统一入口:
- ImageProcessor - 图片 OCR + embedding
- PDFProcessor - PDF 文本提取
- AudioProcessor - 音频 STT
"""

from .image_processor import ImageProcessor
from .pdf_processor import PDFProcessor
from .audio_processor import AudioProcessor


class MultimodalMemory:
    """多模态记忆统一接口"""
    
    def __init__(self):
        self.image = ImageProcessor()
        self.pdf = PDFProcessor()
        self.audio = AudioProcessor()
    
    def process(self, file_path: str) -> dict:
        """
        自动识别文件类型并处理
        
        Args:
            file_path: 文件路径
        
        Returns:
            处理结果
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']:
            return self.image.process(file_path)
        elif suffix == '.pdf':
            return self.pdf.process(file_path)
        elif suffix in ['.mp3', '.wav', '.m4a', '.ogg', '.flac']:
            return self.audio.process(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {suffix}")
    
    def batch_process(self, file_paths: list) -> list:
        """批量处理文件"""
        results = []
        for fp in file_paths:
            try:
                result = self.process(fp)
                results.append(result)
            except Exception as e:
                results.append({
                    "path": fp,
                    "error": str(e)
                })
        return results


from pathlib import Path

__all__ = [
    'MultimodalMemory',
    'ImageProcessor',
    'PDFProcessor',
    'AudioProcessor'
]
