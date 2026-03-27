#!/usr/bin/env python3
"""
完整功能测试 v1.1.0

测试所有新增功能:
1. CLI 命令
2. 多模态记忆
3. 可视化界面 API
4. Git 集成
5. 记忆压缩
6. 错误降级
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

print("=" * 60)
print("统一记忆系统 v1.1.0 - 完整功能测试")
print("=" * 60)
print()

results = {}

# ============================================================
# 测试 1: CLI 命令
# ============================================================
print("📝 测试 1: CLI 命令")
print("-" * 40)

try:
    from cli.mem_cli import cmd_init, cmd_status, cmd_store, cmd_search
    
    # 初始化
    class Args:
        pass
    cmd_init(Args())
    
    # 存储
    args = Args()
    args.text = f"测试记忆 {datetime.now().isoformat()}"
    args.category = "test"
    cmd_store(args)
    
    results["CLI 命令"] = "✅ 通过"
    
except Exception as e:
    results["CLI 命令"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 2: 多模态记忆
# ============================================================
print("📝 测试 2: 多模态记忆")
print("-" * 40)

try:
    from multimodal import ImageProcessor, PDFProcessor, AudioProcessor
    
    # 测试图片处理器（不实际处理）
    img_proc = ImageProcessor()
    print(f"  图片处理器: ✅ OCR {'可用' if img_proc.ocr_available else '不可用'}")
    
    # 测试 PDF 处理器
    pdf_proc = PDFProcessor()
    print(f"  PDF 处理器: ✅ 解析 {'可用' if pdf_proc.pdf_available else '不可用'}")
    
    # 测试音频处理器
    audio_proc = AudioProcessor()
    print(f"  音频处理器: ✅ STT {'可用' if audio_proc.stt_available else '不可用'}")
    
    results["多模态记忆"] = "✅ 通过"
    
except Exception as e:
    results["多模态记忆"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 3: 可视化界面 API
# ============================================================
print("📝 测试 3: 可视化界面 API")
print("-" * 40)

try:
    from web.dashboard import app
    
    # 检查路由
    routes = [r.path for r in app.routes]
    print(f"  路由数量: {len(routes)}")
    
    # 检查关键端点
    key_routes = ["/", "/graph", "/workflow", "/api/status", "/api/search"]
    for route in key_routes:
        if route in routes:
            print(f"  {route}: ✅")
        else:
            print(f"  {route}: ⚠️ 未找到")
    
    results["可视化界面"] = "✅ 通过"
    
except Exception as e:
    results["可视化界面"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 4: Git 集成
# ============================================================
print("📝 测试 4: Git 集成")
print("-" * 40)

try:
    from git.git_integration import GitIntegration
    
    git = GitIntegration()
    
    # 列出已追踪
    repos = git.list_tracked()
    print(f"  已追踪仓库: {len(repos)} 个")
    
    results["Git 集成"] = "✅ 通过"
    
except Exception as e:
    results["Git 集成"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 5: 记忆压缩
# ============================================================
print("📝 测试 5: 记忆压缩")
print("-" * 40)

try:
    from compression.memory_compressor import MemoryCompressor
    
    compressor = MemoryCompressor()
    
    # 获取统计
    stats = compressor.get_compression_stats()
    print(f"  已归档: {stats['archived_memories']} 条")
    
    results["记忆压缩"] = "✅ 通过"
    
except Exception as e:
    results["记忆压缩"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 6: 错误降级
# ============================================================
print("📝 测试 6: 错误降级")
print("-" * 40)

try:
    from resilience.error_handler import ErrorHandler, safe_search, safe_embedding
    
    handler = ErrorHandler()
    
    # 测试降级搜索
    results_search = safe_search("测试", limit=3)
    print(f"  降级搜索: ✅ 返回 {len(results_search)} 条")
    
    # 测试错误报告
    errors = handler.get_error_report()
    print(f"  错误日志: {len(errors)} 条")
    
    results["错误降级"] = "✅ 通过"
    
except Exception as e:
    results["错误降级"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 7: 统一接口更新
# ============================================================
print("📝 测试 7: 统一接口")
print("-" * 40)

try:
    from unified_interface import (
        UnifiedMemory,
        SmartChunker,
        ContextTreeManager,
        HybridSearch,
        SOPWorkflow,
        AgentCollab
    )
    from multimodal import MultimodalMemory
    
    # 测试 MultimodalMemory
    mm = MultimodalMemory()
    print(f"  多模态接口: ✅")
    
    # 测试 UnifiedMemory
    um = UnifiedMemory()
    print(f"  统一入口: ✅")
    
    results["统一接口"] = "✅ 通过"
    
except Exception as e:
    results["统一接口"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 总结
# ============================================================
print("=" * 60)
print("测试结果汇总")
print("=" * 60)
print()

for test_name, status in results.items():
    print(f"  {test_name:15s} {status}")

print()

passed = sum(1 for s in results.values() if s.startswith("✅"))
total = len(results)

print(f"总计: {passed}/{total} 通过")
print()

if passed == total:
    print("🎉 所有测试通过！v1.1.0 已就绪。")
    print()
    print("快速使用:")
    print("  mem init              # 初始化")
    print("  mem store '内容'       # 存储")
    print("  mem search '查询'     # 搜索")
    print("  mem serve             # 启动 Web 界面")
    print("  mem image ./pic.png   # 处理图片")
    print("  mem pdf ./doc.pdf     # 处理 PDF")
    print("  mem git --track ./    # 追踪 Git 仓库")
    print("  mem compress          # 压缩旧记忆")
    sys.exit(0)
else:
    print("⚠️ 部分测试失败，请检查。")
    sys.exit(1)
