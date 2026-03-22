#!/usr/bin/env python3
"""
Audio Processor - 音频处理模块

功能:
- STT (语音转文字)
- 自动存储到记忆系统
"""

import sys
from pathlib import Path
from typing import Dict, Optional
import tempfile
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime


class AudioProcessor:
    """音频处理器"""
    
    def __init__(self):
        self.stt_available = self._check_stt()
    
    def _check_stt(self) -> bool:
        """检查 STT 是否可用"""
        # 检查 whisper
        try:
            result = subprocess.run(
                ["which", "whisper"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def process(self, audio_path: str) -> Dict:
        """
        处理音频
        
        Returns:
            {
                "text": "转录文字",
                "duration": 120.5,
                "memory_id": "audio_xxx",
                "metadata": {...}
            }
        """
        path = Path(audio_path)
        
        if not path.exists():
            raise FileNotFoundError(f"音频不存在: {audio_path}")
        
        result = {
            "path": str(path),
            "filename": path.name,
            "processed_at": datetime.now().isoformat(),
            "text": "",
            "duration": 0,
            "memory_id": None,
            "metadata": {
                "size": path.stat().st_size,
                "extension": path.suffix
            }
        }
        
        # 转录
        result["text"] = self._transcribe(path)
        
        # 获取时长
        result["duration"] = self._get_duration(path)
        
        # 存储到记忆系统
        result["memory_id"] = self._store_memory(result)
        
        return result
    
    def _transcribe(self, audio_path: Path) -> str:
        """转录音频"""
        if not self.stt_available:
            return f"[音频: {audio_path.name} - STT 不可用]"
        
        try:
            # 使用 whisper
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
                tmp_path = tmp.name
            
            result = subprocess.run(
                ["whisper", str(audio_path), "--output_format", "txt", "--output_dir", tempfile.gettempdir()],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # 读取输出
            output_file = Path(tempfile.gettempdir()) / f"{audio_path.stem}.txt"
            if output_file.exists():
                text = output_file.read_text()
                output_file.unlink()
                return text.strip()
            
        except Exception as e:
            return f"[转录失败: {e}]"
        
        return f"[音频: {audio_path.name}]"
    
    def _get_duration(self, audio_path: Path) -> float:
        """获取音频时长"""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except:
            return 0
    
    def _store_memory(self, result: Dict) -> str:
        """存储到记忆系统"""
        try:
            from unified_interface import UnifiedMemory
            um = UnifiedMemory()
            
            # 构建记忆文本
            text = f"[音频记忆]\n文件: {result['filename']}\n"
            text += f"时长: {result['duration']:.1f} 秒\n\n"
            text += f"转录内容:\n{result['text']}"
            
            memory_id = um.quick_store(text, category="audio")
            return memory_id
        except Exception as e:
            print(f"存储失败: {e}")
            return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="音频处理")
    parser.add_argument("audio", help="音频路径")
    parser.add_argument("--store", action="store_true", help="存储到记忆系统")
    
    args = parser.parse_args()
    
    processor = AudioProcessor()
    result = processor.process(args.audio)
    
    print(f"✅ 处理完成:")
    print(f"   文件: {result['filename']}")
    print(f"   时长: {result['duration']:.1f} 秒")
    print(f"   转录: {len(result['text'])} 字符")
    print(f"   记忆ID: {result['memory_id']}")
    
    if args.store:
        print(f"\n转录内容:")
        print(result['text'][:300])


if __name__ == "__main__":
    main()
