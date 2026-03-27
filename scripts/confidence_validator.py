#!/usr/bin/env python3
"""
Confidence Validator - 置信度验证器 v7.0

功能:
- 检测过时记忆 (超过 N 天未验证)
- 检测矛盾记忆 (与其他记忆冲突)
- 标记可疑记忆，使用前需确认
- 支持记忆验证和修正

Usage:
    confidence_validator.py scan              # 扫描可疑记忆
    confidence_validator.py validate <id>     # 验证记忆
    confidence_validator.py conflict          # 检测矛盾
    confidence_validator.py stats             # 统计
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ============================================================
# 配置
# ============================================================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VALIDATION_DIR = MEMORY_DIR / "validation"

# 验证参数
STALE_DAYS = 30           # 超过 30 天未验证视为可能过时
CONFLICT_THRESHOLD = 0.7  # 矛盾检测阈值

# 文件路径
VALIDATION_STATE_FILE = VALIDATION_DIR / "validation_state.json"
CONFLICTS_FILE = VALIDATION_DIR / "conflicts.json"

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 确保目录存在
VALIDATION_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 置信度验证器
# ============================================================

class ConfidenceValidator:
    """置信度验证器"""
    
    # 置信度标记
    CONFIDENCE_VERIFIED = "✅ 已验证"      # 多次确认正确
    CONFIDENCE_STALE = "⚠️ 可能过时"      # 超过 N 天未更新
    CONFIDENCE_CONFLICT = "❌ 矛盾"        # 与其他记忆冲突
    CONFIDENCE_PENDING = "🔄 待更新"      # 用户行为已改变
    
    def __init__(self):
        self.validation_state: Dict[str, Dict] = {}  # memory_id -> validation info
        self.conflicts: List[Dict] = []
        self._load()
    
    def _load(self):
        """加载状态"""
        try:
            if VALIDATION_STATE_FILE.exists():
                self.validation_state = json.loads(VALIDATION_STATE_FILE.read_text())
            if CONFLICTS_FILE.exists():
                self.conflicts = json.loads(CONFLICTS_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载验证状态失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存状态"""
        try:
            VALIDATION_STATE_FILE.write_text(json.dumps(self.validation_state, ensure_ascii=False, indent=2))
            CONFLICTS_FILE.write_text(json.dumps(self.conflicts, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存验证状态失败: {e}", file=sys.stderr)
    
    def scan_stale(self, memories: List[Dict]) -> List[Dict]:
        """扫描过时记忆"""
        stale = []
        now = datetime.now()
        
        for mem in memories:
            mem_id = mem.get("id")
            created_at = mem.get("created_at") or mem.get("timestamp")
            
            if not created_at:
                continue
            
            try:
                if "T" in created_at:
                    mem_time = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
                else:
                    mem_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                
                age_days = (now - mem_time).days
                
                if age_days > STALE_DAYS:
                    # 检查是否已验证
                    val_info = self.validation_state.get(mem_id, {})
                    last_validated = val_info.get("last_validated")
                    
                    if last_validated:
                        last_val_time = datetime.fromisoformat(last_validated)
                        if (now - last_val_time).days < STALE_DAYS:
                            continue  # 最近已验证
                    
                    stale.append({
                        "id": mem_id,
                        "text": mem.get("text", "")[:100],
                        "age_days": age_days,
                        "confidence": self.CONFIDENCE_STALE,
                        "last_validated": val_info.get("last_validated")
                    })
            except Exception as e:
                continue
        
        return stale
    
    def detect_conflicts(self, memories: List[Dict]) -> List[Dict]:
        """检测矛盾记忆"""
        conflicts = []
        
        # 按主题分组
        by_topic = defaultdict(list)
        for mem in memories:
            text = mem.get("text", "").lower()
            # 提取主题关键词
            keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
            for kw in keywords[:2]:
                by_topic[kw].append(mem)
        
        # 检测同一主题下的矛盾
        for topic, mems in by_topic.items():
            if len(mems) < 2:
                continue
            
            # 简单矛盾检测：查找否定词
            positive = []
            negative = []
            
            for mem in mems:
                text = mem.get("text", "").lower()
                if any(neg in text for neg in ["不", "没", "无", "非", "不是", "没有"]):
                    negative.append(mem)
                else:
                    positive.append(mem)
            
            # 同时存在肯定和否定 → 可能矛盾
            if positive and negative:
                conflict = {
                    "topic": topic,
                    "positive": [{"id": m.get("id"), "text": m.get("text", "")[:50]} for m in positive[:2]],
                    "negative": [{"id": m.get("id"), "text": m.get("text", "")[:50]} for m in negative[:2]],
                    "detected_at": datetime.now().isoformat()
                }
                conflicts.append(conflict)
                
                # 更新记忆置信度
                for mem in positive + negative:
                    mem_id = mem.get("id")
                    if mem_id:
                        self.validation_state[mem_id] = {
                            "confidence": self.CONFIDENCE_CONFLICT,
                            "conflict_with": [m.get("id") for m in (positive + negative) if m.get("id") != mem_id],
                            "last_checked": datetime.now().isoformat()
                        }
        
        self.conflicts.extend(conflicts)
        self._save()
        
        return conflicts
    
    def validate(self, memory_id: str, is_correct: bool = True, note: str = None):
        """验证记忆"""
        self.validation_state[memory_id] = {
            "confidence": self.CONFIDENCE_VERIFIED if is_correct else self.CONFIDENCE_PENDING,
            "last_validated": datetime.now().isoformat(),
            "validation_note": note
        }
        self._save()
    
    def get_confidence(self, memory_id: str) -> str:
        """获取记忆置信度"""
        if memory_id in self.validation_state:
            return self.validation_state[memory_id].get("confidence", self.CONFIDENCE_VERIFIED)
        return self.CONFIDENCE_VERIFIED  # 默认已验证
    
    def mark_needs_update(self, memory_id: str, reason: str = None):
        """标记需要更新"""
        self.validation_state[memory_id] = {
            "confidence": self.CONFIDENCE_PENDING,
            "needs_update": True,
            "reason": reason,
            "marked_at": datetime.now().isoformat()
        }
        self._save()
    
    def stats(self) -> Dict:
        """统计"""
        by_confidence = defaultdict(int)
        for val in self.validation_state.values():
            conf = val.get("confidence", self.CONFIDENCE_VERIFIED)
            by_confidence[conf] += 1
        
        return {
            "total_validated": len(self.validation_state),
            "conflicts_detected": len(self.conflicts),
            "by_confidence": dict(by_confidence),
            "recent_conflicts": self.conflicts[-3:] if self.conflicts else []
        }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Confidence Validator v7.0")
    parser.add_argument("command", choices=["scan", "validate", "conflict", "stats"])
    parser.add_argument("--memory-id", help="记忆 ID")
    parser.add_argument("--correct", action="store_true", help="验证为正确")
    parser.add_argument("--incorrect", action="store_true", help="验证为错误")
    parser.add_argument("--note", help="备注")
    
    args = parser.parse_args()
    validator = ConfidenceValidator()
    
    # 加载记忆
    memories = []
    memory_file = MEMORY_DIR / "memories.json"
    if memory_file.exists():
        try:
            memories = json.loads(memory_file.read_text())
        except:
            pass
    
    if args.command == "scan":
        stale = validator.scan_stale(memories)
        print(f"📋 发现 {len(stale)} 条可能过时的记忆:")
        for s in stale[:10]:
            print(f"  [{s['confidence']}] {s['text']}...")
    
    elif args.command == "validate":
        if not args.memory_id:
            print("❌ 请指定 --memory-id")
            sys.exit(1)
        is_correct = not args.incorrect
        validator.validate(args.memory_id, is_correct, args.note)
        print(f"✅ 已验证: {args.memory_id}")
    
    elif args.command == "conflict":
        conflicts = validator.detect_conflicts(memories)
        print(f"📋 发现 {len(conflicts)} 个矛盾:")
        for c in conflicts[:5]:
            print(f"  主题 [{c['topic']}]:")
            for p in c.get("positive", []):
                print(f"    + {p['text']}...")
            for n in c.get("negative", []):
                print(f"    - {n['text']}...")
    
    elif args.command == "stats":
        stats = validator.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()
