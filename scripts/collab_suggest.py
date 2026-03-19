#!/usr/bin/env python3
"""
Smart Collaboration Suggester - 智能协作建议系统 v1.0

功能:
- 分析对话内容，识别需要同步的信息
- 主动提示应该同步给哪个Agent
- 学习协作模式
- 自动生成同步建议

Usage:
    # 分析对话内容
    python3 scripts/collab_suggest.py analyze --text "刘总今天说要用飞书"
    
    # 查看建议
    python3 scripts/collab_suggest.py suggest --agent "main"
    
    # 学习模式
    python3 scripts/collab_suggest.py learn --pattern "刘总|偏好|设置" --target "all"
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import hashlib

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
SUGGEST_DIR = MEMORY_DIR / "suggest"
PATTERNS_FILE = SUGGEST_DIR / "patterns.json"
SUGGESTIONS_FILE = SUGGEST_DIR / "suggestions.jsonl"
LEARNED_FILE = SUGGEST_DIR / "learned.jsonl"


# 默认同步模式
DEFAULT_PATTERNS = [
    {
        "id": "user_preference",
        "keywords": ["偏好", "喜欢", "习惯", "prefer", "like"],
        "category": "preference",
        "target": "all",
        "priority": "high"
    },
    {
        "id": "user_info",
        "keywords": ["刘总", "老板", "用户", "user", "刘选权"],
        "category": "user",
        "target": "all",
        "priority": "high"
    },
    {
        "id": "task",
        "keywords": ["任务", "待办", "todo", "task", "需要"],
        "category": "task",
        "target": "all",
        "priority": "medium"
    },
    {
        "id": "project",
        "keywords": ["项目", "工程", "project", "repo"],
        "category": "project",
        "target": "all",
        "priority": "medium"
    },
    {
        "id": "decision",
        "keywords": ["决定", "确定", "选择", "decide", "confirm"],
        "category": "decision",
        "target": "all",
        "priority": "high"
    }
]


def ensure_dirs():
    """确保目录存在"""
    SUGGEST_DIR.mkdir(parents=True, exist_ok=True)
    
    if not PATTERNS_FILE.exists():
        with open(PATTERNS_FILE, 'w') as f:
            json.dump({"patterns": DEFAULT_PATTERNS}, f, ensure_ascii=False, indent=2)
    
    if not SUGGESTIONS_FILE.exists():
        SUGGESTIONS_FILE.touch()
    
    if not LEARNED_FILE.exists():
        LEARNED_FILE.touch()


def load_patterns() -> List[Dict]:
    """加载同步模式"""
    ensure_dirs()
    with open(PATTERNS_FILE) as f:
        data = json.load(f)
    return data.get("patterns", DEFAULT_PATTERNS)


def analyze_text(text: str, source_agent: str = "main") -> Dict:
    """分析文本，识别需要同步的内容"""
    ensure_dirs()
    patterns = load_patterns()
    
    suggestions = []
    matched_keywords = []
    
    for pattern in patterns:
        for keyword in pattern["keywords"]:
            if keyword.lower() in text.lower():
                matched_keywords.append(keyword)
                suggestions.append({
                    "pattern_id": pattern["id"],
                    "category": pattern["category"],
                    "target": pattern["target"],
                    "priority": pattern["priority"],
                    "matched_keyword": keyword,
                    "text_snippet": text[:100]
                })
                break  # 一个模式只匹配一次
    
    result = {
        "text": text[:200],
        "source_agent": source_agent,
        "timestamp": datetime.now().isoformat(),
        "matched_keywords": list(set(matched_keywords)),
        "suggestions": suggestions,
        "should_sync": len(suggestions) > 0
    }
    
    # 存储建议
    if suggestions:
        with open(SUGGESTIONS_FILE, 'a') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    return result


def get_suggestions(agent: str = None, limit: int = 10) -> List[Dict]:
    """获取同步建议"""
    ensure_dirs()
    
    suggestions = []
    with open(SUGGESTIONS_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if agent is None or entry["source_agent"] == agent:
                    suggestions.append(entry)
            except:
                continue
    
    suggestions.sort(key=lambda x: x["timestamp"], reverse=True)
    return suggestions[:limit]


def learn_pattern(pattern_id: str, keywords: List[str], category: str, target: str, priority: str = "medium") -> Dict:
    """学习新的同步模式"""
    ensure_dirs()
    
    patterns = load_patterns()
    
    # 检查是否已存在
    for p in patterns:
        if p["id"] == pattern_id:
            p["keywords"] = list(set(p["keywords"] + keywords))
            break
    else:
        patterns.append({
            "id": pattern_id,
            "keywords": keywords,
            "category": category,
            "target": target,
            "priority": priority
        })
    
    # 保存
    with open(PATTERNS_FILE, 'w') as f:
        json.dump({"patterns": patterns}, f, ensure_ascii=False, indent=2)
    
    # 记录学习日志
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "learn_pattern",
        "pattern_id": pattern_id,
        "keywords": keywords
    }
    with open(LEARNED_FILE, 'a') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    print(f"✅ 学习模式: [{pattern_id}] 关键词: {keywords}")
    return {"learned": True, "pattern_id": pattern_id}


def get_stats() -> Dict:
    """获取建议统计"""
    ensure_dirs()
    
    stats = {
        "total_suggestions": 0,
        "by_category": {},
        "by_priority": {"high": 0, "medium": 0, "low": 0},
        "patterns_count": len(load_patterns()),
        "learned_count": 0
    }
    
    with open(SUGGESTIONS_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                stats["total_suggestions"] += 1
                
                for s in entry.get("suggestions", []):
                    cat = s["category"]
                    stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
                    stats["by_priority"][s["priority"]] = stats["by_priority"].get(s["priority"], 0) + 1
            except:
                continue
    
    with open(LEARNED_FILE, 'r') as f:
        for line in f:
            try:
                json.loads(line.strip())
                stats["learned_count"] += 1
            except:
                continue
    
    return stats


def main():
    parser = argparse.ArgumentParser(description="Smart Collaboration Suggester v1.0")
    parser.add_argument("command", choices=["analyze", "suggest", "learn", "patterns", "stats"])
    parser.add_argument("--text", "-t", help="分析文本")
    parser.add_argument("--agent", "-a", help="来源Agent")
    parser.add_argument("--pattern-id", help="模式ID")
    parser.add_argument("--keywords", "-k", help="关键词(逗号分隔)")
    parser.add_argument("--category", "-c", default="other", help="类别")
    parser.add_argument("--target", help="目标Agent")
    parser.add_argument("--priority", "-p", default="medium", help="优先级")
    parser.add_argument("--limit", "-l", type=int, default=10, help="限制数量")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    agent = args.agent or "main"
    
    if args.command == "analyze":
        if not args.text:
            print("❌ 缺少参数: --text")
            return
        result = analyze_text(args.text, agent)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            if result["should_sync"]:
                print(f"💡 检测到 {len(result['suggestions'])} 条同步建议:")
                for s in result["suggestions"]:
                    print(f"   [{s['priority']}] {s['category']}: 匹配关键词 '{s['matched_keyword']}'")
                    print(f"      建议同步给: {s['target']}")
            else:
                print("ℹ️ 无需同步")
    
    elif args.command == "suggest":
        suggestions = get_suggestions(agent, args.limit)
        if args.json:
            print(json.dumps(suggestions, ensure_ascii=False, indent=2))
        else:
            print(f"💡 同步建议 (共 {len(suggestions)} 条)")
            for s in suggestions:
                print(f"  [{s['timestamp'][:16]}] {s['source_agent']}: {s['matched_keywords']}")
    
    elif args.command == "learn":
        if not all([args.pattern_id, args.keywords]):
            print("❌ 缺少参数: --pattern-id, --keywords")
            return
        keywords = [k.strip() for k in args.keywords.split(",")]
        result = learn_pattern(args.pattern_id, keywords, args.category, args.target or "all", args.priority)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "patterns":
        patterns = load_patterns()
        if args.json:
            print(json.dumps(patterns, ensure_ascii=False, indent=2))
        else:
            print(f"📋 同步模式 (共 {len(patterns)} 条)")
            for p in patterns:
                print(f"  [{p['id']}] {p['category']} → {p['target']}")
                print(f"      关键词: {p['keywords']}")
    
    elif args.command == "stats":
        stats = get_stats()
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("📊 建议统计")
            print(f"   总建议数: {stats['total_suggestions']}")
            print(f"   按类别: {stats['by_category']}")
            print(f"   按优先级: {stats['by_priority']}")
            print(f"   模式数: {stats['patterns_count']}")
            print(f"   学习记录: {stats['learned_count']}")


if __name__ == "__main__":
    main()
