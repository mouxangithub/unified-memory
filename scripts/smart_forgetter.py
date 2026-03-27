#!/usr/bin/env python3
"""
Smart Forgetter - 智能遗忘器 v7.0

功能:
- 自动遗忘低价值记忆
- 合并重复记忆
- 归档旧记忆
- 压缩 L3 冷记忆

Usage:
    smart_forgetter.py forget --dry-run        # 预览遗忘
    smart_forgetter.py forget                  # 执行遗忘
    smart_forgetter.py compress                # 压缩冷记忆
    smart_forgetter.py archive --days 90       # 归档旧记忆
    smart_forgetter.py stats                   # 统计
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
ARCHIVE_DIR = MEMORY_DIR / "archive"
FORGETTER_STATE_FILE = MEMORY_DIR / "forgetter_state.json"

# 遗忘参数
FORGET_IMPORTANCE = 0.1           # 低于此值遗忘
FORGET_AGE_DAYS = 90              # 超过此天数考虑遗忘
FORGET_NEVER_ACCESSED_DAYS = 60   # 从未访问则遗忘
DUPLICATE_THRESHOLD = 0.95        # 相似度阈值
MAX_ARCHIVE_SIZE_MB = 100         # 归档目录最大大小

# 确保目录存在
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 智能遗忘器
# ============================================================

class SmartForgetter:
    """智能遗忘器"""
    
    def __init__(self):
        self.state: Dict = {
            "last_forget": None,
            "forgotten_count": 0,
            "archived_count": 0,
            "compressed_count": 0
        }
        self._load()
    
    def _load(self):
        """加载状态"""
        try:
            if FORGETTER_STATE_FILE.exists():
                self.state = json.loads(FORGETTER_STATE_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载状态失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存状态"""
        try:
            FORGETTER_STATE_FILE.write_text(json.dumps(self.state, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存状态失败: {e}", file=sys.stderr)
    
    def find_forgettable(self, memories: List[Dict]) -> List[Dict]:
        """找出可遗忘的记忆"""
        forgettable = []
        now = datetime.now()
        
        for mem in memories:
            mem_id = mem.get("id")
            text = mem.get("text", "")
            importance = float(mem.get("importance", 0.5))
            
            # 条件 1: 重要性极低
            if importance < FORGET_IMPORTANCE:
                forgettable.append({
                    "id": mem_id,
                    "reason": "low_importance",
                    "importance": importance,
                    "text": text[:100]
                })
                continue
            
            # 条件 2: 年龄过大
            created_at = mem.get("created_at") or mem.get("timestamp")
            if created_at:
                try:
                    if "T" in created_at:
                        mem_time = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        mem_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    
                    age_days = (now - mem_time).days
                    
                    if age_days > FORGET_AGE_DAYS:
                        forgettable.append({
                            "id": mem_id,
                            "reason": "too_old",
                            "age_days": age_days,
                            "text": text[:100]
                        })
                except:
                    pass
        
        return forgettable
    
    def find_duplicates(self, memories: List[Dict]) -> List[List[str]]:
        """查找重复记忆组"""
        # 简单的基于文本相似度的重复检测
        groups = []
        visited = set()
        
        for i, mem1 in enumerate(memories):
            id1 = mem1.get("id")
            if id1 in visited:
                continue
            
            text1 = mem1.get("text", "").lower()
            if not text1:
                continue
            
            group = [id1]
            for j, mem2 in enumerate(memories[i+1:], i+1):
                id2 = mem2.get("id")
                if id2 in visited:
                    continue
                
                text2 = mem2.get("text", "").lower()
                if not text2:
                    continue
                
                # 简单相似度
                similarity = self._simple_similarity(text1, text2)
                if similarity >= DUPLICATE_THRESHOLD:
                    group.append(id2)
                    visited.add(id2)
            
            if len(group) > 1:
                groups.append(group)
                visited.add(id1)
        
        return groups
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """计算简单相似度"""
        # 词集相似度
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def archive_old(self, memories: List[Dict], days: int = 90, dry_run: bool = False) -> List[str]:
        """归档旧记忆"""
        now = datetime.now()
        archived_ids = []
        
        for mem in memories:
            created_at = mem.get("created_at") or mem.get("timestamp")
            if not created_at:
                continue
            
            try:
                if "T" in created_at:
                    mem_time = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
                else:
                    mem_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                
                age_days = (now - mem_time).days
                
                if age_days > days:
                    if not dry_run:
                        self._archive_memory(mem)
                    archived_ids.append(mem.get("id"))
            except:
                pass
        
        if not dry_run and archived_ids:
            self.state["archived_count"] += len(archived_ids)
            self.state["last_forget"] = datetime.now().isoformat()
            self._save()
        
        return archived_ids
    
    def _archive_memory(self, memory: Dict):
        """归档单个记忆"""
        archive_file = ARCHIVE_DIR / f"mem_{memory.get('id')}_{datetime.now().strftime('%Y%m%d')}.json"
        archive_file.write_text(json.dumps(memory, ensure_ascii=False, indent=2))
    
    def compress_cold(self, memories: List[Dict]) -> Dict:
        """压缩冷记忆"""
        compressed = 0
        compression_stats = {"before": 0, "after": 0}
        
        for mem in memories:
            # 检查是否是冷记忆（重要性低或旧）
            importance = float(mem.get("importance", 0.5))
            
            if importance < 0.3:
                # 压缩文本
                original_len = len(mem.get("text", ""))
                if original_len > 200:
                    compressed_text = self._compress_text(mem.get("text", ""))
                    mem["text"] = compressed_text
                    mem["compressed"] = True
                    mem["original_length"] = original_len
                    compressed += 1
                    
                    compression_stats["before"] += original_len
                    compression_stats["after"] += len(compressed_text)
        
        if compressed > 0:
            self.state["compressed_count"] += compressed
            self._save()
        
        return {
            "compressed_count": compressed,
            "compression_ratio": compression_stats["after"] / compression_stats["before"] if compression_stats["before"] > 0 else 1.0
        }
    
    def _compress_text(self, text: str) -> str:
        """压缩文本"""
        lines = text.split("\n")
        if len(lines) > 5:
            # 保留前 3 行和后 1 行，中间压缩
            compressed = lines[:3]
            compressed.append(f"... ({len(lines)-4} lines omitted) ...")
            compressed.append(lines[-1])
            return "\n".join(compressed)
        elif len(text) > 200:
            return text[:150] + "... [truncated]"
        return text
    
    def clean_archive(self):
        """清理归档目录"""
        # 检查归档大小
        total_size = sum(f.stat().st_size for f in ARCHIVE_DIR.rglob("*") if f.is_file())
        total_mb = total_size / (1024 * 1024)
        
        if total_mb > MAX_ARCHIVE_SIZE_MB:
            print(f"归档目录过大 ({total_mb:.1f} MB)，开始清理...")
            
            # 按时间排序，删除最旧的
            files = sorted(ARCHIVE_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime)
            
            removed = 0
            while total_mb > MAX_ARCHIVE_SIZE_MB * 0.8 and files:
                f = files.pop(0)
                size = f.stat().st_size / (1024 * 1024)
                f.unlink()
                total_mb -= size
                removed += 1
            
            print(f"已删除 {removed} 个归档文件")
    
    def stats(self) -> Dict:
        """统计"""
        # 计算归档目录大小
        total_size = sum(f.stat().st_size for f in ARCHIVE_DIR.rglob("*") if f.is_file())
        
        return {
            "state": self.state,
            "archive_size_mb": round(total_size / (1024 * 1024), 2),
            "archive_files": len(list(ARCHIVE_DIR.glob("*.json"))),
            "parameters": {
                "forget_importance": FORGET_IMPORTANCE,
                "forget_age_days": FORGET_AGE_DAYS,
                "duplicate_threshold": DUPLICATE_THRESHOLD,
                "max_archive_size_mb": MAX_ARCHIVE_SIZE_MB
            }
        }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Smart Forgetter v7.0")
    parser.add_argument("command", choices=["forget", "compress", "archive", "clean", "stats"])
    parser.add_argument("--dry-run", action="store_true", help="仅预览")
    parser.add_argument("--days", type=int, default=90, help="天数")
    
    args = parser.parse_args()
    
    forgetter = SmartForgetter()
    
    # 加载记忆
    memories = []
    memory_file = MEMORY_DIR / "memories.json"
    if memory_file.exists():
        try:
            memories = json.loads(memory_file.read_text())
        except:
            pass
    
    if args.command == "forget":
        forgettable = forgetter.find_forgettable(memories)
        print(f"📋 发现 {len(forgettable)} 条可遗忘记忆:")
        for f in forgettable[:10]:
            print(f"  [{f['reason']}] {f['text'][:50]}...")
        
        if not args.dry_run and forgettable:
            # 实际执行遗忘
            forget_ids = {f["id"] for f in forgettable}
            remaining = [m for m in memories if m.get("id") not in forget_ids]
            memory_file.write_text(json.dumps(remaining, ensure_ascii=False, indent=2))
            
            forgetter.state["forgotten_count"] += len(forgettable)
            forgetter.state["last_forget"] = datetime.now().isoformat()
            forgetter._save()
            print(f"✅ 已遗忘 {len(forgettable)} 条记忆")
    
    elif args.command == "compress":
        result = forgetter.compress_cold(memories)
        print(f"✅ 压缩 {result['compressed_count']} 条记忆")
        print(f"压缩率: {result['compression_ratio']:.1%}")
    
    elif args.command == "archive":
        archived = forgetter.archive_old(memories, args.days, args.dry_run)
        print(f"📦 {'将' if args.dry_run else '已'}归档 {len(archived)} 条记忆")
    
    elif args.command == "clean":
        forgetter.clean_archive()
    
    elif args.command == "stats":
        stats = forgetter.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()
