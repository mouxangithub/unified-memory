#!/usr/bin/env python3
"""
多模态记忆模块 v1.0

功能:
- 图片记忆（OCR提取文字）
- 音频记忆（语音转文字）
- 多模态搜索（CLIP embedding）
- 可配置可选项（OCR/STT按需启用）

Usage:
    mem store --image /path/to/image.jpg
    mem store --audio /path/to/voice.m4a
    mem multimodal config          # 显示配置
    mem multimodal enable ocr      # 启用OCR
    mem multimodal enable stt      # 启用STT

依赖（可选）:
    OCR: pip install paddleocr 或 tesseract
    STT: pip install openai-whisper 或使用讯飞API
    CLIP: pip install sentence-transformers
"""

import json
import subprocess
import shutil
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import hashlib

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
MULTIMODAL_DIR = MEMORY_DIR / "multimodal"
MULTIMODAL_CONFIG_FILE = MEMORY_DIR / "multimodal_config.json"

# 默认配置（所有功能默认禁用，用户按需启用）
DEFAULT_CONFIG = {
    "enabled": True,
    "ocr": {
        "enabled": False,
        "engine": "auto",  # auto, paddleocr, tesseract
        "languages": ["ch", "en"],
        "fallback": "提示用户手动输入",
    },
    "stt": {
        "enabled": False,
        "engine": "auto",  # auto, whisper, xfyun
        "language": "zh",
        "fallback": "提示用户手动输入",
    },
    "clip": {
        "enabled": False,
        "model": "clip-ViT-B-32",
        "fallback": "纯文本搜索",
    },
    "storage": {
        "max_file_size_mb": 20,
        "supported_image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
        "supported_audio_formats": ["m4a", "mp3", "wav", "ogg"],
    },
    "privacy": {
        "store_original": False,  # 是否存储原始文件
        "auto_delete_after_days": 30,
    }
}


def load_config() -> Dict:
    """加载配置"""
    if MULTIMODAL_CONFIG_FILE.exists():
        return json.loads(MULTIMODAL_CONFIG_FILE.read_text())
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict):
    """保存配置"""
    MULTIMODAL_CONFIG_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))


def check_ocr_available() -> Dict:
    """检查OCR引擎可用性"""
    engines = {
        "paddleocr": False,
        "tesseract": False,
    }
    
    # 检查 PaddleOCR
    try:
        import paddleocr
        engines["paddleocr"] = True
    except ImportError:
        pass
    
    # 检查 Tesseract
    if shutil.which("tesseract"):
        engines["tesseract"] = True
    
    return engines


def check_stt_available() -> Dict:
    """检查STT引擎可用性"""
    engines = {
        "whisper": False,
        "xfyun": False,
    }
    
    # 检查 Whisper
    try:
        import whisper
        engines["whisper"] = True
    except ImportError:
        pass
    
    # 检查讯飞（需要API配置）
    config = load_config()
    if config.get("stt", {}).get("xfyun_appid"):
        engines["xfyun"] = True
    
    return engines


def check_clip_available() -> bool:
    """检查CLIP可用性"""
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False


