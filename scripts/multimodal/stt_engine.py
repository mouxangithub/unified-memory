#!/usr/bin/env python3
"""
STT Engine - 语音转文字引擎

支持:
- Whisper (OpenAI)
- 阿里云语音识别
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class STTResult:
    text: str
    segments: List[Dict]  # 时间戳分段
    language: str
    source: str


class STTEngine:
    """语音转文字引擎"""
    
    def __init__(self, engine: str = "auto"):
        self.engine = engine
        self.available = self._check_available()
    
    def _check_available(self) -> Dict[str, bool]:
        """检查可用引擎"""
        engines = {}
        
        # Whisper
        try:
            import whisper
            engines["whisper"] = True
        except:
            engines["whisper"] = False
        
        # 阿里云语音
        import os
        engines["aliyun"] = bool(os.environ.get("ALIYUN_AK"))
        
        return engines
    
    def transcribe(self, audio_path: str, language: str = None) -> STTResult:
        """转录音频"""
        path = Path(audio_path)
        
        if not path.exists():
            raise FileNotFoundError(f"音频不存在: {audio_path}")
        
        # 选择引擎
        if self.engine == "auto":
            if self.available.get("whisper"):
                return self._transcribe_whisper(audio_path, language)
            elif self.available.get("aliyun"):
                return self._transcribe_aliyun(audio_path)
            else:
                raise RuntimeError("没有可用的 STT 引擎")
        
        elif self.engine == "whisper":
            return self._transcribe_whisper(audio_path, language)
        elif self.engine == "aliyun":
            return self._transcribe_aliyun(audio_path)
        else:
            raise ValueError(f"未知引擎: {self.engine}")
    
    def _transcribe_whisper(self, audio_path: str, language: str = None) -> STTResult:
        """Whisper 转录"""
        import whisper
        
        # 加载模型 (tiny/base/small/medium/large)
        model = whisper.load_model("base")
        
        # 转录
        options = {}
        if language:
            options["language"] = language
        
        result = model.transcribe(audio_path, **options)
        
        # 提取分段
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"]
            })
        
        return STTResult(
            text=result["text"],
            segments=segments,
            language=result.get("language", "unknown"),
            source="whisper"
        )
    
    def _transcribe_aliyun(self, audio_path: str) -> STTResult:
        """阿里云语音识别"""
        import os
        import json
        import time
        import requests
        
        ak = os.environ.get("ALIYUN_AK")
        sk = os.environ.get("ALIYUN_SK")
        
        if not ak or not sk:
            raise ValueError("需要设置 ALIYUN_AK 和 ALIYUN_SK")
        
        # 这里简化实现，实际需要调用阿里云语音识别 API
        # 文件上传 -> 获取任务 ID -> 轮询结果
        
        return STTResult(
            text="[阿里云语音识别需要完整实现]",
            segments=[],
            language="zh",
            source="aliyun"
        )


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="STT 引擎")
    parser.add_argument("audio", help="音频路径")
    parser.add_argument("--engine", "-e", default="auto", choices=["auto", "whisper", "aliyun"])
    parser.add_argument("--language", "-l", default=None, help="语言代码 (zh/en)")
    
    args = parser.parse_args()
    
    stt = STTEngine(args.engine)
    
    print(f"可用引擎: {[k for k, v in stt.available.items() if v]}")
    print(f"\n转录中...")
    
    result = stt.transcribe(args.audio, args.language)
    
    print(f"\n来源: {result.source}")
    print(f"语言: {result.language}")
    print(f"\n文本:\n{result.text}")


if __name__ == "__main__":
    main()
