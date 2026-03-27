# unified-memory - 统一记忆系统 v2.0.0

> 零依赖 AI Agent 框架，集成记忆、搜索、协作、工作流自动化

---

## 核心特性

### 对标 QMD

- ✅ **Context Tree** - 项目级上下文管理
- ✅ **智能摘要** - 压缩历史，提取精华
- ✅ **混合搜索** - BM25 + 向量 + RRF

### 对标 MetaGPT

- ✅ **项目模板** - 快速启动
- ✅ **多 Agent 协作** - 智能调度
- ✅ **工作流 SOP** - YAML 定义

### 独有优势

- ✅ **多模态** - OCR/STT（独有）
- ✅ **智能分类** - 自动打标签（独有）
- ✅ **零依赖** - 开箱即用（独有）

---

## 快速开始

```bash
# 安装
git clone https://github.com/mouxangithub/unified-memory.git

# 初始化项目
mem template create software-project ./my-app

# 存储记忆
mem store "重要决策" --tags "架构"

# 搜索记忆
mem search "架构"

# 更新上下文
mem ctx update "任务" --progress 50

# 压缩历史
mem summary compress --days 7
```

---

## 核心命令

```bash
# Context Tree
mem ctx init/update/decision/status/export

# 智能摘要
mem summary compress/decisions/summary

# 项目模板
mem template list/create

# 系统管理
mem health
mem validate
```

---

## 对比优势

| 维度 | 我们 | QMD | MetaGPT |
|------|------|-----|---------|
| 依赖数量 | 0 ✅ | ~5 | 70+ |
| Context Tree | ✅ | ✅ | ⚠️ |
| 智能摘要 | ✅ | ✅ | ❌ |
| 多模态 | ✅ 独有 | ❌ | ⚠️ |
| 零依赖 | ✅ 独有 | ❌ | ❌ |

---

## 文档

- [快速开始](docs/QUICK_START.md)
- [真实案例](docs/REAL_CASES.md)
- [变更日志](CHANGELOG_v2.md)
- [路线图](docs/ROADMAP_v1.1.md)

---

## 链接

- **GitHub**: https://github.com/mouxangithub/unified-memory
- **ClawHub**: https://clawhub.com/skill/unified-memory

---

*更新: 2026-03-23*
