#!/usr/bin/env python3
"""
OCR Engine - 多模态 OCR 引擎

支持:
- Tesseract (开源)
- PaddleOCR (中文优化)
- 阿里云千问 VL (云端 API)
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class OCRResult:
    text: str
    confidence: float
    boxes: List[Dict]  # 文本框坐标
    source: str  # tesseract/paddle/qwen


class OCREngine:
    """统一 OCR 引擎"""
    
    def __init__(self, engine: str = "auto"):
        self.engine = engine
        self.available = self._check_available()
    
    def _check_available(self) -> Dict[str, bool]:
        """检查可用引擎"""
        engines = {}
        
        # Tesseract
        try:
            result = subprocess.run(["tesseract", "--version"], capture_output=True)
            engines["tesseract"] = result.returncode == 0
        except:
            engines["tesseract"] = False
        
        # PaddleOCR
        try:
            from paddleocr import PaddleOCR
            engines["paddle"] = True
        except:
            engines["paddle"] = False
        
        # 阿里云千问 VL (通过 API)
        # 需要 DASHSCOPE_API_KEY
        import os
        engines["qwen"] = bool(os.environ.get("DASHSCOPE_API_KEY"))
        
        return engines
    
    def extract_text(self, image_path: str) -> OCRResult:
        """提取图片中的文字"""
        path = Path(image_path)
        
        if not path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")
        
        # 根据引擎选择
        if self.engine == "auto":
            # 优先级: paddle > tesseract > qwen
            if self.available.get("paddle"):
                return self._ocr_paddle(image_path)
            elif self.available.get("tesseract"):
                return self._ocr_tesseract(image_path)
            elif self.available.get("qwen"):
                return self._ocr_qwen(image_path)
            else:
                raise RuntimeError("没有可用的 OCR 引擎")
        
        elif self.engine == "paddle":
            return self._ocr_paddle(image_path)
        elif self.engine == "tesseract":
            return self._ocr_tesseract(image_path)
        elif self.engine == "qwen":
            return self._ocr_qwen(image_path)
        else:
            raise ValueError(f"未知引擎: {self.engine}")
    
    def _ocr_tesseract(self, image_path: str) -> OCRResult:
        """Tesseract OCR"""
        import subprocess
        
        # 中文支持
        lang = "chi_sim+eng"
        
        result = subprocess.run(
            ["tesseract", image_path, "stdout", "-l", lang, "--psm", "6"],
            capture_output=True,
            text=True
        )
        
        text = result.stdout.strip()
        
        return OCRResult(
            text=text,
            confidence=0.8,  # Tesseract 不返回置信度
            boxes=[],
            source="tesseract"
        )
    
    def _ocr_paddle(self, image_path: str) -> OCRResult:
        """PaddleOCR (中文优化)"""
        from paddleocr import PaddleOCR
        
        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        result = ocr.ocr(image_path, cls=True)
        
        texts = []
        boxes = []
        confidences = []
        
        for line in result[0]:
            box, (text, conf) = line
            texts.append(text)
            boxes.append(box)
            confidences.append(conf)
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        return OCRResult(
            text="\n".join(texts),
            confidence=avg_conf,
            boxes=boxes,
            source="paddle"
        )
    
    def _ocr_qwen(self, image_path: str) -> OCRResult:
        """阿里云千问 VL API"""
        import os
        import base64
        import requests
        
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("需要设置 DASHSCOPE_API_KEY")
        
        # 读取图片
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 调用 API
        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen-vl-max",
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"image": f"data:image/jpeg;base64,{image_data}"},
                                {"text": "请识别图片中的所有文字，按原始排版输出。"}
                            ]
                        }
                    ]
                }
            }
        )
        
        result = response.json()
        text = result["output"]["choices"][0]["message"]["content"][0]["text"]
        
        return OCRResult(
            text=text,
            confidence=0.95,  # 云端 API 通常置信度更高
            boxes=[],
            source="qwen"
        )
    
    def batch_extract(self, image_paths: List[str]) -> List[OCRResult]:
        """批量提取"""
        return [self.extract_text(p) for p in image_paths]


# CLI 入口
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR 引擎")
    parser.add_argument("image", help="图片路径")
    parser.add_argument("--engine", "-e", default="auto", choices=["auto", "tesseract", "paddle", "qwen"])
    
    args = parser.parse_args()
    
    ocr = OCREngine(args.engine)
    
    print(f"可用引擎: {[k for k, v in ocr.available.items() if v]}")
    print(f"\n提取中...")
    
    result = ocr.extract_text(args.image)
    
    print(f"\n来源: {result.source}")
    print(f"置信度: {result.confidence:.2%}")
    print(f"\n文本:\n{result.text}")


if __name__ == "__main__":
    main()
