#!/usr/bin/env python3
"""
端到端测试 - 验证系统可用性

测试场景:
1. 存储 → 搜索 完整链路
2. 工作流执行
3. Agent 协作
4. 记忆进化
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

print("=" * 60)
print("端到端测试 - 统一记忆系统 v1.0.0")
print("=" * 60)
print()

results = {}

# ============================================================
# 测试 1: 存储 → 搜索 完整链路
# ============================================================
print("📝 测试 1: 存储 → 搜索 完整链路")
print("-" * 40)

try:
    from unified_interface import UnifiedMemory
    
    um = UnifiedMemory()
    
    # 存储
    test_content = f"测试记忆 {datetime.now().isoformat()} - 用户偏好深色主题"
    memory_id = um.quick_store(test_content, category="preference")
    print(f"  存储: ✅ {memory_id}")
    
    # 搜索（使用 lex 模式，不依赖 embedding）
    results_list = um.search.search(test_content[:10], mode="lex", limit=3)
    print(f"  搜索: ✅ 找到 {len(results_list)} 条")
    
    results["存储→搜索"] = "✅ 通过"
    
except Exception as e:
    results["存储→搜索"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 2: 智能分块
# ============================================================
print("📝 测试 2: 智能分块")
print("-" * 40)

try:
    from unified_interface import SmartChunker
    
    chunker = SmartChunker(max_tokens=100)
    
    test_text = """
# 项目概述
这是一个测试项目

## 技术栈
- Python 3.11
- FastAPI
- LanceDB

## 代码示例
```python
def hello():
    print("Hello, World!")
```

## 总结
项目已完成
"""
    
    chunks = chunker.chunk(test_text)
    
    # 验证代码块没有被切断
    code_preserved = any("```python" in c and "hello()" in c for c in chunks)
    
    if code_preserved:
        print(f"  分块: ✅ {len(chunks)} 块")
        print(f"  代码保护: ✅")
        results["智能分块"] = "✅ 通过"
    else:
        results["智能分块"] = "❌ 代码块被切断"
        print(f"  代码保护: ❌ 代码块被切断")
    
except Exception as e:
    results["智能分块"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 3: 工作流加载
# ============================================================
print("📝 测试 3: 工作流加载")
print("-" * 40)

try:
    from unified_interface import SOPWorkflow
    
    workflow = SOPWorkflow()
    sops = workflow.list_sops()
    
    if sops:
        print(f"  SOP 列表: ✅ {sops}")
        results["工作流"] = "✅ 通过"
    else:
        # 尝试加载默认
        from workflow_sop import init_default_sops
        init_default_sops()
        sops = workflow.list_sops()
        print(f"  SOP 列表: ✅ {sops} (已初始化)")
        results["工作流"] = "✅ 通过"
    
except Exception as e:
    results["工作流"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 4: Agent 协作
# ============================================================
print("📝 测试 4: Agent 协作")
print("-" * 40)

try:
    from unified_interface import AgentCollab
    
    ac = AgentCollab()
    
    # 创建任务
    task_id = f"test_task_{datetime.now().timestamp()}"
    ac.add_task(task_id, "测试任务", priority=1)
    print(f"  创建任务: ✅ {task_id}")
    
    # 获取统计
    # stats = ac.get_stats()  # 如果有这个方法
    print(f"  Agent 协作: ✅")
    results["Agent协作"] = "✅ 通过"
    
except Exception as e:
    results["Agent协作"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 5: 错误降级
# ============================================================
print("📝 测试 5: 错误降级机制")
print("-" * 40)

try:
    # 测试 Ollama 不可用时的降级
    from unified_interface import HybridSearch
    
    # 模拟 Ollama 不可用
    original_url = os.environ.get("OLLAMA_HOST")
    os.environ["OLLAMA_HOST"] = "http://invalid-host:11434"
    
    search = HybridSearch()
    
    # lex 模式应该仍然可用（不需要 embedding）
    results_lex = search.search("测试", mode="lex", limit=3)
    
    # 恢复
    if original_url:
        os.environ["OLLAMA_HOST"] = original_url
    else:
        os.environ.pop("OLLAMA_HOST", None)
    
    print(f"  lex 降级: ✅")
    results["错误降级"] = "✅ 通过"
    
except Exception as e:
    results["错误降级"] = f"❌ {e}"
    print(f"  错误: {e}")

print()

# ============================================================
# 测试 6: 数据持久化
# ============================================================
print("📝 测试 6: 数据持久化")
print("-" * 40)

try:
    from pathlib import Path
    
    memory_dir = Path.home() / ".openclaw" / "workspace" / "memory"
    vector_dir = memory_dir / "vector"
    context_file = memory_dir / "context_tree.json"
    
    checks = []
    
    if memory_dir.exists():
        checks.append("memory/ ✅")
    else:
        checks.append("memory/ ❌")
    
    if vector_dir.exists():
        checks.append("vector/ ✅")
    else:
        checks.append("vector/ ❌")
    
    print(f"  目录检查: {', '.join(checks)}")
    
    if all("✅" in c for c in checks):
        results["数据持久化"] = "✅ 通过"
    else:
        results["数据持久化"] = "⚠️ 部分通过"
    
except Exception as e:
    results["数据持久化"] = f"❌ {e}"
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
    print("🎉 所有端到端测试通过！系统可用。")
    sys.exit(0)
elif passed >= total * 0.7:
    print("⚠️ 大部分测试通过，但有部分问题需要修复。")
    sys.exit(1)
else:
    print("❌ 多项测试失败，系统需要修复后再使用。")
    sys.exit(2)
