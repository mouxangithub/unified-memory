#!/usr/bin/env python3
"""
Memory System v2 Patch - P1/P2 修复

P1: 访问追踪 + 置信度衰减
P2: 统一数据源 + Schema 版本控制 + 健康检查增强
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"
MEMORY_FILE = MEMORY_DIR / "memories.json"
SCHEMA_VERSION = "1.1"

# 向量数据库
try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    HAS_LANCEDB = False


class AccessTracker:
    """P1: 访问追踪"""
    
    def __init__(self):
        self.db_path = VECTOR_DB_DIR
        
    def track_access(self, memory_ids: List[str]) -> Dict:
        """
        更新访问追踪字段
        
        Args:
            memory_ids: 被访问的记忆ID列表
        
        Returns:
            更新统计
        """
        if not HAS_LANCEDB:
            return {"error": "LanceDB not available"}
        
        updated = 0
        now = datetime.now().isoformat()
        
        try:
            conn = lancedb.connect(str(self.db_path))
            table = conn.open_table("memories")
            df = table.to_arrow()
            
            # 构建更新后的数据
            new_rows = []
            for i in range(df.num_rows):
                row = {col: df[col][i].as_py() for col in df.column_names}
                
                if row['id'] in memory_ids:
                    row['access_count'] = (row.get('access_count') or 0) + 1
                    row['last_accessed'] = now
                    updated += 1
                
                new_rows.append(row)
            
            # 重建表
            conn.drop_table('memories')
            import pyarrow as pa
            
            schema = pa.schema([
                ('id', pa.string()),
                ('text', pa.string()),
                ('category', pa.string()),
                ('scope', pa.string()),
                ('importance', pa.float64()),
                ('timestamp', pa.string()),
                ('vector', pa.list_(pa.float32())),
                ('access_count', pa.int64()),
                ('last_accessed', pa.string()),
                ('confidence', pa.float64()),
                ('tags', pa.string()),
                ('source', pa.string()),
                ('metadata', pa.string()),
            ])
            
            new_table = conn.create_table('memories', schema=schema)
            new_table.add(new_rows)
            
            return {"updated": updated, "timestamp": now}
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_hot_memories(self, threshold: int = 5) -> List[Dict]:
        """获取高频访问记忆"""
        if not HAS_LANCEDB:
            return []
        
        try:
            conn = lancedb.connect(str(self.db_path))
            table = conn.open_table("memories")
            df = table.to_arrow()
            
            hot = []
            for i in range(df.num_rows):
                access_count = df['access_count'][i].as_py() or 0
                if access_count >= threshold:
                    hot.append({
                        'id': df['id'][i].as_py(),
                        'text': df['text'][i].as_py()[:50],
                        'access_count': access_count,
                        'last_accessed': df['last_accessed'][i].as_py(),
                    })
            
            return sorted(hot, key=lambda x: x['access_count'], reverse=True)
            
        except Exception as e:
            print(f"获取热记忆失败: {e}", file=sys.stderr)
            return []


class ConfidenceDecay:
    """P1: 置信度衰减"""
    
    HALF_LIFE_DAYS = 30  # 30天半衰期
    
    def __init__(self):
        self.db_path = VECTOR_DB_DIR
    
    def calculate_decay(self, timestamp: str, initial_confidence: float = 0.5) -> float:
        """
        计算衰减后的置信度
        
        Args:
            timestamp: 记忆创建时间
            initial_confidence: 初始置信度
        
        Returns:
            衰减后的置信度
        """
        try:
            created = datetime.fromisoformat(timestamp.replace(' ', 'T'))
            age_days = (datetime.now() - created).days
            
            # 指数衰减: conf * 0.5^(age/half_life)
            decay_factor = math.pow(0.5, age_days / self.HALF_LIFE_DAYS)
            return initial_confidence * decay_factor
            
        except Exception:
            return initial_confidence
    
    def apply_decay(self) -> Dict:
        """应用置信度衰减到所有记忆"""
        if not HAS_LANCEDB:
            return {"error": "LanceDB not available"}
        
        try:
            conn = lancedb.connect(str(self.db_path))
            table = conn.open_table("memories")
            df = table.to_arrow()
            
            updated = 0
            new_rows = []
            
            for i in range(df.num_rows):
                row = {col: df[col][i].as_py() for col in df.column_names}
                
                # 计算衰减
                old_conf = row.get('confidence') or 0.5
                new_conf = self.calculate_decay(row['timestamp'], old_conf)
                
                if abs(new_conf - old_conf) > 0.01:  # 只更新有明显变化的
                    row['confidence'] = round(new_conf, 3)
                    updated += 1
                
                new_rows.append(row)
            
            # 重建表
            conn.drop_table('memories')
            import pyarrow as pa
            
            schema = pa.schema([
                ('id', pa.string()),
                ('text', pa.string()),
                ('category', pa.string()),
                ('scope', pa.string()),
                ('importance', pa.float64()),
                ('timestamp', pa.string()),
                ('vector', pa.list_(pa.float32())),
                ('access_count', pa.int64()),
                ('last_accessed', pa.string()),
                ('confidence', pa.float64()),
                ('tags', pa.string()),
                ('source', pa.string()),
                ('metadata', pa.string()),
            ])
            
            new_table = conn.create_table('memories', schema=schema)
            new_table.add(new_rows)
            
            return {"updated": updated, "half_life_days": self.HALF_LIFE_DAYS}
            
        except Exception as e:
            return {"error": str(e)}


class UnifiedStats:
    """P2: 统一数据源"""
    
    def __init__(self):
        self.db_path = VECTOR_DB_DIR
    
    def get_all_stats(self) -> Dict:
        """统一获取所有统计"""
        if not HAS_LANCEDB:
            return {"error": "LanceDB not available"}
        
        try:
            conn = lancedb.connect(str(self.db_path))
            table = conn.open_table("memories")
            df = table.to_arrow()
            
            total = df.num_rows
            
            # 分类统计
            categories = {}
            for i in range(total):
                cat = df['category'][i].as_py() or 'unknown'
                categories[cat] = categories.get(cat, 0) + 1
            
            # 访问统计
            access_counts = [df['access_count'][i].as_py() or 0 for i in range(total)]
            never_accessed = sum(1 for c in access_counts if c == 0)
            hot_count = sum(1 for c in access_counts if c >= 5)
            
            # 置信度统计
            confidences = [df['confidence'][i].as_py() or 0.5 for i in range(total)]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # 时间统计
            timestamps = [df['timestamp'][i].as_py() for i in range(total)]
            timestamps = [t for t in timestamps if t]
            latest = max(timestamps) if timestamps else None
            oldest = min(timestamps) if timestamps else None
            
            return {
                "total": total,
                "categories": categories,
                "access": {
                    "never_accessed": never_accessed,
                    "hot_count": hot_count,
                    "total_accesses": sum(access_counts),
                },
                "confidence": {
                    "average": round(avg_confidence, 3),
                    "min": min(confidences),
                    "max": max(confidences),
                },
                "time": {
                    "latest": latest,
                    "oldest": oldest,
                },
                "schema_version": SCHEMA_VERSION,
            }
            
        except Exception as e:
            return {"error": str(e)}


class SchemaManager:
    """P2: Schema 版本控制"""
    
    REQUIRED_COLUMNS = {
        "1.0": ['id', 'text', 'category', 'scope', 'importance', 'timestamp', 'vector'],
        "1.1": ['id', 'text', 'category', 'scope', 'importance', 'timestamp', 'vector',
                'access_count', 'last_accessed', 'confidence', 'tags', 'source', 'metadata'],
    }
    
    CURRENT_VERSION = SCHEMA_VERSION
    
    def __init__(self):
        self.db_path = VECTOR_DB_DIR
    
    def check_schema(self) -> Dict:
        """检查当前 schema 版本"""
        if not HAS_LANCEDB:
            return {"error": "LanceDB not available"}
        
        try:
            conn = lancedb.connect(str(self.db_path))
            table = conn.open_table("memories")
            df = table.to_arrow()
            
            current_columns = set(df.column_names)
            
            # 检查各版本
            versions = {}
            for ver, required in self.REQUIRED_COLUMNS.items():
                required_set = set(required)
                if required_set.issubset(current_columns):
                    versions[ver] = "✅"
                else:
                    missing = required_set - current_columns
                    versions[ver] = f"❌ 缺少: {missing}"
            
            # 确定当前版本
            detected_version = None
            for ver in sorted(self.REQUIRED_COLUMNS.keys(), reverse=True):
                if versions[ver] == "✅":
                    detected_version = ver
                    break
            
            return {
                "detected_version": detected_version,
                "current_columns": list(current_columns),
                "version_status": versions,
                "needs_upgrade": detected_version != self.CURRENT_VERSION,
            }
            
        except Exception as e:
            return {"error": str(e)}


class HealthCheck:
    """P2: 健康检查增强"""
    
    def __init__(self):
        self.db_path = VECTOR_DB_DIR
        self.stats = UnifiedStats()
        self.schema = SchemaManager()
    
    def full_check(self, fix: bool = False) -> Dict:
        """完整健康检查"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues": [],
            "fixed": [],
        }
        
        # 1. Schema 检查
        schema_result = self.schema.check_schema()
        results["checks"]["schema"] = schema_result
        
        if schema_result.get("needs_upgrade"):
            results["issues"].append("Schema 需要升级")
        
        # 2. 统计检查
        stats_result = self.stats.get_all_stats()
        results["checks"]["stats"] = stats_result
        
        if stats_result.get("access", {}).get("never_accessed", 0) > 0:
            count = stats_result["access"]["never_accessed"]
            results["issues"].append(f"{count} 条记忆从未被访问")
        
        # 3. 置信度检查
        if stats_result.get("confidence", {}).get("average", 0) == 0:
            results["issues"].append("置信度统计异常")
        
        # 4. 数据完整性
        total = stats_result.get("total", 0)
        if total == 0:
            results["issues"].append("数据库为空")
        
        # 计算健康分数
        issue_count = len(results["issues"])
        health_score = max(0, 100 - issue_count * 20)
        results["health_score"] = health_score
        
        return results
    
    def fix_issues(self) -> Dict:
        """自动修复问题"""
        # 这个会在 P0 迁移后调用
        return {"message": "请先运行 P0 迁移脚本"}


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory System v2 Patch")
    parser.add_argument("action", choices=[
        "track", "decay", "stats", "schema", "health", "all"
    ])
    parser.add_argument("--ids", nargs="+", help="记忆ID列表 (track)")
    parser.add_argument("--fix", action="store_true", help="自动修复")
    
    args = parser.parse_args()
    
    if args.action == "track":
        if not args.ids:
            print("❌ 请提供 --ids 参数")
            sys.exit(1)
        tracker = AccessTracker()
        result = tracker.track_access(args.ids)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == "decay":
        decay = ConfidenceDecay()
        result = decay.apply_decay()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == "stats":
        stats = UnifiedStats()
        result = stats.get_all_stats()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == "schema":
        schema = SchemaManager()
        result = schema.check_schema()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == "health":
        health = HealthCheck()
        result = health.full_check(fix=args.fix)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.action == "all":
        print("=== Schema 检查 ===")
        schema = SchemaManager()
        print(json.dumps(schema.check_schema(), indent=2, ensure_ascii=False))
        
        print("\n=== 统一统计 ===")
        stats = UnifiedStats()
        print(json.dumps(stats.get_all_stats(), indent=2, ensure_ascii=False))
        
        print("\n=== 健康检查 ===")
        health = HealthCheck()
        print(json.dumps(health.full_check(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
