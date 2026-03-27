#!/usr/bin/env python3
"""
Feedback Learner - 反馈学习闭环 v7.0

功能:
- 跟踪记忆使用效果
- 根据反馈调整重要性
- 记录修正历史
- 支持主动学习

Usage:
    feedback_learner.py track <memory_id> <outcome>   # 记录使用效果
    feedback_learner.py adjust                        # 调整重要性
    feedback_learner.py corrections                   # 查看修正历史
    feedback_learner.py learn <correction>            # 从修正中学习
    feedback_learner.py stats                         # 统计
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import defaultdict, Counter

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
FEEDBACK_DIR = MEMORY_DIR / "feedback"

# 调整参数
IMPORTANCE_BOOST = 0.1    # 有帮助时增加
IMPORTANCE_DECAY = 0.1    # 无帮助时减少
MIN_IMPORTANCE = 0.1      # 最低重要性
MAX_IMPORTANCE = 1.0      # 最高重要性

# 文件路径
FEEDBACK_LOG_FILE = FEEDBACK_DIR / "feedback_log.jsonl"
CORRECTIONS_FILE = FEEDBACK_DIR / "corrections.json"
IMPORTANCE_ADJUSTMENTS_FILE = FEEDBACK_DIR / "importance_adjustments.json"

# Ollama
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "deepseek-v3.2:cloud")

# 确保目录存在
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 反馈学习器
# ============================================================

class FeedbackLearner:
    """反馈学习器"""
    
    # 结果类型
    OUTCOME_HELPFUL = "helpful"      # 有帮助
    OUTCOME_IRRELEVANT = "irrelevant" # 无关
    OUTCOME_WRONG = "wrong"           # 错误
    OUTCOME_OUTDATED = "outdated"     # 过时
    
    def __init__(self):
        self.feedback_log: List[Dict] = []
        self.corrections: List[Dict] = []
        self.adjustments: Dict[str, List[Dict]] = {}  # memory_id -> adjustments
        self._load()
    
    def _load(self):
        """加载数据"""
        try:
            if FEEDBACK_LOG_FILE.exists():
                for line in FEEDBACK_LOG_FILE.read_text().strip().split("\n"):
                    if line:
                        self.feedback_log.append(json.loads(line))
            if CORRECTIONS_FILE.exists():
                self.corrections = json.loads(CORRECTIONS_FILE.read_text())
            if IMPORTANCE_ADJUSTMENTS_FILE.exists():
                self.adjustments = json.loads(IMPORTANCE_ADJUSTMENTS_FILE.read_text())
        except Exception as e:
            print(f"⚠️ 加载反馈数据失败: {e}", file=sys.stderr)
    
    def _save(self):
        """保存数据"""
        try:
            FEEDBACK_LOG_FILE.write_text("\n".join(json.dumps(f, ensure_ascii=False) for f in self.feedback_log))
            CORRECTIONS_FILE.write_text(json.dumps(self.corrections, ensure_ascii=False, indent=2))
            IMPORTANCE_ADJUSTMENTS_FILE.write_text(json.dumps(self.adjustments, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"⚠️ 保存反馈数据失败: {e}", file=sys.stderr)
    
    def track(self, memory_id: str, outcome: str, context: str = None):
        """记录记忆使用效果"""
        feedback = {
            "memory_id": memory_id,
            "outcome": outcome,
            "context": context[:200] if context else None,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_log.append(feedback)
        
        # 记录调整
        if memory_id not in self.adjustments:
            self.adjustments[memory_id] = []
        
        self.adjustments[memory_id].append({
            "outcome": outcome,
            "timestamp": feedback["timestamp"]
        })
        
        self._save()
        print(f"📝 记录反馈: {memory_id} -> {outcome}")
    
    def adjust_importance(self, memories: List[Dict]) -> Dict[str, float]:
        """根据反馈调整记忆重要性"""
        adjustments = {}
        
        for mem in memories:
            mem_id = mem.get("id")
            if not mem_id:
                continue
            
            current_importance = float(mem.get("importance", 0.5))
            mem_adjustments = self.adjustments.get(mem_id, [])
            
            if not mem_adjustments:
                continue
            
            # 计算最近反馈的影响
            recent = [a for a in mem_adjustments if self._is_recent(a.get("timestamp"))]
            
            if not recent:
                continue
            
            # 统计结果
            outcomes = Counter(a.get("outcome") for a in recent)
            
            # 调整重要性
            new_importance = current_importance
            new_importance += outcomes.get(self.OUTCOME_HELPFUL, 0) * IMPORTANCE_BOOST
            new_importance -= outcomes.get(self.OUTCOME_IRRELEVANT, 0) * IMPORTANCE_DECAY
            new_importance -= outcomes.get(self.OUTCOME_WRONG, 0) * IMPORTANCE_DECAY * 2
            new_importance -= outcomes.get(self.OUTCOME_OUTDATED, 0) * IMPORTANCE_DECAY
            
            # 限制范围
            new_importance = max(MIN_IMPORTANCE, min(MAX_IMPORTANCE, new_importance))
            
            if abs(new_importance - current_importance) > 0.01:
                adjustments[mem_id] = {
                    "old": current_importance,
                    "new": round(new_importance, 3),
                    "change": round(new_importance - current_importance, 3)
                }
                mem["importance"] = new_importance
        
        self._save()
        return adjustments
    
    def _is_recent(self, timestamp: str, days: int = 7) -> bool:
        """判断是否是最近 N 天"""
        if not timestamp:
            return False
        try:
            ts = datetime.fromisoformat(timestamp)
            return (datetime.now() - ts).days <= days
        except:
            return False
    
    def record_correction(self, memory_id: str, original: str, corrected: str, reason: str = None):
        """记录修正"""
        correction = {
            "memory_id": memory_id,
            "original": original,
            "corrected": corrected,
            "reason": reason,
            "corrected_at": datetime.now().isoformat()
        }
        
        self.corrections.append(correction)
        self._save()
        print(f"✏️ 记录修正: {memory_id}")
    
    def learn_from_corrections(self) -> List[Dict]:
        """从修正中学习"""
        learnings = []
        
        # 分析修正模式
        for correction in self.corrections[-10:]:
            if correction.get("analyzed"):
                continue
            
            # 提取学习点
            learning = {
                "memory_id": correction.get("memory_id"),
                "pattern": self._extract_pattern(correction.get("original"), correction.get("corrected")),
                "timestamp": datetime.now().isoformat()
            }
            
            if learning["pattern"]:
                learnings.append(learning)
                correction["analyzed"] = True
        
        self._save()
        return learnings
    
    def _extract_pattern(self, original: str, corrected: str) -> str:
        """提取修正模式"""
        if not original or not corrected:
            return None
        
        # 简单模式：长度变化
        if len(corrected) < len(original) * 0.7:
            return "simplify"  # 简化
        elif len(corrected) > len(original) * 1.3:
            return "expand"    # 扩展
        
        # 内容变化
        if "不" in corrected and "不" not in original:
            return "negate"    # 否定修正
        if "不" in original and "不" not in corrected:
            return "affirm"    # 肯定修正
        
        return "update"        # 一般更新
    
    def get_memory_score(self, memory_id: str) -> Dict:
        """获取记忆的反馈分数"""
        mem_feedback = [f for f in self.feedback_log if f.get("memory_id") == memory_id]
        
        if not mem_feedback:
            return {"score": 0.5, "feedback_count": 0}
        
        outcomes = Counter(f.get("outcome") for f in mem_feedback)
        total = len(mem_feedback)
        
        # 计算分数
        score = (
            outcomes.get(self.OUTCOME_HELPFUL, 0) * 1.0 +
            outcomes.get(self.OUTCOME_IRRELEVANT, 0) * 0.3 +
            outcomes.get(self.OUTCOME_WRONG, 0) * 0.0 +
            outcomes.get(self.OUTCOME_OUTDATED, 0) * 0.2
        ) / total if total > 0 else 0.5
        
        return {
            "score": round(score, 3),
            "feedback_count": total,
            "outcomes": dict(outcomes)
        }
    
    def stats(self) -> Dict:
        """统计"""
        outcomes = Counter(f.get("outcome") for f in self.feedback_log)
        
        # 按记忆统计
        mem_stats = defaultdict(lambda: defaultdict(int))
        for f in self.feedback_log:
            mem_id = f.get("memory_id")
            mem_stats[mem_id][f.get("outcome")] += 1
        
        # 找出最常被反馈的记忆
        top_memories = sorted(mem_stats.items(), key=lambda x: sum(x[1].values()), reverse=True)[:5]
        
        return {
            "total_feedback": len(self.feedback_log),
            "total_corrections": len(self.corrections),
            "by_outcome": dict(outcomes),
            "top_memories": [
                {"id": m[0], "feedback_count": sum(m[1].values())}
                for m in top_memories
            ],
            "recent_corrections": self.corrections[-3:] if self.corrections else []
        }


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Feedback Learner v7.0")
    parser.add_argument("command", choices=["track", "adjust", "corrections", "learn", "stats"])
    parser.add_argument("--memory-id", help="记忆 ID")
    parser.add_argument("--outcome", choices=["helpful", "irrelevant", "wrong", "outdated"], help="结果")
    parser.add_argument("--context", help="上下文")
    parser.add_argument("--original", help="原始内容")
    parser.add_argument("--corrected", help="修正内容")
    parser.add_argument("--reason", help="原因")
    
    args = parser.parse_args()
    learner = FeedbackLearner()
    
    if args.command == "track":
        if not args.memory_id or not args.outcome:
            print("❌ 请指定 --memory-id 和 --outcome")
            sys.exit(1)
        learner.track(args.memory_id, args.outcome, args.context)
    
    elif args.command == "adjust":
        # 加载记忆
        memories = []
        memory_file = MEMORY_DIR / "memories.json"
        if memory_file.exists():
            try:
                memories = json.loads(memory_file.read_text())
            except:
                pass
        
        adjustments = learner.adjust_importance(memories)
        if adjustments:
            print("📊 重要性调整:")
            for mem_id, adj in adjustments.items():
                print(f"  {mem_id}: {adj['old']:.3f} -> {adj['new']:.3f} ({adj['change']:+.3f})")
        else:
            print("无调整")
    
    elif args.command == "corrections":
        print(f"📋 共 {len(learner.corrections)} 条修正:")
        for c in learner.corrections[-10:]:
            print(f"  [{c.get('memory_id')}] {c.get('original')[:30]}... -> {c.get('corrected')[:30]}...")
    
    elif args.command == "learn":
        learnings = learner.learn_from_corrections()
        print(f"📚 提取 {len(learnings)} 个学习点:")
        for l in learnings:
            print(f"  [{l.get('memory_id')}] 模式: {l.get('pattern')}")
    
    elif args.command == "stats":
        stats = learner.stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {args.command}")


if __name__ == "__main__":
    main()
