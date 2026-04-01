# Unified Memory - Overview

[中文](./zh/README.md) | English | [📚 Docs Index](../index.md)

## What is Unified Memory?

Unified Memory is an OpenClaw skill that provides **long-term memory persistence** for AI assistants. It solves the fundamental problem that AI assistants forget everything after each session by automatically extracting, storing, and retrieving relevant context across conversations.

## Core Features

- **Automatic Extraction** — Uses OpenClaw hooks to capture important context at the end of every conversation
- **Semantic Search** — Stores memories as semantic chunks enabling natural-language queries
- **Dual Access Methods** — Works via both MCP tools (explicit) and Hook injection (automatic)
- **Zero Friction** — Memories are captured automatically without requiring the user to explicitly save anything

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐                  │
│  │    Hooks     │    │  MCP Server  │                  │
│  │              │    │              │                  │
│  │ agent_end    │───▶│ memory_search│                  │
│  │ (auto-save)  │    │ memory_update│                  │
│  └──────────────┘    └──────────────┘                  │
│         │                   │                          │
│         ▼                   ▼                          │
│  ┌──────────────────────────────────┐                  │
│  │      Unified Memory Storage      │                  │
│  │   (Workspace + Vector Similarity) │                  │
│  └──────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Option 1: Hook + MCP (Recommended)

This provides the best of both worlds — automatic capture via hooks and explicit recall via MCP tools.

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

### Option 2: MCP Only

Manual memory management with full control.

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

## Integration Methods

| Method | Auto-Capture | Manual Recall | Best For |
|--------|-------------|---------------|----------|
| **Hook + MCP** | ✅ | ✅ | Most users |
| **MCP Only** | ❌ | ✅ | Fine-grained control |
| **Hook Only** | ✅ | ❌ | Simple transparent operation |

See [Integration Comparison](./INTEGRATION_COMPARISON.md) for detailed analysis.

## Key Concepts

### Memory Chunks

Memories are stored as semantic chunks — small units of meaning that can be individually retrieved. Each chunk includes:
- **content**: The actual memory text
- **timestamp**: When the memory was created
- **session_id**: Which conversation it came from
- **importance**: Auto-assigned relevance score (0-1)
- **tags**: Optional categorizations

### The Hook System

The `agent_end` hook automatically triggers after each conversation, extracting key information and saving it. See [Hook Integration](./HOOK_INTEGRATION.md) for details.

### The MCP Tools

The MCP server exposes memory tools for explicit search, update, and management. See [MCP Integration](./MCP_INTEGRATION.md) for details.

## File Structure

```
unified-memory/
├── docs/
│   ├── en/
│   │   ├── README.md           ← You are here
│   │   ├── HOOK_INTEGRATION.md
│   │   ├── MCP_INTEGRATION.md
│   │   └── INTEGRATION_COMPARISON.md
│   └── zh/
│       ├── README.md
│       ├── HOOK_INTEGRATION.md
│       ├── MCP_INTEGRATION.md
│       └── INTEGRATION_COMPARISON.md
├── SKILL.md                    ← Main skill file
└── HOOK.md                     ← Hook configuration
```

## FAQ

**Q: Does it work with any AI model?**
A: Yes — the memory system is model-agnostic. It stores semantic representations that work with any embedding model.

**Q: How much storage does it use?**
A: Typically 1-10KB per conversation, depending on context length. Vector embeddings add ~1KB per chunk.

**Q: Can I delete specific memories?**
A: Yes — use the `memory_delete` MCP tool or reference a memory ID directly.

**Q: What's the similarity threshold for?**
A: It controls how strictly memories must match your query. Lower = more results, higher = more precise.

---

## 📚 Documentation Index

> 🌍 **[English](../en/README.md)** · [中文](../zh/README.md) · [📚 All Docs Index](../index.md)

| Document | Language | Description |
|----------|----------|-------------|
| [README.md](../README.md) | 🌍 | Main documentation |
| [README_CN.md](../README_CN.md) | 🇨🇳 | Chinese main documentation |
| [docs/index.md](../index.md) | 🌍 | **All docs index** — complete documentation hub |
| [docs/en/README.md](../en/README.md) | 🇺🇸 | **You are here** — Technical overview |
| [docs/en/HOOK_INTEGRATION.md](../en/HOOK_INTEGRATION.md) | 🇺🇸 | Hook integration guide |
| [docs/en/MCP_INTEGRATION.md](../en/MCP_INTEGRATION.md) | 🇺🇸 | MCP integration guide |
| [docs/en/INTEGRATION_COMPARISON.md](../en/INTEGRATION_COMPARISON.md) | 🇺🇸 | Integration comparison |
| [docs/zh/README.md](../zh/README.md) | 🇨🇳 | 技术概述 |
| [docs/zh/HOOK_INTEGRATION.md](../zh/HOOK_INTEGRATION.md) | 🇨🇳 | Hook 集成指南 |
| [docs/zh/MCP_INTEGRATION.md](../zh/MCP_INTEGRATION.md) | 🇨🇳 | MCP 集成指南 |