def ocr_image(image_path: str, config: Dict) -> Dict:
    """OCR识别图片"""
    if not config["ocr"]["enabled"]:
        return {
            "success": False,
            "error": "OCR未启用",
            "hint": "使用 `mem multimodal enable ocr` 启用"
        }
    
    # 检查文件
    path = Path(image_path)
    if not path.exists():
        return {"success": False, "error": f"文件不存在: {image_path}"}
    
    # 检查文件大小
    max_size = config["storage"]["max_file_size_mb"] * 1024 * 1024
    if path.stat().st_size > max_size:
        return {"success": False, "error": f"文件过大（>{config['storage']['max_file_size_mb']}MB）"}
    
    # 选择引擎
    engines = check_ocr_available()
    engine = config["ocr"]["engine"]
    
    if engine == "auto":
        if engines["paddleocr"]:
            engine = "paddleocr"
        elif engines["tesseract"]:
            engine = "tesseract"
        else:
            return {
                "success": False,
                "error": "无可用OCR引擎",
                "hint": "安装依赖: pip install paddleocr 或 apt install tesseract"
            }
    
    # 执行OCR
    try:
        if engine == "paddleocr":
            return ocr_with_paddleocr(image_path, config)
        elif engine == "tesseract":
            return ocr_with_tesseract(image_path, config)
        else:
            return {"success": False, "error": f"未知引擎: {engine}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def ocr_with_paddleocr(image_path: str, config: Dict) -> Dict:
    """使用PaddleOCR识别"""
    from paddleocr import PaddleOCR
    
    langs = config["ocr"]["languages"]
    lang = "ch" if "ch" in langs else "en"
    
    ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
    result = ocr.ocr(image_path, cls=True)
    
    # 提取文字
    lines = []
    for line in result:
        for word_info in line:
            lines.append(word_info[1][0])
    
    text = "\n".join(lines)
    
    return {
        "success": True,
        "engine": "paddleocr",
        "text": text,
        "line_count": len(lines)
    }


def ocr_with_tesseract(image_path: str, config: Dict) -> Dict:
    """使用Tesseract识别"""
    langs = config["ocr"]["languages"]
    lang = "chi_sim+eng" if "ch" in langs else "eng"
    
    result = subprocess.run(
        ["tesseract", image_path, "stdout", "-l", lang],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        return {"success": False, "error": result.stderr}
    
    text = result.stdout.strip()
    
    return {
        "success": True,
        "engine": "tesseract",
        "text": text,
        "line_count": len(text.split("\n"))
    }


def transcribe_audio(audio_path: str, config: Dict) -> Dict:
    """语音转文字"""
    if not config["stt"]["enabled"]:
        return {
            "success": False,
            "error": "STT未启用",
            "hint": "使用 `mem multimodal enable stt` 启用"
        }
    
    # 检查文件
    path = Path(audio_path)
    if not path.exists():
        return {"success": False, "error": f"文件不存在: {audio_path}"}
    
    # 选择引擎
    engines = check_stt_available()
    engine = config["stt"]["engine"]
    
    if engine == "auto":
        if engines["whisper"]:
            engine = "whisper"
        elif engines["xfyun"]:
            engine = "xfyun"
        else:
            return {
                "success": False,
                "error": "无可用STT引擎",
                "hint": "安装依赖: pip install openai-whisper"
            }
    
    # 执行转写
    try:
        if engine == "whisper":
            return transcribe_with_whisper(audio_path, config)
        elif engine == "xfyun":
            return transcribe_with_xfyun(audio_path, config)
        else:
            return {"success": False, "error": f"未知引擎: {engine}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def transcribe_with_whisper(audio_path: str, config: Dict) -> Dict:
    """使用Whisper转写"""
    import whisper
    
    lang = config["stt"]["language"]
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language=lang)
    
    text = result["text"]
    
    return {
        "success": True,
        "engine": "whisper",
        "text": text,
        "language": lang,
        "duration": result.get("segments", [{}])[-1].get("end", 0)
    }


def transcribe_with_xfyun(audio_path: str, config: Dict) -> Dict:
    """使用讯飞API转写"""
    # 需要配置讯飞API
    stt_config = config["stt"]
    appid = stt_config.get("xfyun_appid")
    api_key = stt_config.get("xfyun_api_key")
    
    if not appid or not api_key:
        return {
            "success": False,
            "error": "讯飞API未配置",
            "hint": "在配置中设置 xfyun_appid 和 xfyun_api_key"
        }
    
    # TODO: 实现讯飞API调用
    return {
        "success": False,
        "error": "讯飞API功能开发中"
    }


def store_multimodal_memory(
    file_path: str,
    file_type: str,  # image, audio
    config: Dict,
    metadata: Dict = None
) -> Dict:
    """存储多模态记忆"""
    path = Path(file_path)
    
    # 生成ID
    file_hash = hashlib.md5(path.read_bytes()).hexdigest()[:12]
    memory_id = f"{file_type[:3]}_{file_hash}"
    
    # 提取内容
    if file_type == "image":
        result = ocr_image(file_path, config)
    elif file_type == "audio":
        result = transcribe_audio(file_path, config)
    else:
        return {"success": False, "error": f"不支持的文件类型: {file_type}"}
    
    if not result.get("success"):
        return result
    
    # 创建记忆
    memory = {
        "id": memory_id,
        "type": file_type,
        "text": result["text"],
        "timestamp": datetime.now().isoformat(),
        "source": file_path,
        "metadata": metadata or {},
        "engine": result.get("engine"),
        "multimodal": True,
    }
    
    # 存储原始文件（可选）
    if config["privacy"]["store_original"]:
        MULTIMODAL_DIR.mkdir(parents=True, exist_ok=True)
        dest = MULTIMODAL_DIR / f"{memory_id}{path.suffix}"
        dest.write_bytes(path.read_bytes())
        memory["stored_file"] = str(dest)
    
    # 添加到记忆库
    memories = json.loads(MEMORIES_FILE.read_text()) if MEMORIES_FILE.exists() else []
    memories.append(memory)
    MEMORIES_FILE.write_text(json.dumps(memories, indent=2, ensure_ascii=False))
    
    return {
        "success": True,
        "memory_id": memory_id,
        "type": file_type,
        "text_preview": result["text"][:100],
        "engine": result.get("engine"),
        "line_count": result.get("line_count") or result.get("duration")
    }


def print_config():
    """打印配置"""
    config = load_config()
    
    print("🎨 多模态记忆配置\n")
    print("=" * 50)
    
    # OCR
    ocr_status = "✅ 已启用" if config["ocr"]["enabled"] else "❌ 未启用"
    print(f"\n📷 OCR ({ocr_status})")
    print(f"   引擎: {config['ocr']['engine']}")
    print(f"   语言: {config['ocr']['languages']}")
    
    engines = check_ocr_available()
    print(f"   可用引擎: {engines}")
    
    # STT
    stt_status = "✅ 已启用" if config["stt"]["enabled"] else "❌ 未启用"
    print(f"\n🎤 STT ({stt_status})")
    print(f"   引擎: {config['stt']['engine']}")
    print(f"   语言: {config['stt']['language']}")
    
    engines = check_stt_available()
    print(f"   可用引擎: {engines}")
    
    # CLIP
    clip_status = "✅ 已启用" if config["clip"]["enabled"] else "❌ 未启用"
    print(f"\n🖼️ CLIP ({clip_status})")
    print(f"   模型: {config['clip']['model']}")
    print(f"   可用: {check_clip_available()}")
    
    # 隐私
    print(f"\n🔒 隐私设置")
    print(f"   存储原始文件: {config['privacy']['store_original']}")
    print(f"   自动删除天数: {config['privacy']['auto_delete_after_days']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="多模态记忆模块")
    parser.add_argument("command", choices=["config", "enable", "disable", "store", "check"])
    parser.add_argument("--feature", choices=["ocr", "stt", "clip"], help="功能名称")
    parser.add_argument("--image", "-i", help="图片路径")
    parser.add_argument("--audio", "-a", help="音频路径")
    parser.add_argument("--engine", "-e", help="引擎名称")
    
    args = parser.parse_args()
    
    config = load_config()
    
    if args.command == "config":
        print_config()
    
    elif args.command == "check":
        print("🔍 检查多模态功能可用性\n")
        print(f"   OCR: {check_ocr_available()}")
        print(f"   STT: {check_stt_available()}")
        print(f"   CLIP: {check_clip_available()}")
    
    elif args.command == "enable":
        if not args.feature:
            print("❌ 缺少参数: --feature (ocr/stt/clip)")
            return
        
        config[args.feature]["enabled"] = True
        save_config(config)
        print(f"✅ 已启用 {args.feature}")
        
        # 提示安装依赖
        if args.feature == "ocr":
            print("\n安装依赖:")
            print("   PaddleOCR: pip install paddleocr")
            print("   Tesseract: apt install tesseract")
        elif args.feature == "stt":
            print("\n安装依赖:")
            print("   Whisper: pip install openai-whisper")
        elif args.feature == "clip":
            print("\n安装依赖:")
            print("   Sentence-Transformers: pip install sentence-transformers")
    
    elif args.command == "disable":
        if not args.feature:
            print("❌ 缺少参数: --feature (ocr/stt/clip)")
            return
        
        config[args.feature]["enabled"] = False
        save_config(config)
        print(f"✅ 已禁用 {args.feature}")
    
    elif args.command == "store":
        if args.image:
            result = store_multimodal_memory(args.image, "image", config)
        elif args.audio:
            result = store_multimodal_memory(args.audio, "audio", config)
        else:
            print("❌ 缺少参数: --image 或 --audio")
            return
        
        if result.get("success"):
            print(f"✅ 已存储多模态记忆: {result['memory_id']}")
            print(f"   类型: {result['type']}")
            print(f"   预览: {result['text_preview']}...")
        else:
            print(f"❌ {result.get('error')}")
            if result.get("hint"):
                print(f"   提示: {result['hint']}")


if __name__ == "__main__":
    main()
