#!/usr/bin/env python3
"""
Memory Usage Analyzer - 记忆使用分析 v1.0

站在 AI Agent 用户角度，回答：
- 哪些记忆最有用？（访问频率）
- 哪些记忆浪费空间？（从未访问）
- 哪些记忆可能过时？（时效性）
- 记忆分布是否合理？（分类统计）

Usage:
    python3 scripts/memory_usage.py analyze
    python3 scripts/memory_usage.py cleanup-suggest
    python3 scripts/memory_usage.py usage-report
"""

import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
ACCESS_LOG = MEMORY_DIR / "access_history.json"
USAGE_REPORT = MEMORY_DIR / "usage_report.json"


class MemoryUsageAnalyzer:
    """记忆使用分析器"""
    
    def __init__(self):
        self.memories = self._load_memories()
        self.access_log = self._load_access_log()
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            data = table.to_lance().to_table().to_pydict()
            
            memories = []
            for i in range(len(data.get("id", []))):
                memories.append({
                    "id": data["id"][i],
                    "text": data["text"][i],
                    "category": data.get("category", [""])[i] if i < len(data.get("category", [])) else "",
                    "importance": data.get("importance", [0.5])[i] if i < len(data.get("importance", [])) else 0.5,
                    "tags": data.get("tags", [[]])[i] if i < len(data.get("tags", [])) else [],
                    "timestamp": data.get("timestamp", [""])[i] if i < len(data.get("timestamp", [])) else ""
                })
            return memories
        except Exception as e:
            print(f"⚠️ 加载记忆失败: {e}")
            return []
    
    def _load_access_log(self) -> Dict:
        """加载访问日志"""
        if ACCESS_LOG.exists():
            with open(ACCESS_LOG) as f:
                return json.load(f)
        return {"accesses": [], "co_occurrences": {}}
    
    def analyze(self) -> Dict:
        """全面分析"""
        result = {
            "total": len(self.memories),
            "categories": {},
            "access_stats": {},
            "stale_memories": [],
            "unused_memories": [],
            "top_memories": [],
            "recommendations": []
        }
        
        # 1. 分类统计
        categories = Counter(m["category"] for m in self.memories)
        result["categories"] = dict(categories)
        
        # 2. 访问统计
        access_counts = Counter(a.get("id") for a in self.access_log.get("accesses", []))
        
        # 3. 找出最常访问的记忆
        sorted_by_access = sorted(access_counts.items(), key=lambda x: x[1], reverse=True)
        for mem_id, count in sorted_by_access[:5]:
            mem = next((m for m in self.memories if m["id"] == mem_id), None)
            if mem:
                result["top_memories"].append({
                    "id": mem_id,
                    "text": mem["text"][:50] + "...",
                    "access_count": count,
                    "category": mem["category"]
                })
        
        # 4. 找出从未访问的记忆
        for mem in self.memories:
            if mem["id"] not in access_counts:
                result["unused_memories"].append({
                    "id": mem["id"],
                    "text": mem["text"][:50] + "...",
                    "category": mem["category"],
                    "importance": mem["importance"]
                })
        
        # 5. 找出可能过时的记忆（超过30天未访问且重要性<0.5）
        cutoff = datetime.now() - timedelta(days=30)
        for mem in self.memories:
            try:
                mem_time = datetime.fromisoformat(mem["timestamp"])
                if mem_time < cutoff and mem["importance"] < 0.5:
                    result["stale_memories"].append({
                        "id": mem["id"],
                        "text": mem["text"][:50] + "...",
                        "age_days": (datetime.now() - mem_time).days,
                        "importance": mem["importance"]
                    })
            except:
                pass
        
        # 6. 生成建议
        if len(result["unused_memories"]) > len(self.memories) * 0.3:
            result["recommendations"].append({
                "type": "cleanup",
                "message": f"有 {len(result['unused_memories'])} 条记忆从未被访问，建议清理或降低重要性"
            })
        
        if len(result["stale_memories"]) > 5:
            result["recommendations"].append({
                "type": "archive",
                "message": f"有 {len(result['stale_memories'])} 条记忆可能已过时，建议归档"
            })
        
        if not result["top_memories"]:
            result["recommendations"].append({
                "type": "usage",
                "message": "没有访问记录，建议开始使用记忆系统"
            })
        
        # 7. 访问统计摘要
        result["access_stats"] = {
            "total_accesses": len(self.access_log.get("accesses", [])),
            "unique_accessed": len(access_counts),
            "never_accessed": len(self.memories) - len(access_counts),
            "avg_access_per_memory": round(len(self.access_log.get("accesses", [])) / max(len(access_counts), 1), 2)
        }
        
        return result
    
    def cleanup_suggest(self) -> Dict:
        """清理建议"""
        analysis = self.analyze()
        
        suggestions = {
            "can_delete": [],
            "can_archive": [],
            "can_merge": [],
            "can_boost": []
        }
        
        # 1. 可删除：重要性低 + 从未访问 + 超过30天
        for mem in analysis["unused_memories"]:
            if mem["importance"] < 0.3:
                suggestions["can_delete"].append(mem)
        
        # 2. 可归档：可能过时
        suggestions["can_archive"] = analysis["stale_memories"]
        
        # 3. 可合并：相似内容的记忆（简单规则检测）
        texts = [(m["id"], m["text"]) for m in self.memories]
        for i, (id1, text1) in enumerate(texts):
            for id2, text2 in texts[i+1:]:
                # 简单相似度：共享关键词
                words1 = set(text1.split())
                words2 = set(text2.split())
                overlap = len(words1 & words2) / max(len(words1 | words2), 1)
                if overlap > 0.6:
                    suggestions["can_merge"].append({
                        "id1": id1,
                        "id2": id2,
                        "similarity": round(overlap, 2),
                        "text1": text1[:30] + "...",
                        "text2": text2[:30] + "..."
                    })
        
        # 4. 可提升：高访问但重要性低
        access_counts = Counter(a.get("id") for a in self.access_log.get("accesses", []))
        for mem_id, count in access_counts.items():
            if count > 3:  # 访问超过3次
                mem = next((m for m in self.memories if m["id"] == mem_id), None)
                if mem and mem["importance"] < 0.7:
                    suggestions["can_boost"].append({
                        "id": mem_id,
                        "text": mem["text"][:50] + "...",
                        "current_importance": mem["importance"],
                        "suggested_importance": min(0.9, mem["importance"] + 0.2),
                        "access_count": count
                    })
        
        return suggestions
    
    def usage_report(self, days: int = 7) -> Dict:
        """使用报告"""
        cutoff = datetime.now() - timedelta(days=days)
        
        # 筛选时间范围内的访问
        recent_accesses = []
        for acc in self.access_log.get("accesses", []):
            try:
                acc_time = datetime.fromisoformat(acc.get("timestamp", ""))
                if acc_time > cutoff:
                    recent_accesses.append(acc)
            except:
                pass
        
        # 按日期统计
        daily_access = Counter()
        for acc in recent_accesses:
            try:
                date_str = datetime.fromisoformat(acc["timestamp"]).strftime("%Y-%m-%d")
                daily_access[date_str] += 1
            except:
                pass
        
        # 按类别统计
        category_access = Counter()
        for acc in recent_accesses:
            mem_id = acc.get("id")
            mem = next((m for m in self.memories if m["id"] == mem_id), None)
            if mem:
                category_access[mem["category"]] += 1
        
        return {
            "period_days": days,
            "total_accesses": len(recent_accesses),
            "daily_access": dict(sorted(daily_access.items())),
            "category_access": dict(category_access),
            "avg_daily": round(len(recent_accesses) / days, 1),
            "most_active_day": max(daily_access.items(), key=lambda x: x[1])[0] if daily_access else None
        }
    
    def get_memory_score(self, mem_id: str) -> Dict:
        """获取单条记忆的评分"""
        mem = next((m for m in self.memories if m["id"] == mem_id), None)
        if not mem:
            return {"error": "Memory not found"}
        
        # 访问次数
        access_count = sum(1 for a in self.access_log.get("accesses", []) if a.get("id") == mem_id)
        
        # 最近访问
        recent_access = None
        for acc in reversed(self.access_log.get("accesses", [])):
            if acc.get("id") == mem_id:
                recent_access = acc.get("timestamp")
                break
        
        # 记忆年龄
        try:
            age_days = (datetime.now() - datetime.fromisoformat(mem["timestamp"])).days
        except:
            age_days = 0
        
        # 综合评分
        score = (
            mem["importance"] * 0.4 +  # 重要性 40%
            min(access_count / 10, 1) * 0.3 +  # 访问频率 30%
            (1 - min(age_days / 365, 1)) * 0.3  # 新鲜度 30%
        )
        
        return {
            "id": mem_id,
            "text": mem["text"][:50] + "...",
            "importance": mem["importance"],
            "access_count": access_count,
            "age_days": age_days,
            "recent_access": recent_access,
            "score": round(score, 3),
            "grade": "A" if score > 0.7 else "B" if score > 0.5 else "C" if score > 0.3 else "D"
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Usage Analyzer v1.0")
    parser.add_argument("command", choices=["analyze", "cleanup-suggest", "usage-report", "score"])
    parser.add_argument("--id", "-i", help="记忆 ID")
    parser.add_argument("--days", "-d", type=int, default=7, help="统计天数")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    analyzer = MemoryUsageAnalyzer()
    
    if args.command == "analyze":
        result = analyzer.analyze()
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📊 记忆使用分析")
            print(f"\n总记忆: {result['total']} 条")
            print(f"\n分类分布:")
            for cat, count in result["categories"].items():
                print(f"   {cat or '未分类'}: {count} 条")
            
            print(f"\n访问统计:")
            stats = result["access_stats"]
            print(f"   总访问: {stats['total_accesses']} 次")
            print(f"   已访问: {stats['unique_accessed']} 条")
            print(f"   从未访问: {stats['never_accessed']} 条")
            
            if result["top_memories"]:
                print(f"\n🔥 最常访问:")
                for i, mem in enumerate(result["top_memories"], 1):
                    print(f"   {i}. [{mem['access_count']}次] {mem['text']}")
            
            if result["recommendations"]:
                print(f"\n💡 建议:")
                for rec in result["recommendations"]:
                    print(f"   [{rec['type']}] {rec['message']}")
    
    elif args.command == "cleanup-suggest":
        result = analyzer.cleanup_suggest()
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("🧹 清理建议")
            print(f"\n可删除: {len(result['can_delete'])} 条")
            for mem in result["can_delete"][:3]:
                print(f"   - {mem['text']}")
            
            print(f"\n可归档: {len(result['can_archive'])} 条")
            for mem in result["can_archive"][:3]:
                print(f"   - {mem['text']}")
            
            print(f"\n可合并: {len(result['can_merge'])} 对")
            for pair in result["can_merge"][:3]:
                print(f"   - {pair['text1']} ↔ {pair['text2']}")
            
            print(f"\n可提升重要性: {len(result['can_boost'])} 条")
            for mem in result["can_boost"][:3]:
                print(f"   - {mem['text']} ({mem['current_importance']} → {mem['suggested_importance']})")
    
    elif args.command == "usage-report":
        result = analyzer.usage_report(args.days)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📈 使用报告 (最近 {args.days} 天)")
            print(f"\n总访问: {result['total_accesses']} 次")
            print(f"日均: {result['avg_daily']} 次")
            print(f"最活跃: {result['most_active_day']}")
            
            print(f"\n每日访问:")
            for date, count in result["daily_access"].items():
                bar = "█" * min(count, 20)
                print(f"   {date}: {bar} {count}")
            
            print(f"\n分类访问:")
            for cat, count in result["category_access"].items():
                print(f"   {cat or '未分类'}: {count} 次")
    
    elif args.command == "score":
        if not args.id:
            print("❌ 请提供 --id")
            return
        
        result = analyzer.get_memory_score(args.id)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📊 记忆评分")
            print(f"\n内容: {result.get('text', '')}")
            print(f"评分: {result.get('score', 0)} ({result.get('grade', 'N/A')})")
            print(f"\n重要性: {result.get('importance', 0)}")
            print(f"访问次数: {result.get('access_count', 0)}")
            print(f"记忆年龄: {result.get('age_days', 0)} 天")


if __name__ == "__main__":
    main()
