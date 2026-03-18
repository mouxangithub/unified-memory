#!/usr/bin/env python3
"""
Memory Manager - 统一记忆管理 v5.0

整合功能:
- 记忆去重与合并
- 重要性衰减
- 记忆清理
- 统计报告

Usage:
    memory_manager.py dedup              # 去重
    memory_manager.py decay              # 应用衰减
    memory_manager.py clean --days 30    # 清理过期
    memory_manager.py stats              # 统计报告
    memory_manager.py health             # 健康检查
"""

import argparse
import json
import os
import re
import sys
import uuid
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import Counter, defaultdict

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

# 衰减配置
DECAY_HALF_LIFE = 30  # 30天半衰期
DECAY_MIN_IMPORTANCE = 0.1  # 最低重要性


# ============================================================
# 向量工具
# ============================================================

def get_embedding(text: str) -> Optional[List[float]]:
    """获取向量"""
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            timeout=30
        )
        return r.json().get("embedding")
    except:
        return None


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """计算余弦相似度"""
    import math
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ============================================================
# 记忆加载
# ============================================================

def load_all_memories() -> List[Dict]:
    """加载所有记忆"""
    memories = []
    
    for md_file in sorted(MEMORY_DIR.glob("*.md")):
        with open(md_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith('-'):
                    continue
                
                # 支持带标签的新格式: - [时间] [T=标签] [分类] [范围] [I=重要性] 文本
                # 或旧格式: - [时间] [分类] [范围] [I=重要性] 文本
                match = re.match(
                    r'- \[([^\]]+)\] (?:\[T=([^\]]+)\] )?\[([^\]]+)\] \[([^\]]+)\](?: \[I=([^\]]+)\])? (.+)',
                    line
                )
                if match:
                    timestamp_str, tags, category, scope, importance_str, text = match.groups()
                    try:
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except:
                        timestamp = datetime.now()
                    
                    memories.append({
                        "timestamp": timestamp,
                        "timestamp_str": timestamp_str,
                        "tags": tags.split(",") if tags else [],
                        "category": category,
                        "scope": scope,
                        "importance": float(importance_str) if importance_str else 0.5,
                        "text": text,
                        "file": md_file.name,
                        "line": line
                    })
    
    return memories


# ============================================================
# 去重
# ============================================================

def find_duplicates(memories: List[Dict], threshold: float = 0.85) -> List[Tuple[int, int, float]]:
    """找出相似的记忆对"""
    print("🔍 计算相似度...")
    
    # 获取向量
    embeddings = []
    for m in memories:
        emb = get_embedding(m["text"])
        embeddings.append(emb)
    
    # 比较
    duplicates = []
    n = len(memories)
    
    for i in range(n):
        if embeddings[i] is None:
            continue
        for j in range(i + 1, n):
            if embeddings[j] is None:
                continue
            
            sim = cosine_similarity(embeddings[i], embeddings[j])
            if sim >= threshold:
                duplicates.append((i, j, sim))
    
    return duplicates


def dedup_memories(dry_run: bool = True):
    """去重"""
    memories = load_all_memories()
    print(f"📊 总记忆数: {len(memories)}")
    
    # 按类别分组去重
    by_category = defaultdict(list)
    for i, m in enumerate(memories):
        by_category[m["category"]].append((i, m))
    
    all_duplicates = []
    
    for category, items in by_category.items():
        print(f"\n📂 检查类别: {category} ({len(items)} 条)")
        
        # 只检查同类别内的重复
        cat_memories = [m for _, m in items]
        cat_indices = [i for i, _ in items]
        
        for i in range(len(cat_memories)):
            for j in range(i + 1, len(cat_memories)):
                m1, m2 = cat_memories[i], cat_memories[j]
                
                # 文本相似度检查
                text1, text2 = m1["text"], m2["text"]
                
                # 简单文本相似度
                common = len(set(text1) & set(text2))
                total = len(set(text1) | set(text2))
                if total > 0:
                    text_sim = common / total
                else:
                    text_sim = 0
                
                # 如果文本高度相似
                if text_sim > 0.6:
                    # 保留重要性更高的
                    if m1["importance"] >= m2["importance"]:
                        keep, remove = cat_indices[i], cat_indices[j]
                    else:
                        keep, remove = cat_indices[j], cat_indices[i]
                    
                    all_duplicates.append({
                        "keep": memories[keep],
                        "remove": memories[remove],
                        "similarity": text_sim
                    })
    
    if not all_duplicates:
        print("\n✅ 没有发现重复记忆")
        return
    
    print(f"\n⚠️ 发现 {len(all_duplicates)} 对重复记忆")
    
    for dup in all_duplicates:
        print(f"\n  相似度: {dup['similarity']:.2f}")
        print(f"  保留: [{dup['keep']['importance']:.2f}] {dup['keep']['text'][:50]}...")
        print(f"  删除: [{dup['remove']['importance']:.2f}] {dup['remove']['text'][:50]}...")
    
    if dry_run:
        print("\n🔍 以上为预览，使用 --execute 执行实际删除")
    else:
        # 执行删除
        remove_lines = set()
        for dup in all_duplicates:
            remove_lines.add(dup["remove"]["line"])
        
        for md_file in MEMORY_DIR.glob("*.md"):
            lines = []
            with open(md_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() not in remove_lines:
                        lines.append(line)
            
            with open(md_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
        
        print(f"\n✅ 已删除 {len(all_duplicates)} 条重复记忆")


# ============================================================
# 衰减
# ============================================================

def apply_decay(dry_run: bool = True):
    """应用重要性衰减"""
    memories = load_all_memories()
    print(f"📊 总记忆数: {len(memories)}")
    
    decayed = []
    now = datetime.now()
    
    for m in memories:
        days_old = (now - m["timestamp"]).days
        
        # 指数衰减
        decay_factor = 0.5 ** (days_old / DECAY_HALF_LIFE)
        new_importance = max(DECAY_MIN_IMPORTANCE, m["importance"] * decay_factor)
        
        if new_importance < m["importance"] - 0.05:  # 变化超过 0.05 才记录
            decayed.append({
                "memory": m,
                "old_importance": m["importance"],
                "new_importance": new_importance,
                "days_old": days_old
            })
    
    if not decayed:
        print("\n✅ 没有需要衰减的记忆")
        return
    
    print(f"\n📉 需要衰减 {len(decayed)} 条记忆")
    
    for d in decayed[:10]:  # 只显示前 10 条
        print(f"  [{d['old_importance']:.2f} → {d['new_importance']:.2f}] "
              f"({d['days_old']}天) {d['memory']['text'][:40]}...")
    
    if dry_run:
        print(f"\n🔍 以上为预览，使用 --execute 执行实际衰减")
    else:
        # 更新文件
        file_changes = defaultdict(list)
        
        for d in decayed:
            m = d["memory"]
            old_line = m["line"]
            new_importance = d["new_importance"]
            
            # 构建新行
            new_line = re.sub(
                r'\[I=[^\]]+\]',
                f'[I={new_importance:.2f}]',
                old_line
            )
            
            file_changes[m["file"]].append((old_line, new_line))
        
        for filename, changes in file_changes.items():
            filepath = MEMORY_DIR / filename
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            for old_line, new_line in changes:
                content = content.replace(old_line, new_line)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        
        print(f"\n✅ 已更新 {len(decayed)} 条记忆的重要性")


# ============================================================
# 清理
# ============================================================

def clean_old_memories(days: int = 30, dry_run: bool = True):
    """清理过期记忆"""
    cutoff = datetime.now() - timedelta(days=days)
    
    cleaned = []
    snapshot_dir = MEMORY_DIR / "snapshots"
    snapshot_dir.mkdir(exist_ok=True)
    
    for md_file in MEMORY_DIR.glob("*.md"):
        try:
            date_str = md_file.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date < cutoff:
                cleaned.append((md_file, file_date))
        except ValueError:
            continue
    
    if not cleaned:
        print(f"\n✅ 没有需要清理的记忆 (保留 {days} 天)")
        return
    
    print(f"\n🧹 发现 {len(cleaned)} 个过期文件 (超过 {days} 天)")
    
    for f, date in cleaned:
        print(f"  {f.name} ({date.strftime('%Y-%m-%d')})")
    
    if dry_run:
        print("\n🔍 以上为预览，使用 --execute 执行实际清理")
    else:
        import shutil
        for f, _ in cleaned:
            shutil.move(str(f), str(snapshot_dir / f.name))
        
        print(f"\n✅ 已移动到 {snapshot_dir}")


# ============================================================
# 统计
# ============================================================

def show_stats():
    """显示统计"""
    memories = load_all_memories()
    
    # 基本统计
    print(f"📊 记忆统计")
    print(f"=" * 50)
    print(f"总记忆数: {len(memories)}")
    
    # 按类别
    by_category = Counter(m["category"] for m in memories)
    print(f"\n按类别:")
    for cat, count in by_category.most_common():
        avg_importance = sum(m["importance"] for m in memories if m["category"] == cat) / count
        print(f"  {cat}: {count} 条 (平均重要性: {avg_importance:.2f})")
    
    # 按标签
    all_tags = []
    for m in memories:
        all_tags.extend(m.get("tags", []))
    if all_tags:
        by_tag = Counter(all_tags)
        print(f"\n按标签:")
        for tag, count in by_tag.most_common():
            print(f"  #{tag}: {count} 条")
    
    # 按时间
    by_date = Counter(m["timestamp"].strftime("%Y-%m-%d") for m in memories)
    print(f"\n按日期 (最近7天):")
    for date, count in sorted(by_date.items(), reverse=True)[:7]:
        print(f"  {date}: {count} 条")
    
    # 重要性分布
    high = len([m for m in memories if m["importance"] > 0.6])
    medium = len([m for m in memories if 0.3 <= m["importance"] <= 0.6])
    low = len([m for m in memories if m["importance"] < 0.3])
    
    print(f"\n重要性分布:")
    print(f"  高 (>0.6): {high} 条")
    print(f"  中 (0.3-0.6): {medium} 条")
    print(f"  低 (<0.3): {low} 条")
    
    # 向量数据库
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        vector_count = table.count_rows()
        print(f"\n向量数据库: {vector_count} 条")
    except:
        print(f"\n向量数据库: 未初始化")


# ============================================================
# 健康检查
# ============================================================

def health_check():
    """健康检查"""
    issues = []
    
    # 1. 检查向量覆盖率
    memories = load_all_memories()
    try:
        import lancedb
        db = lancedb.connect(str(VECTOR_DB_DIR))
        table = db.open_table("memories")
        vector_count = table.count_rows()
        
        coverage = vector_count / len(memories) if memories else 0
        if coverage < 0.8:
            issues.append(f"向量覆盖率低: {coverage:.1%} ({vector_count}/{len(memories)})")
    except:
        issues.append("向量数据库未初始化")
    
    # 2. 检查分类一致性（排除标签字段）
    categories = set()
    for m in memories:
        cat = m["category"]
        # 跳过标签字段 (T=xxx)
        if not cat.startswith("T="):
            categories.add(cat)
    standard_categories = {"profile", "preferences", "entities", "events", "cases", "patterns", "fact", "learning", "decision"}
    non_standard = categories - standard_categories
    if non_standard:
        issues.append(f"非标准分类: {non_standard}")
    
    # 3. 检查过期记忆
    old_cutoff = datetime.now() - timedelta(days=90)
    old_memories = [m for m in memories if m["timestamp"] < old_cutoff]
    if old_memories:
        issues.append(f"超过90天的记忆: {len(old_memories)} 条")
    
    # 4. 检查低重要性记忆
    low_importance = [m for m in memories if m["importance"] < 0.2]
    if low_importance:
        issues.append(f"低重要性记忆 (<0.2): {len(low_importance)} 条")
    
    # 输出
    print("🏥 健康检查")
    print("=" * 50)
    
    if not issues:
        print("✅ 系统健康")
    else:
        print(f"⚠️ 发现 {len(issues)} 个问题:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n建议操作:")
        print("  - 运行 memory_manager.py dedup --execute")
        print("  - 运行 memory_manager.py decay --execute")
        print("  - 运行 memory_manager.py clean --days 30 --execute")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Memory Manager v5.0")
    subparsers = parser.add_subparsers(dest="command")
    
    # dedup
    dedup_p = subparsers.add_parser("dedup", help="去重")
    dedup_p.add_argument("--execute", action="store_true", help="执行实际操作")
    
    # decay
    decay_p = subparsers.add_parser("decay", help="应用衰减")
    decay_p.add_argument("--execute", action="store_true")
    
    # clean
    clean_p = subparsers.add_parser("clean", help="清理过期")
    clean_p.add_argument("--days", type=int, default=30)
    clean_p.add_argument("--execute", action="store_true")
    
    # stats
    subparsers.add_parser("stats", help="统计报告")
    
    # health
    subparsers.add_parser("health", help="健康检查")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == "dedup":
            dedup_memories(dry_run=not args.execute)
        
        elif args.command == "decay":
            apply_decay(dry_run=not args.execute)
        
        elif args.command == "clean":
            clean_old_memories(args.days, dry_run=not args.execute)
        
        elif args.command == "stats":
            show_stats()
        
        elif args.command == "health":
            health_check()
    
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
