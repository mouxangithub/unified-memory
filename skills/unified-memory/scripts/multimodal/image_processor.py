#!/usr/bin/env python3
"""
Image Processor - 图片处理模块

功能:
- OCR 文字提取
- CLIP embedding
- 自动存储到记忆系统
"""

import sys
from pathlib import Path
from typing import Dict, Optional
import base64

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self):
        self.ocr_available = self._check_ocr()
    
    def _check_ocr(self) -> bool:
        """检查 OCR 是否可用"""
        try:
            import pytesseract
            from PIL import Image
            return True
        except ImportError:
            return False
    
    def process(self, image_path: str) -> Dict:
        """
        处理图片
        
        Returns:
            {
                "text": "OCR 提取的文字",
                "embedding": [0.1, 0.2, ...],  # CLIP embedding
                "memory_id": "img_xxx",
                "metadata": {...}
            }
        """
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        result = {
            "path": str(path),
            "filename": path.name,
            "processed_at": datetime.now().isoformat(),
            "text": "",
            "embedding": None,
            "memory_id": None,
            "metadata": {
                "size": path.stat().st_size,
                "extension": path.suffix
            }
        }
        
        # OCR 提取文字
        result["text"] = self._extract_text(path)
        
        # 生成 embedding（如果可用）
        result["embedding"] = self._get_clip_embedding(path)
        
        # 存储到记忆系统
        result["memory_id"] = self._store_memory(result)
        
        return result
    
    def _extract_text(self, image_path: Path) -> str:
        """OCR 提取文字"""
        if not self.ocr_available:
            return f"[图片: {image_path.name}]"
        
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            return text.strip()
        except Exception as e:
            return f"[OCR 失败: {e}]"
    
    def _get_clip_embedding(self, image_path: Path) -> Optional[list]:
        """获取 CLIP embedding"""
        try:
            # 尝试使用 Ollama 的 CLIP 模型
            import requests
            
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            
            response = requests.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": "clip-vit-base",
                    "image": img_data
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("embedding")
        except:
            pass
        
        return None
    
    def _store_memory(self, result: Dict) -> str:
        """存储到记忆系统"""
        try:
            from unified_interface import UnifiedMemory
            um = UnifiedMemory()
            
            # 构建记忆文本
            text = f"[图片记忆]\n文件: {result['filename']}\n"
            if result['text']:
                text += f"OCR 文字:\n{result['text']}\n"
            
            memory_id = um.quick_store(text, category="image")
            return memory_id
        except Exception as e:
            print(f"存储失败: {e}")
            return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="图片处理")
    parser.add_argument("image", help="图片路径")
    parser.add_argument("--store", action="store_true", help="存储到记忆系统")
    
    args = parser.parse_args()
    
    processor = ImageProcessor()
    result = processor.process(args.image)
    
    print(f"✅ 处理完成:")
    print(f"   文件: {result['filename']}")
    print(f"   OCR 文字: {len(result['text'])} 字符")
    print(f"   记忆ID: {result['memory_id']}")
    
    if args.store:
        print(f"\n记忆内容:")
        print(result['text'][:200])


if __name__ == "__main__":
    main()
