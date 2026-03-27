#!/usr/bin/env python3
"""
Memory Quality - 记忆质量指标 v0.0.7

功能:
- 记忆质量评分
- 可视化报告生成
- 健康度检查

Usage:
    memory_quality.py report              # 生成质量报告
    memory_quality.py health              # 健康度检查
    memory_quality.py metrics             # 详细指标
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False


class MemoryQuality:
    """记忆质量指标"""
    
    def __init__(self):
        self.memories = self._load_memories()
    
    def _load_memories(self) -> List[Dict]:
        """加载记忆"""
        memories = []
        
        if HAS_LANCEDB:
            try:
                db = lancedb.connect(str(VECTOR_DB_DIR))
                table = db.open_table("memories")
                result = table.to_lance().to_table().to_pydict()
                
                if result:
                    count = len(result.get("id", []))
                    for i in range(count):
                        mem = {col: result[col][i] for col in result.keys() if len(result[col]) > i}
                        memories.append(mem)
            except Exception as e:
                print(f"⚠️ 加载失败: {e}")
        
        return memories
    
    def calculate_accuracy(self) -> float:
        """准确率 = 已验证记忆占比"""
        validation_file = MEMORY_DIR / "validation" / "validation_state.json"
        
        if validation_file.exists():
            try:
                validation_state = json.loads(validation_file.read_text())
                verified = sum(1 for v in validation_state.values() if "✅ 已验证" in v.get("confidence", ""))
                return verified / len(self.memories) if self.memories else 0
            except:
                pass
        
        # 默认所有记忆都是准确的
        return 1.0
    
    def calculate_timeliness(self) -> float:
        """时效性 = 最近30天记忆占比"""
        if not self.memories:
            return 0
        
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        recent_count = 0
        for mem in self.memories:
            created_at = mem.get("created_at") or mem.get("timestamp")
            if created_at:
                try:
                    if "T" in created_at:
                        mem_time = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    else:
                        mem_time = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    
                    if mem_time > thirty_days_ago:
                        recent_count += 1
                except:
                    pass
        
        return recent_count / len(self.memories)
    
    def calculate_utilization(self) -> float:
        """利用率 = 被访问记忆占比"""
        feedback_file = MEMORY_DIR / "feedback" / "feedback_log.jsonl"
        
        if feedback_file.exists():
            try:
                accessed_ids = set()
                for line in feedback_file.read_text().strip().split("\n"):
                    if line:
                        feedback = json.loads(line)
                        accessed_ids.add(feedback.get("memory_id"))
                
                return len(accessed_ids) / len(self.memories) if self.memories else 0
            except:
                pass
        
        # 默认假设都被访问过
        return 1.0
    
    def calculate_redundancy(self) -> float:
        """冗余率 = 重复记忆占比"""
        seen_texts = set()
        duplicates = 0
        
        for mem in self.memories:
            text_key = mem.get("text", "")[:50].lower()
            if text_key in seen_texts:
                duplicates += 1
            seen_texts.add(text_key)
        
        return duplicates / len(self.memories) if self.memories else 0
    
    def calculate_coverage(self) -> Dict[str, float]:
        """分类覆盖率"""
        categories = Counter(mem.get("category", "other") for mem in self.memories)
        total = len(self.memories)
        
        return {
            cat: count / total if total > 0 else 0
            for cat, count in categories.items()
        }
    
    def generate_report(self) -> Dict:
        """生成质量报告"""
        accuracy = self.calculate_accuracy()
        timeliness = self.calculate_timeliness()
        utilization = self.calculate_utilization()
        redundancy = self.calculate_redundancy()
        coverage = self.calculate_coverage()
        
        # 综合健康分
        health_score = (
            accuracy * 0.3 +
            timeliness * 0.25 +
            utilization * 0.25 +
            (1 - redundancy) * 0.2
        )
        
        # 评级
        if health_score >= 0.9:
            rating = "🟢 优秀"
        elif health_score >= 0.7:
            rating = "🟡 良好"
        elif health_score >= 0.5:
            rating = "🟠 一般"
        else:
            rating = "🔴 需改进"
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_memories": len(self.memories),
            "metrics": {
                "accuracy": round(accuracy * 100, 1),
                "timeliness": round(timeliness * 100, 1),
                "utilization": round(utilization * 100, 1),
                "redundancy": round(redundancy * 100, 1)
            },
            "health_score": round(health_score * 100, 1),
            "rating": rating,
            "coverage": {k: round(v * 100, 1) for k, v in coverage.items()},
            "recommendations": self._generate_recommendations(
                accuracy, timeliness, utilization, redundancy
            )
        }
    
    def _generate_recommendations(self, accuracy, timeliness, utilization, redundancy):
        """生成优化建议"""
        recommendations = []
        
        if accuracy < 0.8:
            recommendations.append({
                "priority": "high",
                "issue": "准确率较低",
                "action": "运行 memory.py validate 验证记忆"
            })
        
        if timeliness < 0.7:
            recommendations.append({
                "priority": "medium",
                "issue": "时效性不足",
                "action": "清理过时记忆，更新重要信息"
            })
        
        if utilization < 0.5:
            recommendations.append({
                "priority": "medium",
                "issue": "利用率低",
                "action": "优化记忆检索，提高相关性"
            })
        
        if redundancy > 0.2:
            recommendations.append({
                "priority": "high",
                "issue": "冗余率高",
                "action": "运行 memory.py merge 合并重复记忆"
            })
        
        return recommendations
    
    def health_check(self) -> Dict:
        """健康度检查"""
        issues = []
        
        # 检查记忆数量
        if len(self.memories) == 0:
            issues.append({"level": "error", "message": "没有记忆数据"})
        elif len(self.memories) > 1000:
            issues.append({"level": "warning", "message": f"记忆数量过多 ({len(self.memories)})，建议归档"})
        
        # 检查向量数据库
        if not HAS_LANCEDB:
            issues.append({"level": "warning", "message": "LanceDB 未安装，向量搜索不可用"})
        
        # 检查目录结构
        required_dirs = ["hierarchy", "knowledge_blocks", "validation", "feedback", "archive"]
        for dir_name in required_dirs:
            dir_path = MEMORY_DIR / dir_name
            if not dir_path.exists():
                issues.append({"level": "info", "message": f"目录不存在: {dir_name}"})
        
        return {
            "status": "error" if any(i["level"] == "error" for i in issues) else
                      "warning" if any(i["level"] == "warning" for i in issues) else
                      "healthy",
            "issues": issues
        }


def main():
    parser = argparse.ArgumentParser(description="Memory Quality 0.0.7")
    parser.add_argument("command", choices=["report", "health", "metrics"])
    
    args = parser.parse_args()
    
    quality = MemoryQuality()
    
    if args.command == "report":
        report = quality.generate_report()
        
        print("📊 记忆质量报告")
        print("=" * 50)
        print(f"总记忆: {report['total_memories']} 条")
        print(f"健康分: {report['health_score']}% {report['rating']}")
        print()
        print("指标:")
        print(f"  准确率: {report['metrics']['accuracy']}%")
        print(f"  时效性: {report['metrics']['timeliness']}%")
        print(f"  利用率: {report['metrics']['utilization']}%")
        print(f"  冗余率: {report['metrics']['redundancy']}%")
        print()
        
        if report['coverage']:
            print("分类覆盖:")
            for cat, pct in report['coverage'].items():
                print(f"  {cat}: {pct}%")
        
        if report['recommendations']:
            print()
            print("优化建议:")
            for rec in report['recommendations']:
                print(f"  [{rec['priority']}] {rec['issue']}: {rec['action']}")
    
    elif args.command == "health":
        health = quality.health_check()
        
        print("🏥 健康度检查")
        print("=" * 50)
        print(f"状态: {health['status'].upper()}")
        
        if health['issues']:
            print()
            print("问题:")
            for issue in health['issues']:
                print(f"  [{issue['level']}] {issue['message']}")
        else:
            print("✅ 无问题")
    
    elif args.command == "metrics":
        print(json.dumps({
            "accuracy": quality.calculate_accuracy(),
            "timeliness": quality.calculate_timeliness(),
            "utilization": quality.calculate_utilization(),
            "redundancy": quality.calculate_redundancy(),
            "coverage": quality.calculate_coverage()
        }, indent=2))


if __name__ == "__main__":
    main()
