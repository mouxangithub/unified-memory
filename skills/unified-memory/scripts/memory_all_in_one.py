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
    """搜索记忆 - 修复版 v0.2.0"""
    import subprocess
    result = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "memory_qmd_search.py"),
         "search", "--query", args.query,
         "--mode", args.mode,
         "--top-k", str(args.top_k)],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        # 直接输出结果（不再尝试解析 JSON）
        output = result.stdout.strip()
        if output:
            print(output)
        else:
            print("🔍 未找到相关记忆")
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


def cmd_conflict(args):
    """矛盾记忆检测与解决"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "conflict_resolver.py"), args.action]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_isolated(args):
    """处理孤立记忆"""
    memory_file = MEMORY_DIR / "memories.json"
    memories = json.loads(memory_file.read_text()) if memory_file.exists() else []
    isolated = [m for m in memories if m.get("access_count", 0) == 0]
    
    print(f"🔗 发现 {len(isolated)} 条孤立记忆（从未被访问）\n")
    
    if args.fix and isolated:
        # 自动关联到常用标签
        for m in isolated[:args.limit]:
            m["tags"] = m.get("tags", []) + ["auto-linked"]
            m["access_count"] = 1
            print(f"✅ 已关联: {m.get('text', '')[:50]}...")
        
        memory_file.write_text(json.dumps(memories, indent=2, ensure_ascii=False))
        print(f"\n📊 已处理 {min(len(isolated), args.limit)} 条孤立记忆")
    elif isolated:
        print("待处理的孤立记忆:")
        for i, m in enumerate(isolated[:10], 1):
            print(f"  [{i}] {m.get('text', '')[:60]}...")
        if len(isolated) > 10:
            print(f"  ... 还有 {len(isolated) - 10} 条")
        print(f"\n💡 使用 --fix 自动关联")


def cmd_trace(args):
    """决策追溯链"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_trace.py")]
    
    if args.timeline:
        cmd.extend(["--timeline", "--limit", str(args.limit)])
    elif args.mem_id:
        cmd.append(args.mem_id)
    else:
        cmd.append("--timeline")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_heatmap(args):
    """记忆访问热力图"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_heatmap.py")]
    
    if args.boost:
        cmd.extend(["--boost", "--threshold", str(args.threshold)])
    if args.save:
        cmd.append("--save")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_collab(args):
    """协作效率可视化"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_collab.py"), "--period", str(args.period)]
    
    if args.html:
        cmd.append("--html")
    if args.save:
        cmd.append("--save")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_compress_eval(args):
    """L3压缩质量评估"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_compress_eval.py")]
    
    if args.id:
        cmd.extend(["--id", args.id])
    if args.report:
        cmd.append("--report")
    if args.save:
        cmd.append("--save")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_encrypt(args):
    """敏感信息加密"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_sensitive.py"), "encrypt", "--id", args.id]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_decrypt(args):
    """解密查看"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_sensitive.py"), "decrypt", 
           "--id", args.id, "--agent", args.agent]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_sensitive(args):
    """敏感信息检测"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_sensitive.py"), args.action,
           "--limit", str(args.limit)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_predict(args):
    """记忆预测"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_predict.py"), args.action]
    
    if args.enable_push:
        cmd.append("--enable-push")
    if args.disable_push:
        cmd.append("--disable-push")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def cmd_multimodal(args):
    """多模态记忆"""
    import subprocess
    cmd = ["python3", str(SCRIPTS_DIR / "memory_multimodal.py"), args.action]
    
    if args.feature:
        cmd.extend(["--feature", args.feature])
    if args.image:
        cmd.extend(["--image", args.image])
    if args.audio:
        cmd.extend(["--audio", args.audio])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


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
    
    # conflict
    p_conflict = subparsers.add_parser("conflict", help="矛盾记忆解决")
    p_conflict.add_argument("action", choices=["detect", "auto", "resolve"],
                           help="操作类型")
    p_conflict.set_defaults(func=cmd_conflict)
    
    # isolated
    p_isolated = subparsers.add_parser("isolated", help="处理孤立记忆")
    p_isolated.add_argument("--fix", action="store_true", help="自动修复")
    p_isolated.add_argument("--limit", type=int, default=10, help="处理数量")
    p_isolated.set_defaults(func=cmd_isolated)
    
    # trace
    p_trace = subparsers.add_parser("trace", help="决策追溯链")
    p_trace.add_argument("mem_id", nargs="?", help="记忆ID")
    p_trace.add_argument("--timeline", "-t", action="store_true", help="显示决策时间线")
    p_trace.add_argument("--limit", "-l", type=int, default=10, help="显示数量")
    p_trace.set_defaults(func=cmd_trace)
    
    # heatmap
    p_heatmap = subparsers.add_parser("heatmap", help="记忆访问热力图")
    p_heatmap.add_argument("--boost", "-b", action="store_true", help="自动提升高频记忆权重")
    p_heatmap.add_argument("--threshold", "-t", type=int, default=3, help="提升阈值")
    p_heatmap.add_argument("--save", "-s", action="store_true", help="保存热力图")
    p_heatmap.set_defaults(func=cmd_heatmap)
    
    # collab
    p_collab = subparsers.add_parser("collab", help="协作效率可视化")
    p_collab.add_argument("--html", "-H", action="store_true", help="生成HTML报告")
    p_collab.add_argument("--period", "-p", type=int, default=7, help="统计周期（天）")
    p_collab.add_argument("--save", "-s", action="store_true", help="保存统计")
    p_collab.set_defaults(func=cmd_collab)
    
    # compress-eval
    p_compress = subparsers.add_parser("compress-eval", help="L3压缩质量评估")
    p_compress.add_argument("--id", "-i", help="评估指定记忆ID")
    p_compress.add_argument("--report", "-r", action="store_true", help="生成详细报告")
    p_compress.add_argument("--save", "-s", action="store_true", help="保存评估结果")
    p_compress.set_defaults(func=cmd_compress_eval)
    
    # encrypt (敏感信息加密)
    p_encrypt = subparsers.add_parser("encrypt", help="敏感信息加密")
    p_encrypt.add_argument("--id", "-i", required=True, help="记忆ID")
    p_encrypt.set_defaults(func=cmd_encrypt)
    
    # decrypt (解密查看)
    p_decrypt = subparsers.add_parser("decrypt", help="解密查看")
    p_decrypt.add_argument("--id", "-i", required=True, help="记忆ID")
    p_decrypt.add_argument("--agent", "-a", default="unknown", help="Agent名称")
    p_decrypt.set_defaults(func=cmd_decrypt)
    
    # sensitive (敏感信息检测)
    p_sensitive = subparsers.add_parser("sensitive", help="敏感信息检测")
    p_sensitive.add_argument("action", choices=["detect", "scan", "audit"], help="操作")
    p_sensitive.add_argument("--limit", "-l", type=int, default=20, help="显示数量")
    p_sensitive.set_defaults(func=cmd_sensitive)
    
    # predict (记忆预测)
    p_predict = subparsers.add_parser("predict", help="记忆预测")
    p_predict.add_argument("action", choices=["today", "week", "train", "config"], help="操作")
    p_predict.add_argument("--enable-push", action="store_true", help="启用推送")
    p_predict.add_argument("--disable-push", action="store_true", help="禁用推送")
    p_predict.set_defaults(func=cmd_predict)
    
    # multimodal (多模态记忆)
    p_multimodal = subparsers.add_parser("multimodal", help="多模态记忆")
    p_multimodal.add_argument("action", choices=["config", "enable", "disable", "check", "store"], help="操作")
    p_multimodal.add_argument("--feature", choices=["ocr", "stt", "clip"], help="功能名称")
    p_multimodal.add_argument("--image", "-i", help="图片路径")
    p_multimodal.add_argument("--audio", "-a", help="音频路径")
    p_multimodal.set_defaults(func=cmd_multimodal)
    
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
