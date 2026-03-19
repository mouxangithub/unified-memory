#!/usr/bin/env python3
"""
Conflict Resolver - 矛盾记忆自动解决器 v1.0

功能:
- 自动检测矛盾记忆
- 智能合并策略
- 提供解决建议
- 支持用户确认

解决策略:
- 高相似度 (>0.9): 自动合并
- 中等相似度 (0.7-0.9): 建议合并
- 低相似度 (<0.7): 标记矛盾
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

# 添加脚本目录
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from memory import MemorySystemV7
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
CONFLICT_DIR = MEMORY_DIR / "conflicts"

# 合并阈值
MERGE_AUTO_THRESHOLD = 0.9      # 自动合并
MERGE_SUGGEST_THRESHOLD = 0.7   # 建议合并
MERGE_CONFLICT_THRESHOLD = 0.5  # 标记矛盾

# 文件路径
CONFLICTS_FILE = CONFLICT_DIR / "detected_conflicts.json"
RESOLUTIONS_FILE = CONFLICT_DIR / "resolutions.json"

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 确保目录存在
CONFLICT_DIR.mkdir(parents=True, exist_ok=True)


class ConflictResolver:
    """矛盾记忆解决器"""
    
    def __init__(self):
        self.memory = MemorySystemV7() if HAS_MEMORY else None
        self.conflicts: List[Dict] = []
        self.resolutions: List[Dict] = []
        self._load()
    
    def _load(self):
        """加载状态"""
        try:
            if CONFLICTS_FILE.exists():
                self.conflicts = json.loads(CONFLICTS_FILE.read_text())
            if RESOLUTIONS_FILE.exists():
                self.resolutions = json.loads(RESOLUTIONS_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载冲突数据失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存状态"""
        try:
            CONFLICTS_FILE.write_text(json.dumps(self.conflicts, ensure_ascii=False, indent=2))
            RESOLUTIONS_FILE.write_text(json.dumps(self.resolutions, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存冲突数据失败: {e}", file=sys.stderr)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单版本）"""
        # 基于词汇重叠的简单相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def detect_conflicts(self, memories: List[Dict]) -> List[Dict]:
        """检测矛盾记忆"""
        conflicts = []
        
        # 按主题分组
        by_topic = defaultdict(list)
        for mem in memories:
            text = mem.get("text", "").lower()
            # 提取主题关键词
            keywords = [word for word in text.split() if len(word) > 2]
            for kw in keywords[:3]:
                by_topic[kw].append(mem)
        
        # 检测同一主题下的矛盾
        for topic, mems in by_topic.items():
            if len(mems) < 2:
                continue
            
            # 检测否定词
            positive = []
            negative = []
            
            for mem in mems:
                text = mem.get("text", "").lower()
                if any(neg in text for neg in ["不", "没", "无", "非", "不是", "没有", "不要"]):
                    negative.append(mem)
                else:
                    positive.append(mem)
            
            # 同时存在肯定和否定 → 矛盾
            if positive and negative:
                conflict = {
                    "topic": topic,
                    "positive": [{"id": m.get("id"), "text": m.get("text", "")} for m in positive],
                    "negative": [{"id": m.get("id"), "text": m.get("text", "")} for m in negative],
                    "detected_at": datetime.now().isoformat(),
                    "status": "pending"
                }
                conflicts.append(conflict)
        
        self.conflicts.extend(conflicts)
        self._save()
        
        return conflicts
    
    def generate_resolution(self, conflict: Dict) -> Dict:
        """生成解决方案"""
        positive = conflict.get("positive", [])
        negative = conflict.get("negative", [])
        
        if not positive or not negative:
            return {"error": "缺少正面或负面记忆"}
        
        # 计算相似度
        pos_text = " ".join([p["text"] for p in positive])
        neg_text = " ".join([n["text"] for n in negative])
        similarity = self.calculate_similarity(pos_text, neg_text)
        
        # 生成解决方案
        resolution = {
            "conflict_id": f"conflict_{datetime.now().timestamp()}",
            "similarity": similarity,
            "strategy": None,
            "suggestion": None,
            "auto_resolve": False,
            "created_at": datetime.now().isoformat()
        }
        
        if similarity >= MERGE_AUTO_THRESHOLD:
            # 高相似度：自动合并
            resolution["strategy"] = "auto_merge"
            resolution["suggestion"] = self._merge_texts(positive, negative)
            resolution["auto_resolve"] = True
            
        elif similarity >= MERGE_SUGGEST_THRESHOLD:
            # 中等相似度：建议合并
            resolution["strategy"] = "suggest_merge"
            resolution["suggestion"] = self._create_merge_suggestion(positive, negative)
            
        else:
            # 低相似度：标记矛盾
            resolution["strategy"] = "mark_conflict"
            resolution["suggestion"] = "这些记忆存在明显矛盾，需要用户明确选择保留哪个版本。"
        
        self.resolutions.append(resolution)
        self._save()
        
        return resolution
    
    def _merge_texts(self, positive: List[Dict], negative: List[Dict]) -> str:
        """合并文本"""
        # 简单合并策略：保留更完整的版本
        all_texts = [p["text"] for p in positive] + [n["text"] for n in negative]
        longest = max(all_texts, key=len)
        return longest
    
    def _create_merge_suggestion(self, positive: List[Dict], negative: List[Dict]) -> str:
        """创建合并建议"""
        pos_texts = [p["text"] for p in positive]
        neg_texts = [n["text"] for n in negative]
        
        suggestion = f"""检测到相似但矛盾的记忆：

正面记忆：
{chr(10).join(['- ' + t for t in pos_texts])}

负面记忆：
{chr(10).join(['- ' + t for t in neg_texts])}

建议：保留更具体或更近期的版本，或合并为一个综合陈述。"""
        
        return suggestion
    
    def apply_resolution(self, resolution_id: str, action: str = "accept") -> bool:
        """应用解决方案"""
        resolution = next((r for r in self.resolutions if r["conflict_id"] == resolution_id), None)
        
        if not resolution:
            print(f"❌ 未找到解决方案: {resolution_id}")
            return False
        
        if action == "accept":
            # 应用解决方案
            print(f"✅ 已应用解决方案: {resolution['strategy']}")
            resolution["status"] = "applied"
            resolution["applied_at"] = datetime.now().isoformat()
            self._save()
            return True
        
        elif action == "reject":
            # 拒绝解决方案
            print(f"❌ 已拒绝解决方案: {resolution['strategy']}")
            resolution["status"] = "rejected"
            resolution["rejected_at"] = datetime.now().isoformat()
            self._save()
            return True
        
        return False
    
    def auto_resolve_all(self) -> Dict:
        """自动解决所有可自动解决的矛盾"""
        results = {
            "total": len(self.conflicts),
            "auto_resolved": 0,
            "need_confirmation": 0,
            "conflicts": 0
        }
        
        for conflict in self.conflicts:
            if conflict.get("status") != "pending":
                continue
            
            resolution = self.generate_resolution(conflict)
            
            if resolution.get("auto_resolve"):
                # 自动应用
                self.apply_resolution(resolution["conflict_id"], "accept")
                results["auto_resolved"] += 1
            elif resolution.get("strategy") == "suggest_merge":
                results["need_confirmation"] += 1
            else:
                results["conflicts"] += 1
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_conflicts": len(self.conflicts),
            "total_resolutions": len(self.resolutions),
            "pending": len([c for c in self.conflicts if c.get("status") == "pending"]),
            "resolved": len([r for r in self.resolutions if r.get("status") == "applied"]),
            "by_strategy": {
                "auto_merge": len([r for r in self.resolutions if r.get("strategy") == "auto_merge"]),
                "suggest_merge": len([r for r in self.resolutions if r.get("strategy") == "suggest_merge"]),
                "mark_conflict": len([r for r in self.resolutions if r.get("strategy") == "mark_conflict"])
            }
        }


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="矛盾记忆解决器")
    parser.add_argument("command", choices=["detect", "resolve", "auto", "stats", "list"])
    parser.add_argument("--id", help="指定冲突ID")
    parser.add_argument("--action", choices=["accept", "reject"], help="操作")
    
    args = parser.parse_args()
    
    resolver = ConflictResolver()
    
    if args.command == "detect":
        # 检测矛盾
        if not HAS_MEMORY:
            print("❌ 记忆系统未加载")
            return
        
        memories = resolver.memory.memories if resolver.memory else []
        conflicts = resolver.detect_conflicts(memories)
        
        print(f"🔍 检测到 {len(conflicts)} 个矛盾")
        for i, c in enumerate(conflicts, 1):
            print(f"\n矛盾 #{i}:")
            print(f"  主题: {c['topic']}")
            print(f"  正面: {len(c['positive'])} 条")
            print(f"  负面: {len(c['negative'])} 条")
    
    elif args.command == "resolve":
        # 生成解决方案
        if not args.id:
            print("❌ 请指定 --id")
            return
        
        conflict = next((c for c in resolver.conflicts if c.get("topic") == args.id), None)
        if not conflict:
            print(f"❌ 未找到冲突: {args.id}")
            return
        
        resolution = resolver.generate_resolution(conflict)
        print(f"\n📋 解决方案:")
        print(f"  策略: {resolution['strategy']}")
        print(f"  相似度: {resolution['similarity']:.2f}")
        print(f"  建议:\n{resolution['suggestion']}")
    
    elif args.command == "auto":
        # 自动解决
        results = resolver.auto_resolve_all()
        print(f"\n🤖 自动解决结果:")
        print(f"  总计: {results['total']}")
        print(f"  自动解决: {results['auto_resolved']}")
        print(f"  需确认: {results['need_confirmation']}")
        print(f"  真正矛盾: {results['conflicts']}")
    
    elif args.command == "stats":
        # 统计
        stats = resolver.get_stats()
        print(f"\n📊 矛盾解决统计:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    elif args.command == "list":
        # 列出矛盾
        print(f"\n📋 矛盾列表:")
        for i, c in enumerate(resolver.conflicts, 1):
            print(f"\n#{i} {c['topic']}")
            print(f"  状态: {c.get('status', 'pending')}")
            print(f"  检测时间: {c['detected_at']}")


if __name__ == "__main__":
    main()
