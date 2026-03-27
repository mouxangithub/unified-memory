# 🧠 统一记忆系统 (unified-memory)

跨 Agent 的长期记忆系统，支持 RAG、混合搜索、知识图谱。

## 功能

- 🔍 混合搜索 (BM25 + Vector + Rerank)
- 🏊 多级记忆池 (核心/工作/上下文/归档)
- 💬 多智能体共享
- 🔒 隐私计算
- 📊 监控分析
- 🌐 知识图谱

## 安装

```bash
# 安装依赖（可选功能）
pip install lancedb sentence-transformers pytest

# 或一键安装
pip install -r requirements.txt
```

## 使用

```bash
# 搜索记忆
python scripts/memory_all_in_one.py search "查询内容"

# 存储记忆
python scripts/memory_all_in_one.py store "记忆内容"

# 运行测试
python scripts/memory_benchmark.py
```

## 架构

- `memory_all_in_one.py` - 统一入口
- `memory_bm25.py` - BM25 搜索
- `memory_pool.py` - 记忆池
- `memory_sqlite.py` - SQLite 存储
- `memory_rerank_full.py` - Rerank
- `memory_benchmark.py` - 性能测试
