#!/usr/bin/env python3
"""
Memory Heatmap - 记忆访问热力图 v1.0

功能:
- 统计记忆访问频率
- 自动提升高频记忆权重
- 生成热力图可视化

Usage:
    mem heatmap          # 显示热力图
    mem heatmap --boost  # 自动提升高频记忆权重
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict

MEMORY_DIR = Path.home() / ".openclaw/workspace/memory"
MEMORIES_FILE = MEMORY_DIR / "memories.json"
ACCESS_FILE = MEMORY_DIR / "access_history.json"
HEATMAP_FILE = MEMORY_DIR / "heatmap.json"


def load_memories() -> List[Dict]:
    """加载所有记忆"""
    if MEMORIES_FILE.exists():
        return json.loads(MEMORIES_FILE.read_text())
    return []


def save_memories(memories: List[Dict]):
    """保存记忆"""
    MEMORIES_FILE.write_text(json.dumps(memories, indent=2, ensure_ascii=False))


def load_access_history() -> List[Dict]:
    """加载访问历史"""
    if ACCESS_FILE.exists():
        return json.loads(ACCESS_FILE.read_text())
    return []


def calculate_heatmap(memories: List[Dict], access_history: List[Dict]) -> Dict:
    """计算热力图"""
    # 统计访问次数
    access_count = defaultdict(int)
    for entry in access_history:
        # 兼容不同格式
        if isinstance(entry, dict):
            mem_id = entry.get("memory_id") or entry.get("id")
        elif isinstance(entry, str):
            mem_id = entry
        else:
            continue
        if mem_id:
            access_count[mem_id] += 1
    
    # 为每个记忆计算热度
    heatmap = []
    for m in memories:
        mem_id = m.get("id")
        count = access_count.get(mem_id, 0) + m.get("access_count", 0)
        
        # 热度分数 = 访问次数 × 重要性
        importance = m.get("importance", 0.5)
        heat_score = count * importance
        
        heatmap.append({
            "id": mem_id,
            "text": m.get("text", "")[:50],
            "category": m.get("category", "?"),
            "access_count": count,
            "importance": importance,
            "heat_score": round(heat_score, 2),
            "last_accessed": m.get("last_accessed", "?")
        })
    
    # 按热度排序
    heatmap.sort(key=lambda x: x["heat_score"], reverse=True)
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_memories": len(memories),
        "heatmap": heatmap[:20]  # 只保留前20
    }


def boost_hot_memories(memories: List[Dict], heatmap: Dict, threshold: int = 3) -> int:
    """提升高频记忆权重"""
    boosted = 0
    
    for entry in heatmap.get("heatmap", []):
        if entry["access_count"] >= threshold:
            # 找到对应记忆
            for m in memories:
                if m.get("id") == entry["id"]:
                    # 提升重要性（最高0.9）
                    old_importance = m.get("importance", 0.5)
                    new_importance = min(0.9, old_importance + 0.1)
                    m["importance"] = new_importance
                    m["boosted"] = True
                    boosted += 1
                    break
    
    return boosted


def visualize_heatmap(heatmap: Dict) -> str:
    """生成可视化文本"""
    lines = ["🔥 记忆访问热力图\n"]
    lines.append(f"统计时间: {heatmap['generated_at'][:10]}")
    lines.append(f"总记忆数: {heatmap['total_memories']}\n")
    lines.append("=" * 60)
    
    for i, entry in enumerate(heatmap.get("heatmap", [])[:10], 1):
        # 热度条
        heat = entry["heat_score"]
        bar_len = min(int(heat * 2), 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        
        lines.append(f"\n[{i:2d}] 🔥 {heat:5.1f} |{bar}|")
        lines.append(f"     📝 {entry['text']}...")
        lines.append(f"     📊 访问: {entry['access_count']} | 重要: {entry['importance']:.1f} | 分类: {entry['category']}")
    
    return "\n".join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Heatmap - 记忆访问热力图")
    parser.add_argument("--boost", "-b", action="store_true", help="自动提升高频记忆权重")
    parser.add_argument("--threshold", "-t", type=int, default=3, help="提升阈值")
    parser.add_argument("--save", "-s", action="store_true", help="保存热力图")
    
    args = parser.parse_args()
    
    memories = load_memories()
    access_history = load_access_history()
    
    # 计算热力图
    heatmap = calculate_heatmap(memories, access_history)
    
    if args.boost:
        boosted = boost_hot_memories(memories, heatmap, args.threshold)
        save_memories(memories)
        print(f"✅ 已提升 {boosted} 条高频记忆的权重\n")
    
    # 显示热力图
    print(visualize_heatmap(heatmap))
    
    # 保存
    if args.save:
        HEATMAP_FILE.write_text(json.dumps(heatmap, indent=2, ensure_ascii=False))
        print(f"\n💾 热力图已保存到 {HEATMAP_FILE}")


if __name__ == "__main__":
    main()
