#!/usr/bin/env python3
"""
Memory Optimization - 记忆系统优化集成 v1.0

集成三大优化:
1. 矛盾记忆自动解决 ⚡
2. 检索智能提示 💡
3. 性能可视化 📈

使用:
    memory_optimize.py run         # 运行所有优化
    memory_optimize.py check       # 检查系统状态
    memory_optimize.py report      # 生成优化报告
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# 添加脚本目录
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from conflict_resolver import ConflictResolver
from smart_search import SmartSearch
from performance_dashboard import PerformanceDashboard


class MemoryOptimizer:
    """记忆系统优化器"""
    
    def __init__(self):
        self.conflict_resolver = ConflictResolver()
        self.smart_searcher = SmartSearch()
        self.dashboard = PerformanceDashboard()
    
    def run_all_optimizations(self) -> Dict:
        """运行所有优化"""
        print("\n🚀 开始运行记忆系统优化...\n")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "optimizations": {}
        }
        
        # 优化一：矛盾记忆自动解决
        print("⚡ 优化一：矛盾记忆自动解决")
        print("-" * 50)
        try:
            conflict_results = self.conflict_resolver.auto_resolve_all()
            results["optimizations"]["conflict_resolution"] = conflict_results
            print(f"  ✅ 完成: 自动解决 {conflict_results['auto_resolved']} 个")
            print(f"  📋 需确认: {conflict_results['need_confirmation']} 个")
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results["optimizations"]["conflict_resolution"] = {"error": str(e)}
        
        # 优化二：检索智能提示
        print("\n💡 优化二：检索智能提示")
        print("-" * 50)
        try:
            # 收集当前上下文的推荐
            recommendations = self.smart_searcher.recommend(top_k=5)
            trending = self.smart_searcher.get_trending_keywords(5)
            
            results["optimizations"]["smart_search"] = {
                "recommendations": len(recommendations),
                "trending_keywords": trending
            }
            print(f"  ✅ 完成: 生成 {len(recommendations)} 条推荐")
            print(f"  🔥 热门关键词: {', '.join([kw['keyword'] for kw in trending[:3]])}")
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results["optimizations"]["smart_search"] = {"error": str(e)}
        
        # 优化三：性能可视化
        print("\n📈 优化三：性能可视化")
        print("-" * 50)
        try:
            metrics = self.dashboard.collect_metrics()
            trends = self.dashboard.get_trends(days=7)
            
            results["optimizations"]["performance"] = {
                "health_score": metrics["health"].get("health_score", 0),
                "total_memories": metrics["memory_stats"].get("total_count", 0),
                "search_latency_ms": metrics["performance"].get("search_latency_ms", 0),
                "alerts": len(metrics["alerts"])
            }
            print(f"  ✅ 完成: 健康评分 {metrics['health'].get('health_score', 0):.1f}/100")
            print(f"  ⚠️  告警: {len(metrics['alerts'])} 个")
        except Exception as e:
            print(f"  ❌ 失败: {e}")
            results["optimizations"]["performance"] = {"error": str(e)}
        
        print("\n" + "="*50)
        print("✅ 所有优化完成！")
        print("="*50 + "\n")
        
        return results
    
    def check_system_status(self) -> Dict:
        """检查系统状态"""
        print("\n🔍 检查记忆系统状态...\n")
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # 检查矛盾解决器
        try:
            conflict_stats = self.conflict_resolver.get_stats()
            status["components"]["conflict_resolver"] = {
                "status": "✅ 正常",
                "total_conflicts": conflict_stats.get("total_conflicts", 0),
                "pending": conflict_stats.get("pending", 0)
            }
        except Exception as e:
            status["components"]["conflict_resolver"] = {
                "status": "❌ 异常",
                "error": str(e)
            }
        
        # 检查智能搜索
        try:
            search_stats = self.smart_searcher.get_stats()
            status["components"]["smart_search"] = {
                "status": "✅ 正常",
                "total_searches": search_stats.get("total_searches", 0),
                "recommendations": search_stats.get("total_recommendations", 0)
            }
        except Exception as e:
            status["components"]["smart_search"] = {
                "status": "❌ 异常",
                "error": str(e)
            }
        
        # 检查性能仪表板
        try:
            metrics = self.dashboard.collect_metrics()
            status["components"]["dashboard"] = {
                "status": "✅ 正常",
                "health_score": metrics["health"].get("health_score", 0),
                "alerts": len(metrics["alerts"])
            }
        except Exception as e:
            status["components"]["dashboard"] = {
                "status": "❌ 异常",
                "error": str(e)
            }
        
        # 显示状态
        print("组件状态:")
        for name, info in status["components"].items():
            print(f"  {info['status']} {name}")
            if "error" not in info:
                for key, value in info.items():
                    if key != "status":
                        print(f"      {key}: {value}")
        
        print("\n" + "="*50 + "\n")
        
        return status
    
    def generate_report(self) -> str:
        """生成优化报告"""
        print("\n📊 生成优化报告...\n")
        
        # 收集数据
        conflict_stats = self.conflict_resolver.get_stats()
        search_stats = self.smart_searcher.get_stats()
        metrics = self.dashboard.collect_metrics()
        trends = self.dashboard.get_trends(days=7)
        
        # 生成报告
        report = f"""
