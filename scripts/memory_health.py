#!/usr/bin/env python3
"""
Memory Health - 记忆健康度检测 v0.1.6

功能:
- 自动验证记忆
- 矛盾检测
- 过时检测
- 质量评分

Usage:
    python3 scripts/memory_health.py report   # 健康报告
    python3 scripts/memory_health.py validate # 验证记忆
    python3 scripts/memory_health.py conflicts # 矛盾检测
    python3 scripts/memory_health.py fix     # 修复问题
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# 矛盾词对
CONFLICT_PAIRS = [
    ("喜欢", "讨厌"),
    ("爱", "恨"),
    ("是", "不是"),
    ("可以", "不可以"),
    ("会", "不会"),
    ("有", "没有"),
    ("使用", "不使用"),
    ("采用", "不采用"),
]

# 过时时间（天）
OUTDATED_DAYS = 90


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    memories = []
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        result = table.to_lance().to_table().to_pydict()
        
        count = len(result.get("id", []))
        for i in range(count):
            memories.append({
                "id": result["id"][i] if i < len(result.get("id", [])) else "",
                "text": result["text"][i] if i < len(result.get("text", [])) else "",
                "category": result["category"][i] if i < len(result.get("category", [])) else "",
                "importance": float(result["importance"][i]) if i < len(result.get("importance", [])) else 0.5,
                "timestamp": result["timestamp"][i] if i < len(result.get("timestamp", [])) else ""
            })
    except Exception as e:
        print(f"加载失败: {e}")
    
    return memories


def detect_conflicts(memories: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """检测矛盾记忆"""
    conflicts = []
    
    for i, m1 in enumerate(memories):
        for m2 in memories[i+1:]:
            # 跳过不同类别
            if m1.get("category") != m2.get("category"):
                continue
            
            text1 = m1.get("text", "")
            text2 = m2.get("text", "")
            
            # 检查是否相似但矛盾
            for word1, word2 in CONFLICT_PAIRS:
                if word1 in text1 and word2 in text2:
                    conflicts.append((m1, m2))
                    break
    
    return conflicts


def detect_outdated(memories: List[Dict]) -> List[Dict]:
    """检测过时记忆"""
    outdated = []
    now = datetime.now()
    threshold = now - timedelta(days=OUTDATED_DAYS)
    
    for m in memories:
        try:
            ts = m.get("timestamp", "")
            if ts:
                dt = datetime.fromisoformat(ts)
                if dt < threshold:
                    outdated.append(m)
        except:
            pass
    
    return outdated


def detect_duplicates(memories: List[Dict]) -> List[Tuple[Dict, Dict]]:
    """检测重复记忆"""
    duplicates = []
    
    for i, m1 in enumerate(memories):
        for m2 in memories[i+1:]:
            text1 = m1.get("text", "").lower().strip()
            text2 = m2.get("text", "").lower().strip()
            
            # 简单相似度检查
            if text1 and text2:
                longer = max(len(text1), len(text2))
                shorter = min(len(text1), len(text2))
                
                # 只检查高度相似的记忆
                # 1. 完全相同
                if text1 == text2:
                    duplicates.append((m1, m2))
                    continue
                
                # 2. 一个是另一个的子串，且长度差异小
                if shorter > 20:  # 只检查较长文本
                    if text1 in text2 and (longer - shorter) < longer * 0.3:
                        duplicates.append((m1, m2))
                    elif text2 in text1 and (longer - shorter) < longer * 0.3:
                        duplicates.append((m1, m2))
    
    return duplicates


def calculate_health_score(memories: List[Dict]) -> Dict:
    """计算健康度分数"""
    total = len(memories)
    if total == 0:
        return {"score": 100, "issues": 0, "details": {}}
    
    conflicts = detect_conflicts(memories)
    outdated = detect_outdated(memories)
    duplicates = detect_duplicates(memories)
    
    # 分数计算
    issues = len(conflicts) * 10 + len(outdated) * 3 + len(duplicates) * 2
    score = max(0, 100 - issues)
    
    return {
        "score": score,
        "total": total,
        "conflicts": len(conflicts),
        "outdated": len(outdated),
        "duplicates": len(duplicates),
        "details": {
            "conflicts": [{"text1": c[0]["text"][:30], "text2": c[1]["text"][:30]} for c in conflicts[:5]],
            "outdated": [o["text"][:30] for o in outdated[:5]],
            "duplicates": [{"text1": d[0]["text"][:30], "text2": d[1]["text"][:30]} for d in duplicates[:5]]
        }
    }


def validate_memories(memories: List[Dict]) -> Dict:
    """验证记忆"""
    validation = {
        "total": len(memories),
        "valid": 0,
        "issues": []
    }
    
    for m in memories:
        text = m.get("text", "")
        
        # 基本检查
        if len(text) < 3:
            validation["issues"].append({"id": m["id"], "issue": "text_too_short"})
            continue
        
        if not m.get("category"):
            validation["issues"].append({"id": m["id"], "issue": "no_category"})
            continue
        
        validation["valid"] += 1
    
    return validation


def fix_issues(duplicates: List[Tuple[Dict, Dict]]):
    """修复问题 - 删除重复"""
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        
        # 删除后面的重复项
        for m1, m2 in duplicates:
            print(f"🗑️ 删除重复: {m2['text'][:30]}...")
            table.delete(f"id = '{m2['id']}'")
        
        print(f"✅ 已删除 {len(duplicates)} 条重复记忆")
    except Exception as e:
        print(f"❌ 修复失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="Memory Health 0.1.6")
    parser.add_argument("command", choices=["report", "validate", "conflicts", "fix"])
    parser.add_argument("--fix", action="store_true", help="自动修复")
    
    args = parser.parse_args()
    
    print("🏥 Memory 健康检测...")
    memories = load_memories()
    print(f"加载 {len(memories)} 条记忆\n")
    
    if args.command == "report":
        health = calculate_health_score(memories)
        
        print(f"📊 健康度分数: {health['score']}/100")
        print(f"\n问题统计:")
        print(f"   矛盾: {health['conflicts']} 条")
        print(f"   过时: {health['outdated']} 条")
        print(f"   重复: {health['duplicates']} 条")
        
        if health['duplicates'] > 0:
            print(f"\n🔄 重复记忆示例:")
            for d in health['details']['duplicates'][:3]:
                print(f"   - {d['text1']}... ≈ {d['text2']}...")
    
    elif args.command == "validate":
        result = validate_memories(memories)
        print(f"验证结果:")
        print(f"   有效: {result['valid']}/{result['total']}")
        if result['issues']:
            print(f"\n⚠️ 问题:")
            for issue in result['issues'][:5]:
                print(f"   - {issue['id'][:8]}: {issue['issue']}")
    
    elif args.command == "conflicts":
        conflicts = detect_conflicts(memories)
        print(f"发现 {len(conflicts)} 对矛盾记忆:")
        for c in conflicts:
            print(f"\n❌ 矛盾:")
            print(f"   1. {c[0]['text'][:50]}")
            print(f"   2. {c[1]['text'][:50]}")
    
    elif args.command == "fix":
        duplicates = detect_duplicates(memories)
        print(f"发现 {len(duplicates)} 对重复")
        if args.fix:
            fix_issues(duplicates)
        else:
            print("使用 --fix 参数确认删除")


if __name__ == "__main__":
    main()
