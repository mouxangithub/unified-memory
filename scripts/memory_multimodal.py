#!/usr/bin/env python3
"""
Memory Multimodal - 多模态记忆 v0.2.0

功能:
- 图片记忆（存储图片描述）
- 语音记忆（语音转文字）
- 文件记忆（文件信息提取）
- 支持多种格式

Usage:
    python3 scripts/memory_multimodal.py store-image image.png --desc "截图"
    python3 scripts/memory_multimodal.py store-audio audio.mp3
    python3 scripts/memory_multimodal.py store-file document.pdf
    python3 scripts/memory_multimodal.py list --type image
"""

import argparse
import json
import os
import sys
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
MEDIA_DIR = MEMORY_DIR / "media"

# 媒体类型
MEDIA_TYPES = {
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    "audio": [".mp3", ".wav", ".m4a", ".ogg", ".flac"],
    "video": [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    "document": [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".md"]
}

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

try:
    import lancedb
    import requests
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


def get_file_type(file_path: str) -> Optional[str]:
    """获取文件类型"""
    ext = Path(file_path).suffix.lower()
    for media_type, extensions in MEDIA_TYPES.items():
        if ext in extensions:
            return media_type
    return None


def compute_file_hash(file_path: str) -> str:
    """计算文件哈希"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def copy_to_media(file_path: str, media_type: str) -> str:
    """复制文件到媒体目录"""
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    type_dir = MEDIA_DIR / media_type
    type_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用哈希命名
    file_hash = compute_file_hash(file_path)
    ext = Path(file_path).suffix
    new_name = f"{file_hash}{ext}"
    new_path = type_dir / new_name
    
    # 如果已存在则跳过
    if new_path.exists():
        return str(new_path)
    
    # 复制文件
    import shutil
    shutil.copy2(file_path, new_path)
    
    return str(new_path)


def describe_image(image_path: str) -> str:
    """描述图片（使用 LLM Vision）"""
    try:
        # 读取图片
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        # 调用视觉模型
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": "llava:13b",  # 或其他视觉模型
                "prompt": "描述这张图片的内容，简洁直接:",
                "images": [image_data],
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        pass
    
    return "图片内容（自动描述不可用）"


def transcribe_audio(audio_path: str) -> str:
    """语音转文字"""
    try:
        # 使用 Whisper 或其他模型
        # 这里简化处理，实际需要调用 ASR 服务
        response = requests.post(
            f"{OLLAMA_HOST}/api/transcribe",
            json={
                "audio": audio_path
            },
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json().get("text", "")
    except:
        pass
    
    return "语音内容（转录不可用）"


def extract_file_info(file_path: str) -> str:
    """提取文件信息"""
    path = Path(file_path)
    stat = path.stat()
    
    info = {
        "name": path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": path.suffix
    }
    
    # 根据文件类型提取更多信息
    if path.suffix == ".pdf":
        info["type"] = "PDF 文档"
    elif path.suffix in [".docx", ".doc"]:
        info["type"] = "Word 文档"
    elif path.suffix in [".xlsx", ".xls"]:
        info["type"] = "Excel 表格"
    elif path.suffix == ".md":
        info["type"] = "Markdown 文档"
    else:
        info["type"] = "文件"
    
    return json.dumps(info, ensure_ascii=False)


def store_memory(
    content: str,
    media_type: str = "text",
    media_path: Optional[str] = None,
    category: str = "general",
    importance: float = 0.5
) -> bool:
    """存储记忆"""
    if not HAS_DEPS:
        print("❌ 缺少依赖")
        return False
    
    try:
        import uuid
        
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        
        # 存储元数据
        metadata = {
            "type": media_type,
            "original_path": media_path
        }
        
        table.add([{
            "id": str(uuid.uuid4()),
            "text": content,
            "category": category,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "vector": []
        }])
        
        return True
    except Exception as e:
        print(f"❌ 存储失败: {e}")
        return False


def store_image(image_path: str, description: Optional[str] = None) -> Dict:
    """存储图片记忆"""
    # 复制文件
    media_path = copy_to_media(image_path, "image")
    
    # 生成描述
    if not description:
        description = describe_image(image_path)
    
    # 存储记忆
    content = f"[图片] {description}"
    success = store_memory(content, "image", media_path, "media", 0.6)
    
    return {
        "path": media_path,
        "description": description,
        "success": success
    }


def store_audio(audio_path: str, description: Optional[str] = None) -> Dict:
    """存储语音记忆"""
    # 复制文件
    media_path = copy_to_media(audio_path, "audio")
    
    # 转录
    transcription = transcribe_audio(audio_path)
    
    # 存储记忆
    content = f"[语音] {description or transcription}"
    success = store_memory(content, "audio", media_path, "media", 0.6)
    
    return {
        "path": media_path,
        "transcription": transcription,
        "success": success
    }


def store_file(file_path: str, description: Optional[str] = None) -> Dict:
    """存储文件记忆"""
    file_type = get_file_type(file_path) or "document"
    
    # 复制文件
    media_path = copy_to_media(file_path, file_type)
    
    # 提取信息
    file_info = extract_file_info(file_path)
    
    # 存储记忆
    content = f"[文件] {description or Path(file_path).name}"
    success = store_memory(content, file_type, media_path, "document", 0.5)
    
    return {
        "path": media_path,
        "info": file_info,
        "success": success
    }


def list_media(media_type: Optional[str] = None) -> List[Dict]:
    """列出媒体文件"""
    results = []
    
    if not MEDIA_DIR.exists():
        return results
    
    type_dirs = [MEDIA_DIR / media_type] if media_type else MEDIA_DIR.iterdir()
    
    for type_dir in type_dirs:
        if type_dir.is_dir():
            for file_path in type_dir.rglob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    results.append({
                        "type": type_dir.name,
                        "name": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Memory Multimodal 0.2.0")
    parser.add_argument("command", choices=[
        "store-image", "store-audio", "store-file", "list"
    ])
    parser.add_argument("file", nargs="?", help="文件路径")
    parser.add_argument("--desc", "-d", help="描述")
    parser.add_argument("--type", "-t", help="媒体类型过滤")
    
    args = parser.parse_args()
    
    if args.command == "store-image":
        if not args.file:
            print("请提供图片路径")
            return
        result = store_image(args.file, args.desc)
        print(f"✅ 已存储: {result['path']}")
        print(f"   描述: {result['description'][:50]}...")
    
    elif args.command == "store-audio":
        if not args.file:
            print("请提供音频路径")
            return
        result = store_audio(args.file, args.desc)
        print(f"✅ 已存储: {result['path']}")
        if result['transcription']:
            print(f"   转录: {result['transcription'][:50]}...")
    
    elif args.command == "store-file":
        if not args.file:
            print("请提供文件路径")
            return
        result = store_file(args.file, args.desc)
        print(f"✅ 已存储: {result['path']}")
    
    elif args.command == "list":
        media_list = list_media(args.type)
        print(f"📂 媒体文件 ({len(media_list)} 个):")
        for m in media_list[:10]:
            print(f"   [{m['type']}] {m['name']} ({m['size']} bytes)")


if __name__ == "__main__":
    main()