# 记忆系统优化报告

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 系统概览

- **总记忆数**: {metrics['memory_stats'].get('total_count', 0)}
- **健康评分**: {metrics['health'].get('health_score', 0):.1f}/100
- **存储大小**: {metrics['performance'].get('total_storage_mb', 0):.2f}MB

## ⚡ 矛盾解决

- **总矛盾数**: {conflict_stats.get('total_conflicts', 0)}
- **待处理**: {conflict_stats.get('pending', 0)}
- **已解决**: {conflict_stats.get('resolved', 0)}

### 解决策略分布

- 自动合并: {conflict_stats.get('by_strategy', {}).get('auto_merge', 0)} 个
- 建议合并: {conflict_stats.get('by_strategy', {}).get('suggest_merge', 0)} 个
- 标记矛盾: {conflict_stats.get('by_strategy', {}).get('mark_conflict', 0)} 个

## 💡 智能检索

- **总搜索次数**: {search_stats.get('total_searches', 0)}
- **推荐记忆数**: {search_stats.get('total_recommendations', 0)}

### 热门关键词

"""
        
        trending = search_stats.get('trending_keywords', [])
        for i, kw in enumerate(trending[:5], 1):
            report += f"{i}. {kw['keyword']} ({kw['count']} 次)\n"
        
        report += f"""
## 📈 性能趋势（最近7天）

- **记忆数量**: {trends.get('memory_count', {}).get('avg', 0):.0f} (平均)
- **搜索延迟**: {trends.get('search_latency', {}).get('avg_ms', 0):.1f}ms (平均)
- **健康评分**: {trends.get('health_score', {}).get('avg', 0):.1f} (平均)

## ⚠️ 系统告警

"""
        
        alerts = metrics.get('alerts', [])
        if alerts:
            for alert in alerts:
                report += f"- [{alert['level']}] {alert['message']}\n"
        else:
            report += "✅ 无告警\n"
        
        report += """
---

**优化建议**:

"""
        
        # 生成优化建议
        if conflict_stats.get('pending', 0) > 0:
            report += "1. 运行 `memory_optimize.py run` 自动解决矛盾记忆\n"
        
        if metrics['health'].get('conflict_rate', 0) > 0.1:
            report += "2. 矛盾率过高，建议手动确认矛盾记忆\n"
        
        if metrics['performance'].get('total_storage_mb', 0) > 50:
            report += "3. 存储空间较大，建议运行 `memory.py forget` 清理过时记忆\n"
        
        return report


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="记忆系统优化集成")
    parser.add_argument("command", choices=["run", "check", "report"])
    
    args = parser.parse_args()
    
    optimizer = MemoryOptimizer()
    
    if args.command == "run":
        results = optimizer.run_all_optimizations()
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif args.command == "check":
        status = optimizer.check_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.command == "report":
        report = optimizer.generate_report()
        print(report)
        
        # 保存报告
        report_file = Path.home() / ".openclaw" / "workspace" / "memory" / "OPTIMIZATION_REPORT.md"
        report_file.write_text(report)
        print(f"\n✅ 报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
