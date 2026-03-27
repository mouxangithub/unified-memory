#!/usr/bin/env python3
"""
Memory Optimization - 记忆优化建议系统 v1.0

功能:
- 自动发现记忆问题
- 提供可操作的优化建议
- 生成优化报告

Usage:
    python3 scripts/memory_optimization.py analyze
    python3 scripts/memory_optimization.py suggest
    python3 scripts/memory_optimization.py report
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


class MemoryOptimizer:
    """记忆优化器"""
    
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
    
    def analyze_issues(self) -> Dict:
        """分析记忆问题"""
        result = {
            "total": len(self.memories),
            "issues": {
                "duplicates": [],
                "low_importance_unused": [],
                "stale": [],
                "missing_category": [],
                "too_short": [],
                "inconsistent_formatting": []
            },
            "stats": {}
        }
        
        # 1. 重复记忆
        text_count = Counter(m["text"] for m in self.memories)
        for text, count in text_count.items():
            if count > 1:
                matching = [m for m in self.memories if m["text"] == text]
                result["issues"]["duplicates"].append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "count": count,
                    "ids": [m["id"] for m in matching]
                })
        
        # 2. 低重要性且未使用的记忆
        access_counts = Counter(a.get("id") for a in self.access_log.get("accesses", []))
        for mem in self.memories:
            if mem["importance"] < 0.3 and mem["id"] not in access_counts:
                result["issues"]["low_importance_unused"].append({
                    "id": mem["id"],
                    "text": mem["text"][:100] + "...",
                    "importance": mem["importance"]
                })
        
        # 3. 过时记忆（超过6个月未更新）
        cutoff = datetime.now() - timedelta(days=180)
        for mem in self.memories:
            try:
                mem_time = datetime.fromisoformat(mem["timestamp"])
                if mem_time < cutoff:
                    result["issues"]["stale"].append({
                        "id": mem["id"],
                        "text": mem["text"][:100] + "...",
                        "age_days": (datetime.now() - mem_time).days,
                        "importance": mem["importance"]
                    })
            except:
                pass
        
        # 4. 缺失分类
        for mem in self.memories:
            if not mem["category"] or mem["category"] == "":
                result["issues"]["missing_category"].append({
                    "id": mem["id"],
                    "text": mem["text"][:100] + "..."
                })
        
        # 5. 过短记忆
        for mem in self.memories:
            if len(mem["text"]) < 10:
                result["issues"]["too_short"].append({
                    "id": mem["id"],
                    "text": mem["text"]
                })
        
        # 6. 统计信息
        categories = Counter(m["category"] for m in self.memories)
        result["stats"] = {
            "categories": dict(categories),
            "avg_importance": sum(m["importance"] for m in self.memories) / max(len(self.memories), 1),
            "total_accesses": len(self.access_log.get("accesses", [])),
            "unique_accessed": len(access_counts)
        }
        
        return result
    
    def generate_suggestions(self) -> List[Dict]:
        """生成优化建议"""
        issues = self.analyze_issues()["issues"]
        suggestions = []
        
        # 1. 重复记忆建议
        if issues["duplicates"]:
            suggestions.append({
                "priority": "high",
                "type": "deduplicate",
                "title": "合并重复记忆",
                "description": f"发现 {len(issues['duplicates'])} 组重复记忆",
                "action": "运行 'mem optimize dedup' 自动处理",
                "impact": f"可减少 {sum(d['count']-1 for d in issues['duplicates'])} 条记忆"
            })
        
        # 2. 低价值记忆清理
        if issues["low_importance_unused"]:
            suggestions.append({
                "priority": "medium",
                "type": "cleanup",
                "title": "清理低价值记忆",
                "description": f"有 {len(issues['low_importance_unused'])} 条低重要性且未使用的记忆",
                "action": "运行 'mem optimize cleanup' 审查后删除",
                "impact": "提高记忆检索质量"
            })
        
        # 3. 过时记忆归档
        if issues["stale"]:
            suggestions.append({
                "priority": "medium",
                "type": "archive",
                "title": "归档过时记忆",
                "description": f"有 {len(issues['stale'])} 条记忆超过6个月未更新",
                "action": "运行 'mem optimize archive' 移至归档",
                "impact": "减少活跃记忆负担"
            })
        
        # 4. 分类标准化
        if issues["missing_category"]:
            suggestions.append({
                "priority": "low",
                "type": "categorize",
                "title": "标记未分类记忆",
                "description": f"有 {len(issues['missing_category'])} 条记忆缺少分类",
                "action": "运行 'mem optimize tag' 添加适当分类",
                "impact": "改善记忆组织结构"
            })
        
        # 5. 记忆充实
        if issues["too_short"]:
            suggestions.append({
                "priority": "low",
                "type": "enrich",
                "title": "充实过短记忆",
                "description": f"有 {len(issues['too_short'])} 条记忆过短（<10字符）",
                "action": "考虑补充信息或删除无价值内容",
                "impact": "提高记忆信息密度"
            })
        
        return suggestions
    
    def get_optimization_report(self) -> Dict:
        """获取优化报告"""
        issues = self.analyze_issues()
        suggestions = self.generate_suggestions()
        
        # 计算健康分数
        total_issues = sum(len(v) for v in issues["issues"].values())
        max_possible_issues = len(self.memories) * 6  # 每条记忆最多6种问题
        health_score = max(0, 100 - int((total_issues / max(max_possible_issues, 1)) * 100))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_score": health_score,
            "total_memories": issues["total"],
            "issues_summary": {k: len(v) for k, v in issues["issues"].items()},
            "suggestions": suggestions,
            "stats": issues["stats"],
            "recommended_actions": [
                s["action"] for s in sorted(suggestions, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]])[:3]
            ]
        }
    
    def apply_optimization(self, action: str) -> Dict:
        """应用特定优化"""
        result = {
            "action": action,
            "success": False,
            "details": {},
            "message": ""
        }
        
        if action == "dedup":
            # 标记重复记忆（实际应用中可以删除或合并）
            duplicates = self.analyze_issues()["issues"]["duplicates"]
            result["details"]["duplicate_groups"] = len(duplicates)
            result["details"]["total_duplicates"] = sum(d["count"]-1 for d in duplicates)
            result["message"] = f"发现 {len(duplicates)} 组重复，建议人工审查后合并"
            result["success"] = True
            
        elif action == "cleanup":
            # 建议清理低价值记忆
            issues = self.analyze_issues()["issues"]["low_importance_unused"]
            result["details"]["candidates"] = len(issues)
            result["message"] = f"发现 {len(issues)} 条低价值记忆候选项，建议人工确认后删除"
            result["success"] = True
            
        elif action == "archive":
            # 建议归档过时记忆
            stale = self.analyze_issues()["issues"]["stale"]
            result["details"]["stale_count"] = len(stale)
            result["message"] = f"发现 {len(stale)} 条过时记忆，建议归档至冷存储"
            result["success"] = True
            
        elif action == "stats":
            # 显示统计信息
            stats = self.analyze_issues()["stats"]
            result["details"] = stats
            result["message"] = "统计信息已生成"
            result["success"] = True
            
        else:
            result["message"] = f"未知操作: {action}"
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Memory Optimization v1.0")
    parser.add_argument("command", choices=["analyze", "suggest", "report", "optimize"])
    parser.add_argument("--action", "-a", help="优化操作 (dedup, cleanup, archive, stats)")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    optimizer = MemoryOptimizer()
    
    if args.command == "analyze":
        result = optimizer.analyze_issues()
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"🔍 记忆问题分析")
            print(f"\n总记忆: {result['total']} 条")
            
            for issue_type, items in result["issues"].items():
                if items:
                    print(f"\n{issue_type}: {len(items)} 个")
                    for item in items[:3]:
                        if isinstance(item, dict):
                            print(f"   - {item.get('text', str(item))[:60]}...")
                        else:
                            print(f"   - {item}")
    
    elif args.command == "suggest":
        suggestions = optimizer.generate_suggestions()
        
        if args.json:
            print(json.dumps(suggestions, ensure_ascii=False, indent=2))
        else:
            print(f"💡 优化建议")
            if not suggestions:
                print("   暂无建议，记忆状态良好！")
                return
            
            for i, sug in enumerate(suggestions, 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[sug["priority"]]
                print(f"\n{i}. {priority_icon} {sug['title']}")
                print(f"   {sug['description']}")
                print(f"   行动: {sug['action']}")
                print(f"   影响: {sug['impact']}")
    
    elif args.command == "report":
        report = optimizer.get_optimization_report()
        
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"📊 记忆优化报告")
            print(f"\n健康分数: {report['health_score']}/100")
            print(f"总记忆: {report['total_memories']} 条")
            
            print(f"\n问题分布:")
            for issue_type, count in report["issues_summary"].items():
                if count > 0:
                    print(f"   {issue_type}: {count}")
            
            print(f"\n📋 建议行动:")
            for i, action in enumerate(report["recommended_actions"], 1):
                print(f"   {i}. {action}")
            
            if report["suggestions"]:
                print(f"\n详细建议:")
                for sug in report["suggestions"][:3]:
                    print(f"   [{sug['priority'].upper()}] {sug['title']}")
    
    elif args.command == "optimize":
        if not args.action:
            print("❌ 请提供 --action (dedup/cleanup/archive/stats)")
            return
        
        result = optimizer.apply_optimization(args.action)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result["success"]:
                print(f"✅ {result['message']}")
                if result["details"]:
                    print(f"   详情: {result['details']}")
            else:
                print(f"❌ {result['message']}")


if __name__ == "__main__":
    main()
