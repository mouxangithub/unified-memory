#!/usr/bin/env python3
"""
Memory Usage Stats - 功能使用统计 v1.0

统计记忆系统各功能的使用情况，帮助识别哪些功能被用到，哪些被忽略。
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import subprocess

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
LOG_FILE = MEMORY_DIR / "integration.log"

# 功能列表
FEATURES = {
    "core": ["memory.py", "memory_integration.py"],
    "search": ["memory.py", "smart_search.py", "concurrent_search.py"],
    "health": ["memory_health.py", "conflict_resolver.py"],
    "optimize": ["memory_optimize.py", "performance_dashboard.py"],
    "multimodal": ["memory_multimodal.py"],
    "cloud": ["memory_cloud.py"],
    "graph": ["memory_graph.py"],
    "qa": ["memory_qa.py"],
    "api": ["memory_api.py"],
    "webui": ["memory_webui.py"],
    "adaptive": ["memory_adaptive.py"],
    "privacy": ["memory_privacy.py"],
    "insights": ["memory_insights.py"],
    "perf": ["memory_perf.py"],
}


def analyze_logs():
    """分析日志文件"""
    if not LOG_FILE.exists():
        return {"error": "日志文件不存在"}
    
    stats = {
        "total_entries": 0,
        "by_date": defaultdict(int),
        "by_action": defaultdict(int),
        "errors": [],
        "warnings": [],
    }
    
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                stats["total_entries"] += 1
                
                # 提取日期
                if line.startswith("["):
                    date_str = line[1:11]  # [2026-03-19
                    stats["by_date"][date_str] += 1
                
                # 统计动作
                if "心跳" in line:
                    stats["by_action"]["heartbeat"] += 1
                elif "会话开始" in line:
                    stats["by_action"]["session_start"] += 1
                elif "会话结束" in line:
                    stats["by_action"]["session_end"] += 1
                elif "存储记忆" in line:
                    stats["by_action"]["store"] += 1
                
                # 统计错误和警告
                if "❌" in line or "ERROR" in line.upper():
                    stats["errors"].append(line)
                elif "⚠️" in line or "WARN" in line.upper():
                    stats["warnings"].append(line)
        
        # 只保留最近10条错误和警告
        stats["errors"] = stats["errors"][-10:]
        stats["warnings"] = stats["warnings"][-10:]
        
        return stats
    
    except Exception as e:
        return {"error": str(e)}


def check_feature_usage():
    """检查功能使用情况"""
    scripts_dir = WORKSPACE / "skills/unified-memory/scripts"
    usage = {}
    
    for feature, scripts in FEATURES.items():
        usage[feature] = {
            "scripts": scripts,
            "exists": all((scripts_dir / s).exists() for s in scripts),
            "last_modified": None,
        }
        
        # 获取最后修改时间
        if usage[feature]["exists"]:
            mtimes = [(scripts_dir / s).stat().st_mtime for s in scripts]
            latest_mtime = max(mtimes)
            usage[feature]["last_modified"] = datetime.fromtimestamp(latest_mtime).isoformat()
    
    return usage


def analyze_memory_db():
    """分析记忆数据库"""
    try:
        result = subprocess.run(
            ["python3", str(WORKSPACE / "skills/unified-memory/scripts/memory.py"), "stats"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            # 提取JSON部分
            lines = result.stdout.strip().split('\n')
            json_start = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('{'):
                    json_start = i
                    break
            
            if json_start >= 0:
                json_str = '\n'.join(lines[json_start:])
                return json.loads(json_str)
        return {"error": "无法获取记忆统计"}
    except Exception as e:
        return {"error": str(e)}


def generate_report():
    """生成使用报告"""
    print("\n" + "="*60)
    print("📊 记忆系统功能使用统计报告")
    print("="*60)
    
    # 1. 日志分析
    print("\n📝 日志分析:")
    log_stats = analyze_logs()
    if "error" not in log_stats:
        print(f"  总日志条目: {log_stats['total_entries']}")
        print(f"  最近7天活动: {sum(v for k, v in log_stats['by_date'].items() if k >= (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))}")
        print(f"  主要动作:")
        for action, count in sorted(log_stats["by_action"].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {action}: {count} 次")
        
        if log_stats["warnings"]:
            print(f"\n  ⚠️ 最近警告: {len(log_stats['warnings'])} 条")
        if log_stats["errors"]:
            print(f"  ❌ 最近错误: {len(log_stats['errors'])} 条")
    else:
        print(f"  错误: {log_stats['error']}")
    
    # 2. 功能使用情况
    print("\n🔧 功能使用情况:")
    feature_usage = check_feature_usage()
    used_features = []
    unused_features = []
    
    for feature, info in feature_usage.items():
        if info["exists"]:
            used_features.append((feature, info["last_modified"]))
        else:
            unused_features.append(feature)
    
    if used_features:
        print("  ✅ 已启用功能:")
        for feature, mtime in sorted(used_features, key=lambda x: x[1] if x[1] else "", reverse=True):
            mtime_str = mtime.split("T")[0] if mtime else "未知"
            print(f"    - {feature}: {mtime_str}")
    
    if unused_features:
        print("  ❌ 未安装功能:")
        for feature in unused_features:
            print(f"    - {feature}")
    
    # 3. 记忆统计
    print("\n📚 记忆统计:")
    mem_stats = analyze_memory_db()
    if "error" not in mem_stats:
        print(f"  总记忆数: {mem_stats.get('total_memories', 0)}")
        if "hierarchy" in mem_stats:
            hierarchy = mem_stats["hierarchy"]
            print(f"  L1 热点记忆: {hierarchy['L1_hot']['count']}")
            print(f"  L2 活跃记忆: {hierarchy['L2_warm']['count']}")
            print(f"  L3 冷存储: {hierarchy['L3_cold']['count']}")
    else:
        print(f"  错误: {mem_stats['error']}")
    
    # 4. 建议
    print("\n💡 优化建议:")
    suggestions = []
    
    if log_stats.get("warnings"):
        suggestions.append("修复警告信息（见上方日志分析）")
    
    if unused_features:
        suggestions.append(f"安装缺失功能: {', '.join(unused_features[:3])}")
    
    if mem_stats.get("hierarchy", {}).get("L1_hot", {}).get("count", 0) == 0:
        suggestions.append("L1热点缓存为空，考虑预热缓存")
    
    if not suggestions:
        suggestions.append("✅ 系统运行良好，无明显问题")
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")
    
    print("\n" + "="*60)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="功能使用统计")
    parser.add_argument("--json", "-j", action="store_true", help="JSON输出")
    
    args = parser.parse_args()
    
    if args.json:
        data = {
            "logs": analyze_logs(),
            "features": check_feature_usage(),
            "memory": analyze_memory_db()
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        generate_report()


if __name__ == "__main__":
    main()
