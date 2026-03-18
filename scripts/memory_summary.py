#!/usr/bin/env python3
"""
Memory Summary - 记忆摘要生成 v0.1.3

功能:
- 自动生成记忆摘要
- 多粒度摘要（短/中/长）
- 基于 LLM 生成摘要
- 摘要历史记录

Usage:
    memory_summary.py generate --memory-id <id>
    memory_summary.py batch --count 10
    memory_summary.py history
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
SUMMARY_DIR = MEMORY_DIR / "summaries"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")


class MemorySummary:
    """记忆摘要生成"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.history_file = SUMMARY_DIR / "history.json"
        self.history = self._load_history()
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        memories = []
        
        if HAS_LANCEDB:
            try:
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                result = table.to_lance().to_table().to_pydict()
                
                if result:
                    count = len(result.get("id", []))
                    for i in range(count):
                        mem = {col: result[col][i] for col in result.keys() if len(result[col]) > i}
                        memories.append(mem)
            except:
                pass
        
        return memories
    
    def _load_history(self) -> Dict:
        """加载历史"""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())
            except:
                pass
        return {"summaries": []}
    
    def _save_history(self):
        """保存历史"""
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
        self.history_file.write_text(json.dumps(self.history, ensure_ascii=False, indent=2))
    
    def _generate_summary_llm(self, text: str, length: str = "medium") -> str:
        """使用 LLM 生成摘要"""
        if not HAS_REQUESTS:
            return self._generate_summary_rule(text, length)
        
        length_prompt = {
            "short": "一句话概括，不超过30字",
            "medium": "简要总结，50-80字",
            "long": "详细摘要，100-150字"
        }
        
        prompt = f"""请为以下记忆生成{length_prompt.get(length, 'medium')}：

记忆内容：
{text}

要求：
1. 保留关键信息
2. 使用用户可理解的语言
3. 如果是偏好类记忆，标注类型

摘要："""
        
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_LLM_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.5, "num_predict": 200}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get("response", "").strip()
                # 清理格式
                summary = summary.replace("摘要：", "").strip()
                return summary
        except Exception as e:
            print(f"⚠️ LLM 生成失败: {e}", file=sys.stderr)
        
        # 降级到规则提取
        return self._generate_summary_rule(text, length)
    
    def _generate_summary_rule(self, text: str, length: str = "medium") -> str:
        """基于规则生成摘要"""
        # 提取关键信息
        import re
        
        # 提取项目名
        project_match = re.search(r'(?:项目|Project)[：:]\s*([^\n,，]+)', text)
        project = project_match.group(1).strip() if project_match else ""
        
        # 提取决策
        decision_match = re.search(r'(决定|确认|选择|同意|批准)[：:]\s*([^\n。]+)', text)
        decision = decision_match.group(0).strip() if decision_match else ""
        
        # 提取偏好
        prefer_match = re.search(r'偏好|喜欢|想要|倾向', text)
        is_prefer = bool(prefer_match)
        
        # 组合摘要
        parts = []
        if project:
            parts.append(f"项目: {project}")
        if decision:
            parts.append(decision)
        if is_prefer:
            parts.append("偏好类记忆")
        
        if not parts:
            # 截取前N个字
            max_len = {"short": 30, "medium": 60, "long": 100}.get(length, 60)
            parts.append(text[:max_len] + "..." if len(text) > max_len else text)
        
        summary = " | ".join(parts)
        
        # 限制长度
        max_len = {"short": 30, "medium": 80, "long": 150}.get(length, 80)
        if len(summary) > max_len:
            summary = summary[:max_len] + "..."
        
        return summary
    
    def generate(self, memory_id: str, length: str = "medium") -> Dict:
        """生成单个记忆的摘要"""
        memory = None
        for mem in self.memories:
            if mem.get("id") == memory_id:
                memory = mem
                break
        
        if not memory:
            return {"error": "Memory not found"}
        
        text = memory.get("text", "")
        
        # 生成摘要
        if HAS_REQUESTS:
            summary = self._generate_summary_llm(text, length)
        else:
            summary = self._generate_summary_rule(text, length)
        
        # 保存
        summary_data = {
            "memory_id": memory_id,
            "summary": summary,
            "length": length,
            "created_at": datetime.now().isoformat(),
            "source_text": text[:100] + "..." if len(text) > 100 else text
        }
        
        self.history["summaries"].append(summary_data)
        self._save_history()
        
        # 保存单独文件
        summary_file = SUMMARY_DIR / f"{memory_id}.json"
        summary_file.write_text(json.dumps(summary_data, ensure_ascii=False, indent=2))
        
        return summary_data
    
    def batch_generate(self, count: int = 10, length: str = "medium") -> Dict:
        """批量生成摘要"""
        # 选择最近的记忆
        recent = sorted(
            self.memories,
            key=lambda x: x.get("created_at") or x.get("timestamp") or "",
            reverse=True
        )[:count]
        
        generated = []
        for mem in recent:
            memory_id = mem.get("id")
            if not memory_id:
                continue
            
            # 跳过已有摘要的
            summary_file = SUMMARY_DIR / f"{memory_id}.json"
            if summary_file.exists():
                continue
            
            result = self.generate(memory_id, length)
            if "summary" in result:
                generated.append(result)
        
        return {
            "total": len(self.memories),
            "requested": count,
            "generated": len(generated),
            "summaries": generated[:5]  # 返回前5个
        }
    
    def get_summary(self, memory_id: str) -> Optional[Dict]:
        """获取记忆摘要"""
        summary_file = SUMMARY_DIR / f"{memory_id}.json"
        if summary_file.exists():
            try:
                return json.loads(summary_file.read_text())
            except:
                pass
        return None
    
    def get_history(self) -> Dict:
        """获取历史"""
        return {
            "total": len(self.history.get("summaries", [])),
            "recent": self.history.get("summaries", [])[-10:]
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Summary 0.1.3")
    parser.add_argument("command", choices=["generate", "batch", "history", "get"])
    parser.add_argument("--memory-id", "-m", help="记忆 ID")
    parser.add_argument("--count", "-c", type=int, default=10, help="批量数量")
    parser.add_argument("--length", "-l", choices=["short", "medium", "long"], default="medium")
    
    args = parser.parse_args()
    
    summary = MemorySummary()
    
    if args.command == "generate":
        if not args.memory_id:
            print("❌ 请指定 --memory-id")
            sys.exit(1)
        
        result = summary.generate(args.memory_id, args.length)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            print(f"✅ 摘要生成成功:")
            print(f"  记忆: {result['memory_id'][:16]}...")
            print(f"  长度: {result['length']}")
            print(f"  摘要: {result['summary']}")
    
    elif args.command == "batch":
        print(f"🔄 批量生成摘要 (前 {args.count} 条)...")
        result = summary.batch_generate(args.count, args.length)
        
        print(f"\n✅ 完成:")
        print(f"  总记忆: {result['total']}")
        print(f"  请求数: {result['requested']}")
        print(f"  生成数: {result['generated']}")
        
        if result["summaries"]:
            print(f"\n示例:")
            for s in result["summaries"][:3]:
                print(f"  - {s['summary'][:50]}...")
    
    elif args.command == "history":
        history = summary.get_history()
        print(f"📜 摘要历史 ({history['total']} 条):")
        
        for h in history["recent"]:
            print(f"  {h['created_at'][:10]}: {h['summary'][:50]}...")
    
    elif args.command == "get":
        if not args.memory_id:
            print("❌ 请指定 --memory-id")
            sys.exit(1)
        
        result = summary.get_summary(args.memory_id)
        
        if result:
            print(f"📋 摘要:")
            print(f"  记忆: {result['memory_id'][:16]}...")
            print(f"  摘要: {result['summary']}")
            print(f"  时间: {result['created_at']}")
        else:
            print("❌ 未找到摘要")


if __name__ == "__main__":
    main()
