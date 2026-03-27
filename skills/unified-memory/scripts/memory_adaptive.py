#!/usr/bin/env python3
"""
Memory Adaptive Confidence - 动态置信度自适应 v1.0

功能:
- 置信度衰减模型
- 置信度恢复模型
- 反馈驱动的自适应调整
- 置信度平滑曲线

Usage:
    python3 scripts/memory_adaptive.py update --id MEM_ID --feedback helpful
    python3 scripts/memory_adaptive.py decay --days 30
    python3 scripts/memory_adaptive.py recover --id MEM_ID
    python3 scripts/memory_adaptive.py stats
"""

import argparse
import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
CONFIDENCE_FILE = MEMORY_DIR / "adaptive_confidence.json"

# 参数
DECAY_HALF_LIFE = 30  # 衰减半衰期（天）
RECOVERY_RATE = 0.1   # 每次正向反馈恢复量
DECAY_RATE = 0.05     # 每次负向反馈衰减量
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 1.0
CONFIRMATION_THRESHOLD = 2  # 连续 N 次正向反馈才提升置信度


class AdaptiveConfidence:
    """自适应置信度管理"""
    
    def __init__(self):
        self.confidence_data = self._load_confidence()
    
    def _load_confidence(self) -> Dict:
        """加载置信度数据"""
        if CONFIDENCE_FILE.exists():
            with open(CONFIDENCE_FILE) as f:
                return json.load(f)
        return {
            "memories": {},  # mem_id -> confidence_info
            "global_stats": {
                "total_adjustments": 0,
                "avg_confidence": 0.5
            }
        }
    
    def save(self):
        """保存置信度数据"""
        CONFIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIDENCE_FILE, 'w') as f:
            json.dump(self.confidence_data, f, indent=2)
    
    def get_confidence(self, mem_id: str) -> float:
        """获取记忆的置信度"""
        if mem_id in self.confidence_data["memories"]:
            return self.confidence_data["memories"][mem_id].get("confidence", 0.5)
        return 0.5  # 默认中等置信度
    
    def initialize(self, mem_id: str, initial_confidence: float = 0.5):
        """初始化记忆的置信度"""
        if mem_id not in self.confidence_data["memories"]:
            self.confidence_data["memories"][mem_id] = {
                "confidence": initial_confidence,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "feedback_history": [],
                "consecutive_positive": 0,
                "decay_events": 0,
                "recovery_events": 0
            }
            self.save()
    
    def apply_feedback(self, mem_id: str, feedback_type: str, reason: str = ""):
        """应用反馈调整置信度"""
        self.initialize(mem_id)
        
        data = self.confidence_data["memories"][mem_id]
        current = data["confidence"]
        
        # 记录反馈
        feedback_entry = {
            "type": feedback_type,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "before": current
        }
        
        adjustment = 0.0
        
        if feedback_type == "helpful":
            # 正向反馈：连续 N 次才提升
            data["consecutive_positive"] = data.get("consecutive_positive", 0) + 1
            
            if data["consecutive_positive"] >= CONFIRMATION_THRESHOLD:
                adjustment = RECOVERY_RATE
                data["recovery_events"] = data.get("recovery_events", 0) + 1
        
        elif feedback_type == "irrelevant":
            # 无关：轻微衰减
            adjustment = -DECAY_RATE * 0.5
            data["consecutive_positive"] = 0
            data["decay_events"] = data.get("decay_events", 0) + 1
        
        elif feedback_type == "wrong":
            # 错误：较大衰减
            adjustment = -DECAY_RATE
            data["consecutive_positive"] = 0
            data["decay_events"] = data.get("decay_events", 0) + 1
        
        elif feedback_type == "outdated":
            # 过时：标记为需要更新
            adjustment = -DECAY_RATE * 0.3
            data["consecutive_positive"] = 0
        
        # 应用调整
        new_confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, current + adjustment))
        data["confidence"] = new_confidence
        data["last_updated"] = datetime.now().isoformat()
        
        feedback_entry["after"] = new_confidence
        feedback_entry["adjustment"] = adjustment
        data["feedback_history"].append(feedback_entry)
        
        # 保留最近 50 条反馈
        if len(data["feedback_history"]) > 50:
            data["feedback_history"] = data["feedback_history"][-50:]
        
        # 更新全局统计
        self.confidence_data["global_stats"]["total_adjustments"] += 1
        
        self.save()
        
        return {
            "mem_id": mem_id,
            "before": current,
            "after": new_confidence,
            "adjustment": adjustment,
            "feedback_type": feedback_type
        }
    
    def apply_time_decay(self, days: int = 30):
        """应用时间衰减"""
        cutoff = datetime.now() - timedelta(days=days)
        
        results = []
        
        for mem_id, data in self.confidence_data["memories"].items():
            # 检查最后更新时间
            try:
                last_updated = datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
            except:
                last_updated = datetime.now()
            
            if last_updated < cutoff:
                # 应用指数衰减
                days_since = (datetime.now() - last_updated).days
                decay_factor = math.exp(-days_since * math.log(2) / DECAY_HALF_LIFE)
                
                current = data["confidence"]
                new_confidence = max(MIN_CONFIDENCE, current * decay_factor)
                
                if new_confidence < current:
                    data["confidence"] = new_confidence
                    data["last_updated"] = datetime.now().isoformat()
                    data["decay_events"] = data.get("decay_events", 0) + 1
                    
                    results.append({
                        "mem_id": mem_id,
                        "before": current,
                        "after": new_confidence,
                        "days_since": days_since
                    })
        
        self.save()
        return results
    
    def force_recovery(self, mem_id: str, amount: float = 0.2):
        """强制恢复置信度（手动验证后）"""
        self.initialize(mem_id)
        
        data = self.confidence_data["memories"][mem_id]
        current = data["confidence"]
        new_confidence = min(MAX_CONFIDENCE, current + amount)
        
        data["confidence"] = new_confidence
        data["last_updated"] = datetime.now().isoformat()
        data["recovery_events"] = data.get("recovery_events", 0) + 1
        data["feedback_history"].append({
            "type": "manual_recovery",
            "timestamp": datetime.now().isoformat(),
            "before": current,
            "after": new_confidence,
            "adjustment": amount
        })
        
        self.save()
        
        return {
            "mem_id": mem_id,
            "before": current,
            "after": new_confidence
        }
    
    def get_low_confidence_memories(self, threshold: float = 0.3) -> List[Dict]:
        """获取低置信度记忆"""
        results = []
        
        for mem_id, data in self.confidence_data["memories"].items():
            if data["confidence"] < threshold:
                results.append({
                    "mem_id": mem_id,
                    "confidence": data["confidence"],
                    "decay_events": data.get("decay_events", 0),
                    "last_updated": data.get("last_updated", "")
                })
        
        return sorted(results, key=lambda x: x["confidence"])
    
    def get_statistics(self) -> Dict:
        """获取置信度统计"""
        if not self.confidence_data["memories"]:
            return {"total": 0, "avg": 0, "distribution": {}}
        
        confidences = [d["confidence"] for d in self.confidence_data["memories"].values()]
        
        # 分布
        distribution = {
            "high (>0.7)": len([c for c in confidences if c > 0.7]),
            "medium (0.3-0.7)": len([c for c in confidences if 0.3 <= c <= 0.7]),
            "low (<0.3)": len([c for c in confidences if c < 0.3])
        }
        
        return {
            "total": len(confidences),
            "avg": sum(confidences) / len(confidences),
            "min": min(confidences),
            "max": max(confidences),
            "distribution": distribution,
            "total_adjustments": self.confidence_data["global_stats"]["total_adjustments"]
        }
    
    def sync_with_memories(self):
        """与记忆数据库同步"""
        try:
            import lancedb
            db = lancedb.connect(str(VECTOR_DB_DIR))
            table = db.open_table("memories")
            df = table.to_lance().to_table().to_pydict()
            
            mem_ids = df.get("id", [])
            importances = df.get("importance", [0.5] * len(mem_ids))
            
            # 初始化未跟踪的记忆
            for i, mem_id in enumerate(mem_ids):
                if mem_id not in self.confidence_data["memories"]:
                    initial = importances[i] if i < len(importances) else 0.5
                    self.initialize(mem_id, initial)
            
            # 清理已删除的记忆
            existing_ids = set(mem_ids)
            tracked_ids = set(self.confidence_data["memories"].keys())
            
            for removed_id in tracked_ids - existing_ids:
                del self.confidence_data["memories"][removed_id]
            
            self.save()
            
            return {
                "total_tracked": len(self.confidence_data["memories"]),
                "new_initialized": len(existing_ids - tracked_ids),
                "removed": len(tracked_ids - existing_ids)
            }
        
        except Exception as e:
            return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Memory Adaptive Confidence v1.0")
    parser.add_argument("command", choices=["update", "decay", "recover", "stats", "sync", "low"])
    parser.add_argument("--id", "-i", help="记忆 ID")
    parser.add_argument("--feedback", "-f", choices=["helpful", "irrelevant", "wrong", "outdated"], help="反馈类型")
    parser.add_argument("--days", "-d", type=int, default=30, help="衰减天数")
    parser.add_argument("--amount", "-a", type=float, default=0.2, help="恢复量")
    parser.add_argument("--threshold", "-t", type=float, default=0.3, help="阈值")
    parser.add_argument("--reason", "-r", default="", help="原因")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    adaptive = AdaptiveConfidence()
    
    if args.command == "update":
        if not args.id or not args.feedback:
            print("❌ 请提供 --id 和 --feedback")
            return
        
        result = adaptive.apply_feedback(args.id, args.feedback, args.reason)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📊 置信度更新: {result['before']:.3f} → {result['after']:.3f}")
            print(f"   调整: {result['adjustment']:+.3f}")
            print(f"   反馈: {args.feedback}")
    
    elif args.command == "decay":
        results = adaptive.apply_time_decay(args.days)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"⏳ 应用时间衰减 ({args.days} 天未更新)")
            print(f"   影响 {len(results)} 条记忆")
            for r in results[:5]:
                print(f"   - {r['mem_id'][:8]}...: {r['before']:.3f} → {r['after']:.3f}")
    
    elif args.command == "recover":
        if not args.id:
            print("❌ 请提供 --id")
            return
        
        result = adaptive.force_recovery(args.id, args.amount)
        
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📈 置信度恢复: {result['before']:.3f} → {result['after']:.3f}")
    
    elif args.command == "stats":
        stats = adaptive.get_statistics()
        
        if args.json:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        else:
            print("📊 置信度统计")
            print(f"   总记忆: {stats['total']}")
            print(f"   平均: {stats['avg']:.3f}")
            print(f"   范围: {stats['min']:.3f} - {stats['max']:.3f}")
            print(f"   分布:")
            for k, v in stats['distribution'].items():
                print(f"     {k}: {v}")
            print(f"   总调整次数: {stats['total_adjustments']}")
    
    elif args.command == "sync":
        print("🔄 同步置信度数据")
        result = adaptive.sync_with_memories()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.command == "low":
        print(f"⚠️ 低置信度记忆 (阈值 < {args.threshold})")
        results = adaptive.get_low_confidence_memories(args.threshold)
        
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            for r in results[:10]:
                print(f"   {r['mem_id'][:8]}... 置信度: {r['confidence']:.3f}")


if __name__ == "__main__":
    main()
