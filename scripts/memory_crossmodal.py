#!/usr/bin/env python3
"""
跨模态深度集成 - Cross-Modal Deep Integration

核心概念：
- 图片 -> 自动描述 -> 存入记忆 -> 可召回
- 语音 -> 转文字 -> 存入记忆 -> 可召回
- 文件 -> 提取内容 -> 存入记忆 -> 可召回

深度集成不是简单存储，而是：
1. 理解内容
2. 生成描述
3. 建立关联
4. 支持召回
"""

import json
import base64
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
CROSSMODAL_DIR = MEMORY_DIR / "crossmodal"


class CrossModalEngine:
    """跨模态引擎"""
    
    def __init__(self):
        CROSSMODAL_DIR.mkdir(parents=True, exist_ok=True)
        self.index_file = CROSSMODAL_DIR / "index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {"items": []}
    
    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
    
    def _generate_id(self) -> str:
        import uuid
        return f"xmodal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    
    def process_image(self, image_path: str, context: str = "") -> Dict:
        """
        处理图片
        
        流程：
        1. 读取图片
        2. 生成描述（调用 LLM 或 OCR）
        3. 提取关键信息
        4. 存入索引
        """
        item_id = self._generate_id()
        
        # 存储路径
        dest_path = CROSSMODAL_DIR / f"{item_id}.jpg"
        
        # 复制文件
        try:
            import shutil
            shutil.copy(image_path, dest_path)
        except:
            pass
        
        # 生成描述（这里用简单的 OCR，实际应该用 LLM）
        description = self._describe_image(image_path)
        
        item = {
            "id": item_id,
            "type": "image",
            "source_path": str(image_path),
            "stored_path": str(dest_path),
            "description": description,
            "context": context,
            "extracted_entities": self._extract_entities(description),
            "created_at": datetime.now().isoformat()
        }
        
        self.index["items"].append(item)
        self._save_index()
        
        return item
    
    def _describe_image(self, image_path: str) -> str:
        """
        描述图片
        
        简化版：使用 OCR + 规则
        完整版：应该调用 LLM (如 GPT-4V)
        """
        # 尝试用 tesseract OCR
        try:
            result = subprocess.run(
                ["tesseract", image_path, "stdout", "-l", "chi_sim+eng"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                text = result.stdout.strip()
                if text:
                    return f"图片文字内容：{text[:500]}"
        except:
            pass
        
        return "图片（无法提取文字内容）"
    
    def process_audio(self, audio_path: str, context: str = "") -> Dict:
        """
        处理音频
        
        流程：
        1. 语音转文字 (STT)
        2. 提取关键信息
        3. 存入索引
        """
        item_id = self._generate_id()
        
        # 转写
        transcript = self._transcribe(audio_path)
        
        item = {
            "id": item_id,
            "type": "audio",
            "source_path": str(audio_path),
            "transcript": transcript,
            "context": context,
            "extracted_entities": self._extract_entities(transcript),
            "created_at": datetime.now().isoformat()
        }
        
        self.index["items"].append(item)
        self._save_index()
        
        return item
    
    def _transcribe(self, audio_path: str) -> str:
        """
        语音转文字
        
        简化版：使用 whisper 或百度 ASR
        完整版：应该调用专业 STT 服务
        """
        # 尝试用 whisper
        try:
            result = subprocess.run(
                ["whisper", "--model", "small", "--language", "Chinese", audio_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout.strip()[:2000]
        except:
            pass
        
        return "音频（无法转写）"
    
    def process_file(self, file_path: str, context: str = "") -> Dict:
        """
        处理文件
        
        支持：PDF, DOC, TXT 等
        """
        item_id = self._generate_id()
        ext = Path(file_path).suffix.lower()
        
        content = ""
        
        if ext == ".txt" or ext == ".md":
            with open(file_path, "r", errors="ignore") as f:
                content = f.read()[:5000]
        elif ext == ".pdf":
            content = self._extract_pdf(file_path)
        else:
            content = f"文件类型 {ext}（无法提取内容）"
        
        item = {
            "id": item_id,
            "type": "file",
            "file_type": ext,
            "source_path": str(file_path),
            "content_preview": content[:500],
            "context": context,
            "extracted_entities": self._extract_entities(content),
            "created_at": datetime.now().isoformat()
        }
        
        self.index["items"].append(item)
        self._save_index()
        
        return item
    
    def _extract_pdf(self, pdf_path: str) -> str:
        """提取 PDF 内容"""
        try:
            result = subprocess.run(
                ["pdftotext", pdf_path, "-"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()[:5000]
        except:
            pass
        return "PDF（无法提取内容）"
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        提取实体
        
        简化版：关键词匹配
        完整版：应该用 NER
        """
        import re
        
        entities = []
        
        # 人名（简单匹配）
        names = re.findall(r'[\u4e00-\u9fa5]{2,4}（[人者员]）', text)
        entities.extend(names)
        
        # 项目名（括号内）
        projects = re.findall(r'【([^】]+)】', text)
        entities.extend(projects)
        
        # 技术词
        tech_words = ["Python", "Java", "微服务", "API", "数据库", "架构"]
        for word in tech_words:
            if word in text:
                entities.append(word)
        
        return list(set(entities))[:10]
    
    def recall(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        召回相关内容
        
        支持跨模态搜索
        """
        results = []
        
        for item in self.index["items"]:
            # 计算相关度
            text = item.get("description", "") or item.get("transcript", "") or item.get("content_preview", "")
            
            # 简单匹配
            if query.lower() in text.lower():
                results.append({
                    "id": item["id"],
                    "type": item["type"],
                    "text": text[:200],
                    "entities": item.get("extracted_entities", []),
                    "created_at": item["created_at"],
                    "relevance": text.lower().count(query.lower()) / len(text)
                })
        
        # 按相关度排序
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:top_k]
    
    def get_recent(self, type_filter: str = None, limit: int = 10) -> List[Dict]:
        """获取最近的内容"""
        items = self.index["items"]
        
        if type_filter:
            items = [i for i in items if i["type"] == type_filter]
        
        # 按时间倒序
        items.sort(key=lambda x: x["created_at"], reverse=True)
        return items[:limit]
    
    def get_stats(self) -> Dict:
        """获取统计"""
        items = self.index["items"]
        
        by_type = {}
        for item in items:
            t = item["type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total": len(items),
            "by_type": by_type
        }


# 全局实例
_crossmodal = None

def get_crossmodal_engine() -> CrossModalEngine:
    global _crossmodal
    if _crossmodal is None:
        _crossmodal = CrossModalEngine()
    return _crossmodal


def process_and_recall(media_path: str, query: str = None) -> Dict:
    """
    处理媒体文件并召回
    
    自动判断类型，处理后建立索引
    """
    engine = get_crossmodal_engine()
    path = Path(media_path)
    ext = path.suffix.lower()
    
    # 处理
    if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        item = engine.process_image(str(path))
    elif ext in [".mp3", ".wav", ".m4a", ".ogg"]:
        item = engine.process_audio(str(path))
    elif ext in [".pdf", ".txt", ".md", ".doc"]:
        item = engine.process_file(str(path))
    else:
        return {"error": f"不支持的文件类型: {ext}"}
    
    # 召回
    results = []
    if query:
        results = engine.recall(query)
    
    return {
        "processed": item,
        "recall_results": results
    }


if __name__ == "__main__":
    print("=" * 60)
    print("跨模态深度集成测试")
    print("=" * 60)
    
    engine = get_crossmodal_engine()
    
    # 统计
    print(f"\n📊 跨模态统计:")
    stats = engine.get_stats()
    print(f"  total: {stats['total']}")
    print(f"  by_type: {stats['by_type']}")
    
    # 召回测试
    print(f"\n🔍 召回测试:")
    results = engine.recall("架构")
    print(f"  找到 {len(results)} 条相关内容")
    
    print("\n✅ 跨模态深度集成测试完成")
