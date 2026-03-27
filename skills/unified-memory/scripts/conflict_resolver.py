#!/usr/bin/env python3
"""
矛盾记忆自动解决器 v1.0
自动检测并解决记忆矛盾

策略:
- 高相似度 (>0.9): 自动合并，保留更完整版本
- 中等相似度 (0.7-0.9): 标记待确认，提供合并建议
- 低相似度 (<0.7): 标记矛盾，需用户明确选择
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
CONFLICTS_DIR = MEMORY_DIR / "conflicts"
RESOLVED_DIR = MEMORY_DIR / "resolved"


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    if MEMORIES_FILE.exists():
        return json.loads(MEMORIES_FILE.read_text())
    return []


def save_memories(memories: List[Dict]):
    """保存记忆"""
    MEMORIES_FILE.write_text(json.dumps(memories, indent=2, ensure_ascii=False))


def calculate_similarity(text1: str, text2: str) -> float:
    """计算文本相似度（简化版 Jaccard）"""
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


def detect_conflicts(memories: List[Dict]) -> List[Dict]:
    """检测矛盾记忆"""
    conflicts = []
    
    for i, m1 in enumerate(memories):
        for j, m2 in enumerate(memories[i+1:], i+1):
            text1 = m1.get("text", "")
            text2 = m2.get("text", "")
            
            if not text1 or not text2:
                continue
            
            # 检查是否属于同一主题
            similarity = calculate_similarity(text1, text2)
            
            if similarity > 0.3:  # 有关联
                # 检查是否有矛盾关键词
                contradiction_pairs = [
                    (["需要"], ["不需要"]),
                    (["要"], ["不要"]),
                    (["能"], ["不能"]),
                    (["可以"], ["不可以"]),
                    (["是"], ["不是"]),
                ]
                
                has_contradiction = False
                for keywords1, keywords2 in contradiction_pairs:
                    if any(kw in text1 for kw in keywords1) and any(kw in text2 for kw in keywords2):
                        has_contradiction = True
                        break
                    if any(kw in text2 for kw in keywords1) and any(kw in text1 for kw in keywords2):
                        has_contradiction = True
                        break
                
                if has_contradiction or similarity > 0.7:
                    conflicts.append({
                        "id1": m1.get("id", f"mem_{i}"),
                        "id2": m2.get("id", f"mem_{j}"),
                        "text1": text1[:100],
                        "text2": text2[:100],
                        "similarity": round(similarity, 3),
                        "type": "contradiction" if has_contradiction else "similar",
                        "strategy": "auto_merge" if similarity > 0.9 else "confirm" if similarity > 0.7 else "user_choice"
                    })
    
    return conflicts


def resolve_conflict(conflict: Dict, memories: List[Dict]) -> Dict:
    """解决单个矛盾"""
    strategy = conflict["strategy"]
    
    # 找到对应的记忆
    mem1 = next((m for m in memories if m.get("id") == conflict["id1"]), None)
    mem2 = next((m for m in memories if m.get("id") == conflict["id2"]), None)
    
    if not mem1 or not mem2:
        return {"status": "error", "message": "记忆不存在"}
    
    if strategy == "auto_merge":
        # 自动合并：保留更完整的版本
        merged_text = mem1["text"] if len(mem1["text"]) > len(mem2["text"]) else mem2["text"]
        merged = {
            "id": mem1["id"],  # 保留第一个ID
            "text": merged_text,
            "category": mem1.get("category", mem2.get("category", "general")),
            "importance": max(mem1.get("importance", 0.5), mem2.get("importance", 0.5)),
            "merged_from": [mem1["id"], mem2["id"]],
            "merged_at": datetime.now().isoformat()
        }
        return {
            "status": "merged",
            "merged": merged,
            "removed_id": mem2["id"]
        }
    
    elif strategy == "confirm":
        # 需要确认：生成合并建议
        return {
            "status": "needs_confirmation",
            "suggestion": f"两条记忆相似度 {conflict['similarity']}，建议合并",
            "text1": mem1["text"],
            "text2": mem2["text"]
        }
    
    else:
        # 用户选择
        return {
            "status": "needs_user_choice",
            "message": "请选择保留哪条记忆",
            "text1": mem1["text"],
            "text2": mem2["text"]
        }


def auto_resolve_all():
    """自动解决所有可解决的矛盾"""
    memories = load_memories()
    conflicts = detect_conflicts(memories)
    
    if not conflicts:
        print("✅ 未检测到矛盾记忆")
        return
    
    print(f"🔍 检测到 {len(conflicts)} 组潜在矛盾\n")
    
    resolved_count = 0
    for conflict in conflicts:
        result = resolve_conflict(conflict, memories)
        
        if result["status"] == "merged":
            # 更新记忆
            mem1_idx = next((i for i, m in enumerate(memories) if m.get("id") == result["merged"]["id"]), None)
            mem2_idx = next((i for i, m in enumerate(memories) if m.get("id") == result["removed_id"]), None)
            
            if mem1_idx is not None:
                memories[mem1_idx] = result["merged"]
            if mem2_idx is not None:
                memories.pop(mem2_idx)
            
            resolved_count += 1
            print(f"✅ 自动合并: {conflict['text1'][:50]}...")
        
        elif result["status"] == "needs_confirmation":
            print(f"⚠️ 待确认: {result['suggestion']}")
        
        else:
            print(f"❓ 需用户选择: {conflict['text1'][:30]}... vs {conflict['text2'][:30]}...")
    
    save_memories(memories)
    print(f"\n📊 统计: 自动解决 {resolved_count} 个，剩余 {len(conflicts) - resolved_count} 个需确认")


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="矛盾记忆解决器")
    parser.add_argument("action", choices=["detect", "resolve", "auto"],
                       help="操作类型")
    
    args = parser.parse_args()
    
    if args.action == "detect":
        conflicts = detect_conflicts(load_memories())
        if conflicts:
            print(f"🔍 检测到 {len(conflicts)} 组矛盾:\n")
            for c in conflicts:
                print(f"  [{c['type']}] 相似度: {c['similarity']}")
                print(f"    - {c['text1'][:50]}...")
                print(f"    - {c['text2'][:50]}...")
                print()
        else:
            print("✅ 未检测到矛盾记忆")
    
    elif args.action == "auto":
        auto_resolve_all()
    
    elif args.action == "resolve":
        conflicts = detect_conflicts(load_memories())
        if conflicts:
            # 逐个处理
            for conflict in conflicts:
                result = resolve_conflict(conflict, load_memories())
                print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("✅ 无需解决")


if __name__ == "__main__":
    main()
