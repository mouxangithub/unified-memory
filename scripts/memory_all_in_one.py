#!/usr/bin/env python3
"""
Memory All-in-One - 统一功能入口 v0.1.0

整合所有记忆系统功能的单一入口：
- 搜索 (QMD风格)
- 存储
- 关联
- 去重
- 衰减
- 健康
- 洞察
- 提醒
- 导出
- 图谱
- QA
- 统计
- 模板

Usage:
    mem search "查询内容"
    mem store "记忆内容" --category preference
    mem health
    mem insights
    mem export
    mem graph
    mem qa "问题"
    mem stats
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DB_DIR = MEMORY_DIR / "vector"

# 脚本目录
SCRIPTS_DIR = Path(__file__).parent


def cmd_search(args):
    """搜索记忆"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_qmd_search.py"),
         "search", "-q", args.query,
         "-m", args.mode,
         "-k", str(args.top_k),
         "--json"],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        print(f"🔍 找到 {len(data.get('results', []))} 条记忆\n")
        
        for i, r in enumerate(data.get("results", [])[:args.top_k], 1):
            score = r.get("score", 0)
            text = r.get("text", "")[:80]
            category = r.get("category", "?")
            mode = r.get("mode", "?")
            
            print(f"[{i}] 📊 {score:.3f} | {category} | {mode}")
            print(f"    {text}...")
            print()
    else:
        print(f"❌ 搜索失败: {result.stderr}")


def cmd_store(args):
    """存储记忆"""
    import subprocess
    
    cmd = ["python3", str(SCRIPTS_DIR / "memory.py"),
           "store", "--text", args.text]
    
    if args.category:
        cmd.extend(["--category", args.category])
    if args.importance:
        cmd.extend(["--importance", str(args.importance)])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ 记忆已存储")
        print(result.stdout)
    else:
        print(f"❌ 存储失败: {result.stderr}")


def cmd_health(args):
    """健康检查"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_health.py"), "report"],
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_insights(args):
    """用户洞察"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_insights.py"), "analyze"],
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_export(args):
    """导出记忆"""
    import subprocess
    
    output = args.output or f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_export.py"),
         "--format", args.format, "--output", output],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print(f"✅ 已导出到: {output}")
    else:
        print(f"❌ 导出失败: {result.stderr}")


def cmd_graph(args):
    """知识图谱"""
    import subprocess
    
    if args.html:
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "memory_graph.py"), "--html", args.output or "memory_graph.html"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"✅ 图谱已生成: {args.output or 'memory_graph.html'}")
        else:
            print(f"❌ 生成失败: {result.stderr}")
    else:
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "memory_graph.py"), "--json"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"📊 知识图谱")
            print(f"   节点: {len(data.get('nodes', {}))}")
            print(f"   边: {len(data.get('edges', {}))}")


def cmd_qa(args):
    """问答"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_qa.py"), "ask", "-q", args.question],
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_stats(args):
    """使用统计"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_usage_stats.py")],
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_associate(args):
    """建立关联"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_association.py"), "build-graph"],
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_dedup(args):
    """去重"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_dedup.py")] + (["--apply"] if args.apply else []),
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_decay(args):
    """衰减"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_decay.py")] + (["--apply"] if args.apply else ["--dry-run"]),
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_reminder(args):
    """提醒"""
    import subprocess
    
    if args.action == "check":
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "memory_reminder.py"), "check"],
            capture_output=True, text=True
        )
        print(result.stdout)
    elif args.action == "add":
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "memory_reminder.py"), "add",
             "--content", args.content, "--date", args.date],
            capture_output=True, text=True
        )
        print(result.stdout)


def cmd_template(args):
    """模板"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_templates.py"), "list"],
        capture_output=True, text=True
    )
    print(result.stdout)


def cmd_mcp(args):
    """启动 MCP 服务器"""
    import subprocess
    print("🚀 启动 MCP 服务器...")
    subprocess.run(["python3", str(SCRIPTS_DIR / "memory_mcp_server.py")])


def main():
    parser = argparse.ArgumentParser(
        description="Memory All-in-One - 统一记忆管理",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # search
    p_search = subparsers.add_parser("search", help="搜索记忆")
    p_search.add_argument("query", help="搜索内容")
    p_search.add_argument("-m", "--mode", default="hybrid", choices=["bm25", "vector", "hybrid"])
    p_search.add_argument("-k", "--top-k", type=int, default=5)
    p_search.set_defaults(func=cmd_search)
    
    # store
    p_store = subparsers.add_parser("store", help="存储记忆")
    p_store.add_argument("text", help="记忆内容")
    p_store.add_argument("-c", "--category", choices=["preference", "fact", "decision", "entity", "learning", "other"])
    p_store.add_argument("-i", "--importance", type=float)
    p_store.set_defaults(func=cmd_store)
    
    # health
    p_health = subparsers.add_parser("health", help="健康检查")
    p_health.set_defaults(func=cmd_health)
    
    # insights
    p_insights = subparsers.add_parser("insights", help="用户洞察")
    p_insights.set_defaults(func=cmd_insights)
    
    # export
    p_export = subparsers.add_parser("export", help="导出记忆")
    p_export.add_argument("-f", "--format", default="json", choices=["json", "markdown", "csv"])
    p_export.add_argument("-o", "--output")
    p_export.set_defaults(func=cmd_export)
    
    # graph
    p_graph = subparsers.add_parser("graph", help="知识图谱")
    p_graph.add_argument("--html", action="store_true", help="生成 HTML 可视化")
    p_graph.add_argument("-o", "--output")
    p_graph.set_defaults(func=cmd_graph)
    
    # qa
    p_qa = subparsers.add_parser("qa", help="问答")
    p_qa.add_argument("question", help="问题")
    p_qa.set_defaults(func=cmd_qa)
    
    # stats
    p_stats = subparsers.add_parser("stats", help="使用统计")
    p_stats.set_defaults(func=cmd_stats)
    
    # associate
    p_assoc = subparsers.add_parser("associate", help="建立关联")
    p_assoc.set_defaults(func=cmd_associate)
    
    # dedup
    p_dedup = subparsers.add_parser("dedup", help="去重检测")
    p_dedup.add_argument("--apply", action="store_true", help="应用去重")
    p_dedup.set_defaults(func=cmd_dedup)
    
    # decay
    p_decay = subparsers.add_parser("decay", help="置信度衰减")
    p_decay.add_argument("--apply", action="store_true", help="应用衰减")
    p_decay.set_defaults(func=cmd_decay)
    
    # reminder
    p_reminder = subparsers.add_parser("reminder", help="提醒管理")
    p_reminder.add_argument("action", choices=["check", "add"])
    p_reminder.add_argument("--content")
    p_reminder.add_argument("--date")
    p_reminder.set_defaults(func=cmd_reminder)
    
    # template
    p_template = subparsers.add_parser("template", help="记忆模板")
    p_template.set_defaults(func=cmd_template)
    
    # mcp
    p_mcp = subparsers.add_parser("mcp", help="启动 MCP 服务器")
    p_mcp.set_defaults(func=cmd_mcp)
    
    args = parser.parse_args()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
