#!/usr/bin/env python3
"""
Memory Insights - 智能洞察 v0.2.1

功能:
- 用户偏好分析
- 记忆热点统计
- 个性化建议
- 行为趋势

Usage:
    python3 scripts/memory_insights.py analyze
    python3 scripts/memory_insights.py trends
    python3 scripts/memory_insights.py suggestions
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from collections import Counter

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
INSIGHTS_FILE = MEMORY_DIR / "insights.json"


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        data = table.to_lance().to_table().to_pydict()
        
        memories = []
        count = len(data.get("id", []))
        for i in range(count):
            memories.append({
                "id": data["id"][i] if i < len(data.get("id", [])) else "",
                "text": data["text"][i] if i < len(data.get("text", [])) else "",
                "category": data["category"][i] if i < len(data.get("category", [])) else "",
                "importance": float(data["importance"][i]) if i < len(data.get("importance", [])) else 0.5,
                "timestamp": data["timestamp"][i] if i < len(data.get("timestamp", [])) else ""
            })
        return memories
    except:
        return []


def analyze_preferences(memories: List[Dict]) -> Dict:
    """分析用户偏好"""
    preferences = {
        "tools": Counter(),
        "projects": Counter(),
        "categories": Counter(),
        "keywords": Counter()
    }
    
    # 工具关键词
    tools = ["飞书", "微信", "QQ", "钉钉", "Slack", "Notion", "Obsidian"]
    # 项目关键词
    project_patterns = ["项目", "龙宫", "官网", "重构", "电商"]
    
    for m in memories:
        text = m.get("text", "")
        category = m.get("category", "")
        
        # 统计类别
        preferences["categories"][category] += 1
        
        # 统计工具
        for tool in tools:
            if tool in text:
                preferences["tools"][tool] += 1
        
        # 统计项目
        for pattern in project_patterns:
            if pattern in text:
                preferences["projects"][pattern] += 1
        
        # 关键词
        keywords = ["喜欢", "偏好", "决定", "选择", "使用"]
        for kw in keywords:
            if kw in text:
                preferences["keywords"][kw] += 1
    
    return {
        "tools": dict(preferences["tools"].most_common(5)),
        "projects": dict(preferences["projects"].most_common(5)),
        "categories": dict(preferences["categories"].most_common(5)),
        "keywords": dict(preferences["keywords"].most_common(5))
    }


def analyze_hotspots(memories: List[Dict]) -> Dict:
    """分析记忆热点"""
    hotspots = {
        "by_importance": [],
        "by_category": {},
        "by_recency": []
    }
    
    # 按重要性排序
    sorted_by_importance = sorted(memories, key=lambda x: x.get("importance", 0), reverse=True)
    hotspots["by_importance"] = [
        {"text": m["text"][:50], "importance": m["importance"]}
        for m in sorted_by_importance[:5]
    ]
    
    # 按类别统计
    for m in memories:
        cat = m.get("category", "unknown")
        hotspots["by_category"][cat] = hotspots["by_category"].get(cat, 0) + 1
    
    # 按时间排序
    sorted_by_time = sorted(
        [m for m in memories if m.get("timestamp")],
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )
    hotspots["by_recency"] = [
        {"text": m["text"][:50], "date": m["timestamp"][:10]}
        for m in sorted_by_time[:5]
    ]
    
    return hotspots


def analyze_trends(memories: List[Dict]) -> Dict:
    """分析行为趋势"""
    now = datetime.now()
    
    trends = {
        "daily": {"total": 0, "by_category": {}},
        "weekly": {"total": 0, "by_category": {}},
        "monthly": {"total": 0, "by_category": {}}
    }
    
    for m in memories:
        try:
            ts = m.get("timestamp", "")
            if not ts:
                continue
            
            dt = datetime.fromisoformat(ts)
            category = m.get("category", "unknown")
            
            # 今天
            if dt.date() == now.date():
                trends["daily"]["total"] += 1
                trends["daily"]["by_category"][category] = trends["daily"]["by_category"].get(category, 0) + 1
            
            # 本周
            if dt > now - timedelta(days=7):
                trends["weekly"]["total"] += 1
                trends["weekly"]["by_category"][category] = trends["weekly"]["by_category"].get(category, 0) + 1
            
            # 本月
            if dt > now - timedelta(days=30):
                trends["monthly"]["total"] += 1
                trends["monthly"]["by_category"][category] = trends["monthly"]["by_category"].get(category, 0) + 1
            
        except:
            pass
    
    return trends


def generate_suggestions(memories: List[Dict], preferences: Dict) -> List[str]:
    """生成个性化建议"""
    suggestions = []
    
    # 基于工具偏好
    tools = preferences.get("tools", {})
    if tools:
        top_tool = list(tools.keys())[0]
        suggestions.append(f"您偏好使用 {top_tool}，建议继续深入了解其高级功能")
    
    # 基于项目
    projects = preferences.get("projects", {})
    if projects:
        suggestions.append("您有多个项目相关记忆，建议定期回顾项目进度")
    
    # 基于类别分布
    categories = preferences.get("categories", {})
    if categories:
        if categories.get("decision", 0) > 3:
            suggestions.append("您做了多个决策，建议记录决策理由以便回顾")
        if categories.get("learning", 0) > 3:
            suggestions.append("您在学习新知识，建议定期复习强化记忆")
    
    # 基于记忆数量
    if len(memories) > 50:
        suggestions.append("记忆数量较多，建议进行一次整理或归档")
    
    return suggestions


def generate_insights() -> Dict:
    """生成完整洞察报告"""
    memories = load_memories()
    
    insights = {
        "total_memories": len(memories),
        "generated_at": datetime.now().isoformat(),
        "preferences": analyze_preferences(memories),
        "hotspots": analyze_hotspots(memories),
        "trends": analyze_trends(memories),
        "suggestions": []
    }
    
    insights["suggestions"] = generate_suggestions(memories, insights["preferences"])
    
    # 保存
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with open(INSIGHTS_FILE, 'w') as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    
    return insights


def main():
    parser = argparse.ArgumentParser(description="Memory Insights 0.2.1")
    parser.add_argument("command", choices=["analyze", "trends", "suggestions"])
    
    args = parser.parse_args()
    
    # 加载或生成洞察
    if INSIGHTS_FILE.exists():
        with open(INSIGHTS_FILE) as f:
            insights = json.load(f)
    else:
        insights = generate_insights()
    
    if args.command == "analyze":
        print("📊 用户洞察分析")
        print(f"\n总记忆: {insights['total_memories']}")
        
        print("\n🔧 工具偏好:")
        for tool, count in insights["preferences"]["tools"].items():
            print(f"   {tool}: {count} 次")
        
        print("\n📁 类别分布:")
        for cat, count in insights["preferences"]["categories"].items():
            print(f"   {cat}: {count} 条")
        
        print("\n🔥 热点记忆:")
        for i, m in enumerate(insights["hotspots"]["by_importance"][:3], 1):
            print(f"   {i}. [{m['importance']:.1f}] {m['text']}...")
    
    elif args.command == "trends":
        print("📈 行为趋势")
        print(f"\n今日: {insights['trends']['daily']['total']} 条")
        print(f"本周: {insights['trends']['weekly']['total']} 条")
        print(f"本月: {insights['trends']['monthly']['total']} 条")
        
        print("\n本周类别分布:")
        for cat, count in insights["trends"]["weekly"]["by_category"].items():
            print(f"   {cat}: {count}")
    
    elif args.command == "suggestions":
        print("💡 个性化建议")
        for i, s in enumerate(insights["suggestions"], 1):
            print(f"   {i}. {s}")


if __name__ == "__main__":
    main()
