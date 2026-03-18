#!/usr/bin/env python3
"""
Memory Summary - 记忆摘要生成 v1.0

功能:
- 多粒度摘要 (short/medium/long)
- 批量生成记忆摘要
- 知识块摘要
- 会话摘要
- 自动缓存

Usage:
    python3 scripts/memory_summary.py generate --id MEM_ID --style short
    python3 scripts/memory_summary.py batch --all
    python3 scripts/memory_summary.py session --session-id "session_xxx"
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
SUMMARY_DIR = MEMORY_DIR / "summaries"
SUMMARY_CACHE = MEMORY_DIR / "summary_cache.json"

# Ollama 配置
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 摘要模板
SUMMARY_PROMPTS = {
    "short": "用一句话概括以下内容的要点（不超过50字）：\n\n{text}",
    "medium": "用一段话概括以下内容的要点（150字以内）：\n\n{text}",
    "long": "详细概括以下内容，包括主要观点和关键信息（300字以内）：\n\n{text}"
}


class MemorySummarizer:
    """记忆摘要生成器"""
    
    def __init__(self):
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        if SUMMARY_CACHE.exists():
            with open(SUMMARY_CACHE) as f:
                return json.load(f)
        return {"summaries": {}}
    
    def _save_cache(self):
        SUMMARY_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(SUMMARY_CACHE, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def _get_summary_from_ollama(self, text: str, style: str = "medium") -> Optional[str]:
        """从 Ollama 获取摘要"""
        if len(text) < 100:
            return text[:100]  # 太短不需要摘要
        
        prompt = SUMMARY_PROMPTS.get(style, SUMMARY_PROMPTS["medium"]).format(text=text[:1000])
        
        try:
            import requests
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": OLLAMA_LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=30
            )
            
            if response.ok:
                result = response.json()
                summary = result.get("response", "").strip()
                return summary[:500] if summary else None
        except Exception as e:
            print(f"⚠️ Ollama 生成失败: {e}")
        
        return None
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 3) -> str:
        """提取关键句子（规则方法）"""
        sentences = text.replace("\n", "。").split("。")
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if not sentences:
            return text[:100]
        
        # 简单评分：包含关键词 + 位置权重
        keywords = {"决定", "选择", "偏好", "重要", "关键", "核心", "主要"}
        
        scored = []
        for i, sent in enumerate(sentences):
            score = 0
            # 包含关键词加分
            for kw in keywords:
                if kw in sent:
                    score += 2
            
            # 靠前的句子加分
            if i < 3:
                score += 1
            
            scored.append((score, sent))
        
        scored.sort(reverse=True)
        top_sentences = [s for _, s in scored[:max_sentences]]
        
        return "。".join(top_sentences) + "。"
    
    def generate_summary(self, text: str, style: str = "medium", use_llm: bool = True) -> str:
        """生成摘要"""
        # 检查缓存
        cache_key = f"{hash(text)}_{style}"
        if cache_key in self.cache["summaries"]:
            return self.cache["summaries"][cache_key]
        
        summary = ""
        
        if use_llm:
            try:
                summary = self._get_summary_from_ollama(text, style)
            except:
                pass
        
        if not summary:
            # 回退到规则方法
            if style == "short":
                summary = self._extract_key_sentences(text, 1)[:50]
            elif style == "long":
                summary = self._extract_key_sentences(text, 5)[:300]
            else:
                summary = self._extract_key_sentences(text, 3)[:150]
        
        # 缓存
        self.cache["summaries"][cache_key] = summary
        self._save_cache()
        
        return summary
    
    def summarize_memory(self, memory_id: str, style: str = "medium") -> Optional[str]:
        """为单条记忆生成摘要"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            
            result = table.where(f"id = '{memory_id}'").to_list()
            if not result:
                return None
            
            mem = result[0]
            text = mem.get("text", "")
            
            summary = self.generate_summary(text, style)
            
            # 保存摘要到文件
            SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
            summary_file = SUMMARY_DIR / f"{memory_id}.json"
            
            with open(summary_file, 'w') as f:
                json.dump({
                    "memory_id": memory_id,
                    "style": style,
                    "summary": summary,
                    "original_length": len(text),
                    "summary_length": len(summary),
                    "generated_at": datetime.now().isoformat()
                }, f, indent=2)
            
            return summary
            
        except Exception as e:
            print(f"❌ 生成记忆摘要失败: {e}")
            return None
    
    def batch_summarize(self, limit: int = 10, style: str = "medium") -> Dict:
        """批量生成摘要"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            memories = []
            for i in range(min(limit, len(data.get("id", [])))):
                memories.append({
                    "id": data["id"][i],
                    "text": data["text"][i]
                })
            
            results = []
            for mem in memories:
                summary = self.summarize_memory(mem["id"], style)
                if summary:
                    results.append({
                        "memory_id": mem["id"],
                        "summary": summary,
                        "text_preview": mem["text"][:50]
                    })
            
            return {
                "total": len(memories),
                "generated": len(results),
                "results": results
            }
            
        except Exception as e:
            return {"error": str(e), "total": 0, "generated": 0}
    
    def get_summary(self, memory_id: str, style: str = "medium") -> Optional[str]:
        """获取已保存的摘要"""
        summary_file = SUMMARY_DIR / f"{memory_id}.json"
        if summary_file.exists():
            try:
                with open(summary_file) as f:
                    data = json.load(f)
                    if data.get("style") == style:
                        return data.get("summary")
            except:
                pass
        return None


def main():
    parser = argparse.ArgumentParser(description="Memory Summary v1.0")
    parser.add_argument("command", choices=["generate", "batch", "session", "list"])
    parser.add_argument("--id", "-i", help="记忆 ID")
    parser.add_argument("--style", "-s", choices=["short", "medium", "long"], default="medium")
    parser.add_argument("--limit", "-l", type=int, default=10, help="批量数量")
    parser.add_argument("--no-llm", action="store_true", help="不使用 LLM")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    summarizer = MemorySummarizer()
    
    if args.command == "generate":
        if not args.id:
            print("❌ 请提供 --id")
            return
        
        summary = summarizer.summarize_memory(args.id, args.style)
        
        if summary:
            if args.json:
                result = {
                    "memory_id": args.id,
                    "style": args.style,
                    "summary": summary
                }
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"📝 摘要 ({args.style}):")
                print(summary)
        else:
            print("❌ 生成失败")
    
    elif args.command == "batch":
        print(f"📦 批量生成摘要 (limit={args.limit}, style={args.style})")
        result = summarizer.batch_summarize(args.limit, args.style)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"   总数: {result['total']}")
            print(f"   生成: {result['generated']}")
            
            for r in result.get("results", [])[:5]:
                print(f"\n   {r['memory_id'][:8]}...")
                print(f"   {r['summary'][:60]}...")
    
    elif args.command == "session":
        # 摘要最近会话（基于记忆）
        print("📋 最近会话摘要")
        
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            # 取最近 5 条
            recent = []
            for i in range(min(5, len(data.get("id", [])))):
                recent.append({
                    "id": data["id"][i],
                    "text": data["text"][i],
                    "timestamp": data.get("timestamp", [""])[i]
                })
            
            for mem in recent:
                summary = summarizer.get_summary(mem["id"], "short")
                if not summary:
                    summary = summarizer.summarize_memory(mem["id"], "short")
                
                print(f"\n   {mem['timestamp'][:10]}")
                print(f"   {summary[:80]}...")
        
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    elif args.command == "list":
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
        summaries = list(SUMMARY_DIR.glob("*.json"))
        
        print(f"📚 已有摘要: {len(summaries)} 个")
        for s in summaries[:10]:
            try:
                with open(s) as f:
                    data = json.load(f)
                print(f"   {s.stem} ({data['style']}): {data['summary'][:40]}...")
            except:
                pass


if __name__ == "__main__":
    main()
