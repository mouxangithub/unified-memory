#!/usr/bin/env python3
"""
Unified Memory CLI - 统一命令行入口

整合所有功能:
- 记忆管理（存储、搜索、导出）
- 系统维护（健康检查、修复、清理）
- 项目生成（FastAPI、React、CLI）
- 可视化（Web UI、工作流）
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def cmd_init(args):
    """初始化记忆系统"""
    print("🚀 初始化记忆系统...")
    
    # 创建目录
    memory_dir = Path.home() / ".openclaw" / "workspace" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "vector").mkdir(exist_ok=True)
    (memory_dir / "cache").mkdir(exist_ok=True)
    (memory_dir / "recovery").mkdir(exist_ok=True)
    
    # 创建标准向量表
    try:
        from maintenance.vector_repair import VectorTableRepair
        repair = VectorTableRepair()
        repair.create_standard_table("memories")
        print("✅ 向量表初始化成功")
    except Exception as e:
        print(f"⚠️ 向量表初始化失败: {e}")
    
    # 初始化健康状态
    health_file = memory_dir / "health.json"
    health_file.write_text('{"vector": {"healthy": true}, "bm25": {"healthy": true}, "cache": {"healthy": true}}')
    
    print("✅ 初始化完成")


def cmd_store(args):
    """存储记忆"""
    print(f"💾 存储记忆: {args.text[:50]}...")
    
    try:
        from agent_memory import AgentMemory
        memory = AgentMemory()
        memory.store(args.text, tags=args.tags.split(",") if args.tags else None)
        print("✅ 存储成功")
    except Exception as e:
        print(f"❌ 存储失败: {e}")


def cmd_search(args):
    """搜索记忆"""
    print(f"🔍 搜索: {args.query}")
    
    try:
        from resilience.error_fallback import ErrorFallback
        fallback = ErrorFallback()
        result = fallback.search_with_fallback(args.query, limit=args.limit)
        
        if result.success:
            print(f"✅ 找到 {len(result.data)} 条结果 ({result.level})")
            for i, item in enumerate(result.data[:5], 1):
                print(f"\n{i}. {item.get('text', item)[:100]}...")
        else:
            print(f"❌ 搜索失败: {result.error}")
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


def cmd_health(args):
    """健康检查"""
    print("🏥 健康检查...\n")
    
    # 记忆系统
    try:
        from agent_memory import AgentMemory
        memory = AgentMemory()
        status = memory.status()
        print("📊 记忆系统:")
        print(f"  总记忆: {status.get('total_memories', 0)} 条")
        print(f"  向量数: {status.get('vectors', 0)} 个")
        print(f"  LLM: {status.get('llm_status', 'unknown')}")
    except Exception as e:
        print(f"❌ 记忆系统检查失败: {e}")
    
    # 向量表
    print("\n📊 向量表:")
    try:
        from maintenance.vector_repair import health_check
        health_check()
    except:
        print("  ⚠️ 向量表检查跳过")
    
    # 降级状态
    print("\n📊 降级状态:")
    try:
        from resilience.error_fallback import ErrorFallback
        fallback = ErrorFallback()
        report = fallback.get_health_report()
        for component, status in report["health"].items():
            emoji = "✅" if status["healthy"] else "❌"
            print(f"  {emoji} {component}")
        print(f"  缓存数量: {report['cache_count']}")
    except:
        print("  ⚠️ 降级状态检查跳过")


def cmd_repair(args):
    """修复系统"""
    print("🔧 修复系统...\n")
    
    if args.vector:
        try:
            from maintenance.vector_repair import VectorTableRepair
            repair = VectorTableRepair()
            result = repair.repair_all()
            print(f"✅ 修复完成: {result['repaired']}/{result['total']}")
        except Exception as e:
            print(f"❌ 向量修复失败: {e}")
    
    if args.cache:
        try:
            from resilience.error_fallback import ErrorFallback
            fallback = ErrorFallback()
            fallback.clear_cache()
        except Exception as e:
            print(f"❌ 缓存清理失败: {e}")


def cmd_scaffold(args):
    """生成项目脚手架"""
    print(f"🏗️ 创建 {args.type} 项目: {args.name}")
    
    try:
        from scaffold.project_scaffold import ProjectScaffold
        scaffold = ProjectScaffold(args.output)
        
        if args.type == "fastapi":
            scaffold.create_fastapi(args.name, args.desc)
        elif args.type == "flask":
            scaffold.create_flask(args.name, args.desc)
        elif args.type == "react":
            scaffold.create_react(args.name, args.desc)
        elif args.type == "cli":
            scaffold.create_cli(args.name, args.desc)
        
        print(f"\n✅ 项目已创建: {args.output}/{args.name}")
    except Exception as e:
        print(f"❌ 项目创建失败: {e}")


def cmd_serve(args):
    """启动 Web 服务"""
    port = args.port
    
    print(f"🌐 启动 Web 服务: http://localhost:{port}")
    print("按 Ctrl+C 停止\n")
    
    try:
        import uvicorn
        
        # 检查是否有完整 API
        api_file = Path(__file__).parent.parent / "memory_server.py"
        if api_file.exists():
            uvicorn.run("memory_server:app", host="0.0.0.0", port=port, reload=args.reload)
        else:
            # 简易服务器
            from http.server import HTTPServer, SimpleHTTPRequestHandler
            import os
            
            os.chdir(Path(__file__).parent.parent / "web")
            server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
            server.serve_forever()
    
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请安装: pip install fastapi uvicorn")


def cmd_export(args):
    """导出记忆"""
    print(f"📤 导出记忆到: {args.output}")
    
    try:
        from memory_export import MemoryExporter
        exporter = MemoryExporter()
        exporter.export(args.output, format=args.format)
        print("✅ 导出成功")
    except Exception as e:
        print(f"❌ 导出失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="统一记忆系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  mem init                    # 初始化
  mem store "重要内容"         # 存储
  mem search "查询关键词"      # 搜索
  mem health                  # 健康检查
  mem repair --vector         # 修复向量表
  mem scaffold fastapi my-api # 创建项目
  mem serve --port 38080      # 启动 Web
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # init
    subparsers.add_parser("init", help="初始化记忆系统")
    
    # store
    store_parser = subparsers.add_parser("store", help="存储记忆")
    store_parser.add_argument("text", help="记忆内容")
    store_parser.add_argument("--tags", "-t", help="标签（逗号分隔）")
    
    # search
    search_parser = subparsers.add_parser("search", help="搜索记忆")
    search_parser.add_argument("query", help="查询内容")
    search_parser.add_argument("--limit", "-l", type=int, default=10, help="结果数量")
    
    # health
    subparsers.add_parser("health", help="健康检查")
    
    # repair
    repair_parser = subparsers.add_parser("repair", help="修复系统")
    repair_parser.add_argument("--vector", action="store_true", help="修复向量表")
    repair_parser.add_argument("--cache", action="store_true", help="清除缓存")
    
    # scaffold
    scaffold_parser = subparsers.add_parser("scaffold", help="生成项目脚手架")
    scaffold_parser.add_argument("type", choices=["fastapi", "flask", "react", "cli"], help="项目类型")
    scaffold_parser.add_argument("name", help="项目名称")
    scaffold_parser.add_argument("--desc", "-d", default="", help="项目描述")
    scaffold_parser.add_argument("--output", "-o", default=".", help="输出目录")
    
    # serve
    serve_parser = subparsers.add_parser("serve", help="启动 Web 服务")
    serve_parser.add_argument("--port", "-p", type=int, default=38080, help="端口")
    serve_parser.add_argument("--reload", "-r", action="store_true", help="热重载")
    
    # export
    export_parser = subparsers.add_parser("export", help="导出记忆")
    export_parser.add_argument("output", help="输出文件")
    export_parser.add_argument("--format", "-f", choices=["json", "csv", "md"], default="json", help="格式")
    
    args = parser.parse_args()
    
    # 路由命令
    if args.command == "init":
        cmd_init(args)
    elif args.command == "store":
        cmd_store(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "health":
        cmd_health(args)
    elif args.command == "repair":
        cmd_repair(args)
    elif args.command == "scaffold":
        cmd_scaffold(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
