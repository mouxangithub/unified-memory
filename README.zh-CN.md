---
priority: critical
title: Unified Memory v4.0.0 — 中文自述（旧版）
---

<!-- Language Toggle -->
**[English](./README.md)** · [中文](./README_CN.md) · [日本語](./README_JA.md)

> ⚠️ **旧版文档** — 本文件为旧版中文自述。建议阅读 [README_CN.md](./README_CN.md) 获取最新中文文档。

---

# Unified Memory v4.0.0

> AI Agent 记忆系统 — 多层化、持久化、主动化

**作者**: 程序员小刘 (@mouxangithub)  
**GitHub**: https://github.com/mouxangithub/unified-memory  
**安装**: `clawhub install unified-memory`  
**版本**: 3.8.4 (2026-03-30)

---

## 概述

Unified Memory 是 OpenClaw Agent 领域功能最丰富的记忆系统 MCP 服务器。它提供持久化上下文、混合搜索（BM25 + 向量 + RRF 融合）、Weibull 衰减、WAL 崩溃恢复、证据链、Transcript-First 架构、泳道记忆、Token 预算强制执行以及深度的 Scope 隔离 —— 全部使用纯 Node.js ESM 实现，零 Python 依赖。

## 核心功能

- 🔄 **持久化上下文** — 记忆在会话重启和压缩事件中持久保存
- 🔍 **混合搜索** — BM25 + 向量 + RRF 融合，支持 MMR 重排
- 📈 **Weibull 衰减** — 模拟人类遗忘曲线
- 💾 **WAL 协议** — 崩溃可恢复的预写日志
- 🏷️ **四层 Scope 隔离** — AGENT / USER / TEAM / GLOBAL
- 📊 **知识图谱** — 实体提取和关系映射
- 🔗 **证据链** — 来源追踪和置信度评分
- 📝 **Transcript-First** — 从 transcript 重建记忆
- 🏊 **泳道记忆** — 并行对话线程隔离
- 💰 **Token 预算** — 硬限制和自动压缩

## 安装

```bash
clawhub install unified-memory
openclaw gateway restart
```

验证：
```bash
mcporter call unified-memory memory_health '{}'
```

## 快速入门

```bash
# 存储记忆
mcporter call unified-memory memory_store '{
  "text": "Liu prefers concise communication",
  "category": "preference",
  "scope": "USER"
}'

# 搜索记忆
mcporter call unified-memory memory_search '{
  "query": "Liu communication style",
  "scope": "USER"
}'

# 查看统计
mcporter call unified-memory memory_stats '{}'
```

## 文档索引

| 文件 | 说明 |
|------|------|
| [README.md](./README.md) | 英汉双语主文档 |
| [README_CN.md](./README_CN.md) | **新版中文主文档（推荐）** |
| [docs/index.md](./docs/index.md) | 📚 **全部文档索引** |
| [docs/zh/README.md](./docs/zh/README.md) | 中文技术概述 |
| [docs/zh/HOOK_INTEGRATION.md](./docs/zh/HOOK_INTEGRATION.md) | Hook 集成指南 |
| [docs/zh/MCP_INTEGRATION.md](./docs/zh/MCP_INTEGRATION.md) | MCP 集成指南 |
| [docs/zh/INTEGRATION_COMPARISON.md](./docs/zh/INTEGRATION_COMPARISON.md) | 集成对比 |

---

*最后更新：2026-04-01 | v3.8.4 | 建议使用 [README_CN.md](./README_CN.md)*
