#!/usr/bin/env python3
"""
CLI 优化 - Enhanced CLI Interface

更友好的命令行体验
"""

import argparse
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))


def cmd_search(args):
    """搜索命令"""
    from memory_all_in_one import search_memories
    
    results = search_memories(args.query, args.limit)
    
    if not results:
        print(f"🔍 未找到关于 '{args.query}' 的记忆")
        return
    
    print(f"\n🔍 搜索 '{args.query}' ({len(results)} 条结果)\n")
    
    for i, r in enumerate(results, 1):
        text = r.get("text", "")[:80]
        score = r.get("score", r.get("hybrid_score", 0))
        category = r.get("category", "unknown")
        
        print(f"  {i}. [{category}] {text}...")
        print(f"     相似度: {score:.2%}\n")


def cmd_store(args):
    """存储命令"""
    from memory_all_in_one import store_memory
    
    memory = {
        "text": args.text,
        "category": args.category or "general",
        "importance": args.importance or 0.5
    }
    
    success = store_memory(memory)
    
    if success:
        print(f"✅ 已存储: {args.text[:50]}...")
    else:
        print("❌ 存储失败")


def cmd_stats(args):
    """统计命令"""
    from memory_all_in_one import get_memory_stats
    
    stats = get_memory_stats()
    
    print("\n📊 记忆系统统计\n")
    print(f"  总记忆数: {stats.get('total', 0)}")
    
    if "by_category" in stats:
        print("\n  分类统计:")
        for cat, count in stats["by_category"].items():
            print(f"    {cat}: {count}")


def cmd_health(args):
    """健康检查命令"""
    from memory_all_in_one import health_check
    
    health = health_check()
    
    print("\n🏥 记忆系统健康检查\n")
    print(f"  健康度: {health.get('score', 0)}/100")
    print(f"  总记忆: {health.get('total', 0)}")
    
    if "issues" in health:
        print("\n  问题:")
        for issue, count in health["issues"].items():
            if count > 0:
                print(f"    {issue}: {count}")


def cmd_graph(args):
    """知识图谱命令"""
    from memory_all_in_one import visualize_knowledge_graph
    
    output = args.output or "knowledge_graph.html"
    visualize_knowledge_graph(output_path=output)
    
    print(f"✅ 知识图谱已生成: {output}")


def cmd_cache(args):
    """缓存命令"""
    from memory_cache import get_cache
    
    cache = get_cache()
    stats = cache.stats()
    
    print("\n💾 缓存状态\n")
    
    if "lru" in stats:
        print(f"  LRU 缓存:")
        print(f"    大小: {stats['lru']['size']}/{stats['lru']['max_size']}")
    
    if "sqlite" in stats:
        print(f"  SQLite 缓存:")
        print(f"    条目: {stats['sqlite']['total_entries']}")
        print(f"    命中率: {stats['sqlite']['hit_rate']:.1%}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="🧠 统一记忆系统 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s search "用户偏好"
  %(prog)s store "新记忆" --category preference
  %(prog)s stats
  %(prog)s health
  %(prog)s graph
  %(prog)s cache
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 搜索
    search_parser = subparsers.add_parser("search", help="搜索记忆")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("--limit", "-n", type=int, default=10, help="返回数量")
    
    # 存储
    store_parser = subparsers.add_parser("store", help="存储记忆")
    store_parser.add_argument("text", help="记忆内容")
    store_parser.add_argument("--category", "-c", help="分类")
    store_parser.add_argument("--importance", "-i", type=float, help="重要性 (0-1)")
    
    # 统计
    subparsers.add_parser("stats", help="查看统计")
    
    # 健康检查
    subparsers.add_parser("health", help="健康检查")
    
    # 知识图谱
    graph_parser = subparsers.add_parser("graph", help="生成知识图谱")
    graph_parser.add_argument("--output", "-o", help="输出文件")
    
    # 缓存
    subparsers.add_parser("cache", help="查看缓存状态")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    commands = {
        "search": cmd_search,
        "store": cmd_store,
        "stats": cmd_stats,
        "health": cmd_health,
        "graph": cmd_graph,
        "cache": cmd_cache,
    }
    
    cmd = commands.get(args.command)
    if cmd:
        try:
            cmd(args)
        except Exception as e:
            print(f"❌ 错误: {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
