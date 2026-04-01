# Unified Memory - 概述

[English](./en/README.md) | 中文 | [📚 文档索引](../index.md)

## 什么是 Unified Memory？

Unified Memory 是一个 OpenClaw 技能，为 AI 助手提供**长期记忆持久化**功能。它解决了 AI 助手在每次会话结束后忘记所有内容的根本问题，通过自动提取、存储和检索跨会话的相关上下文来维持连续性。

## 核心功能

- **自动提取** — 使用 OpenClaw Hooks 在每次对话结束时自动捕获重要上下文
- **语义搜索** — 将记忆存储为语义块，支持自然语言查询
- **双重访问方式** — 同时支持 MCP 工具（显式）和 Hook 注入（自动）
- **零摩擦** — 记忆自动捕获，无需用户手动保存任何内容

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐                  │
│  │    Hooks     │    │  MCP Server  │                  │
│  │              │    │              │                  │
│  │ agent_end    │───▶│ memory_search│                  │
│  │ (自动保存)   │    │ memory_update│                  │
│  └──────────────┘    └──────────────┘                  │
│         │                   │                          │
│         ▼                   ▼                          │
│  ┌──────────────────────────────────┐                  │
│  │      Unified Memory Storage      │                  │
│  │   (工作空间 + 向量相似度搜索)    │                  │
│  └──────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 方式一：Hook + MCP（推荐）

结合两者优势 — 通过 Hook 自动捕获，通过 MCP 工具显式检索。

```json
{
  "plugins": {
    "entries": {
      "unified-memory": {
        "hook": "enabled",
        "config": {
          "mcpEnabled": true,
          "autoExtract": true,
          "similarityThreshold": 0.7
        }
      }
    }
  }
}
```

### 方式二：仅 MCP

手动管理记忆，完全可控。

```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "npx",
      "args": ["@openclaw/mcp-memory"]
    }
  }
}
```

## 集成方式对比

| 方式 | 自动捕获 | 手动检索 | 适用场景 |
|------|:--------:|:--------:|---------|
| **Hook + MCP** | ✅ | ✅ | 大多数用户 |
| **仅 MCP** | ❌ | ✅ | 精细化控制 |
| **仅 Hook** | ✅ | ❌ | 简单透明运行 |

详见 [集成对比](./zh/INTEGRATION_COMPARISON.md)。

## 核心概念

### 记忆块（Memory Chunks）

记忆以语义块形式存储 — 可独立检索的小型语义单元。每个块包含：
- **content**: 记忆的实际文本内容
- **timestamp**: 记忆创建时间
- **session_id**: 来源会话 ID
- **importance**: 自动分配的相关性评分 (0-1)
- **tags**: 可选的分类标签

### Hook 系统

`agent_end` Hook 在每次对话完成后自动触发，提取关键信息并保存。详见 [Hook 集成](./zh/HOOK_INTEGRATION.md)。

### MCP 工具

MCP 服务器暴露内存工具用于显式搜索、更新和管理。详见 [MCP 集成](./zh/MCP_INTEGRATION.md)。

## 文件结构

```
unified-memory/
├── docs/
│   ├── en/
│   │   ├── README.md           ← 英文版
│   │   ├── HOOK_INTEGRATION.md
│   │   ├── MCP_INTEGRATION.md
│   │   └── INTEGRATION_COMPARISON.md
│   └── zh/
│       ├── README.md            ← 你在这里
│       ├── HOOK_INTEGRATION.md
│       ├── MCP_INTEGRATION.md
│       └── INTEGRATION_COMPARISON.md
├── SKILL.md                    ← 主技能文件
└── HOOK.md                     ← Hook 配置
```

## 常见问题

**Q: 它支持任何 AI 模型吗？**
A: 是的 — 记忆系统与模型无关。它存储的语义表示可与任何嵌入模型配合使用。

**Q: 它占用多少存储空间？**
A: 通常每个会话 1-10KB，取决于上下文长度。向量嵌入每个块约增加 1KB。

**Q: 我可以删除特定的记忆吗？**
A: 可以 — 使用 `memory_delete` MCP 工具或直接引用记忆 ID。

**Q: 相似度阈值是用来做什么的？**
A: 它控制记忆与查询的匹配严格程度。越低 = 结果越多，越高 = 越精确。

---

## 📚 文档索引

> 🌍 [English](../en/README.md) · **[中文](../zh/README.md)** · [📚 总索引](../index.md)

| 文档 | 语言 | 说明 |
|------|------|------|
| [README.md](../README.md) | 🌍 | 主文档 |
| [README_CN.md](../README_CN.md) | 🇨🇳 | 中文主文档 |
| [docs/index.md](../index.md) | 🌍 | **总索引页** — 全部文档 |
| [docs/zh/README.md](../zh/README.md) | 🇨🇳 | **你在这里** — 技术概述 |
| [docs/zh/HOOK_INTEGRATION.md](../zh/HOOK_INTEGRATION.md) | 🇨🇳 | Hook 集成指南 |
| [docs/zh/MCP_INTEGRATION.md](../zh/MCP_INTEGRATION.md) | 🇨🇳 | MCP 集成指南 |
| [docs/zh/INTEGRATION_COMPARISON.md](../zh/INTEGRATION_COMPARISON.md) | 🇨🇳 | 集成对比 |
| [docs/en/README.md](../en/README.md) | 🇺🇸 | Technical overview |
| [docs/en/HOOK_INTEGRATION.md](../en/HOOK_INTEGRATION.md) | 🇺🇸 | Hook integration |
| [docs/en/MCP_INTEGRATION.md](../en/MCP_INTEGRATION.md) | 🇺🇸 | MCP integration |
