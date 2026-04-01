# Hook Integration Guide

[中文](./zh/HOOK_INTEGRATION.md) | [README](./README.md) | English

## Overview

The Unified Memory hook system provides **completely transparent automatic memory capture**. Once enabled, the agent automatically saves important context after every conversation — no manual intervention required.

## How the Hook Works

The hook system integrates into two key lifecycle points:

### 1. `before_prompt_build` — Context Injection

Before each prompt is constructed, the hook system:

1. Retrieves relevant memories from storage based on current context
2. Injects those memories into the prompt as `<memory>` blocks
3. Marks injected memories as "recently accessed" to track importance

```
User Query → Hook Intercepts → Retrieve Relevant Memories → Inject into Prompt → Continue
```

**Injection Format:**

```markdown
<memory>
## Recent Context
- [2026-03-28] User asked about setting up OpenClaw on macOS
- [2026-03-25] Discussed preference for dark mode terminals
</memory>
```

### 2. `agent_end` — Automatic Extraction

After each conversation completes, the hook system:

1. Analyzes the conversation transcript
2. Extracts key facts, decisions, preferences, and commitments
3. Creates semantic chunks with importance scores
4. Stores chunks in the unified memory database

```
Conversation Ends → Analyze Transcript → Extract Key Info → Score & Store
```

## Configuration Options

### Basic Configuration

```json
{
  "unified-memory": {
    "hook": "enabled",
    "config": {
      "before_prompt_build": {
        "enabled": true,
        "maxMemories": 10,
        "similarityThreshold": 0.7,
        "injectionFormat": "block"
      },
      "agent_end": {
        "enabled": true,
        "autoExtract": true,
        "minImportanceScore": 0.3,
        "maxChunksPerSession": 50
      }
    }
  }
}
```

### Advanced Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `maxMemories` | number | 10 | Maximum memories to inject per prompt |
| `similarityThreshold` | number | 0.7 | Minimum similarity score (0-1) |
| `minImportanceScore` | number | 0.3 | Minimum score to save a chunk |
| `maxChunksPerSession` | number | 50 | Maximum chunks per conversation |
| `injectionFormat` | string | "block" | How memories appear: "block", "inline", or "json" |
| `excludedContexts` | string[] | [] | Patterns to exclude from extraction |

### Context Exclusion Example

```json
{
  "config": {
    "agent_end": {
      "excludedContexts": [
        "password:*",
        "api_key:*",
        "secret:*"
      ]
    }
  }
}
```

## Performance Impact

### Latency Overhead

| Phase | Typical | With Hook |
|-------|---------|-----------|
| Prompt Build | 10-50ms | 15-80ms |
| Memory Retrieval | — | 5-30ms |
| Storage Write | — | 2-10ms |
| **Total** | **10-50ms** | **22-120ms** |

### Resource Usage

- **CPU**: ~1-3% additional during retrieval
- **Memory**: ~5-20MB for index cache
- **Storage**: ~1-10KB per conversation session
- **Vector Embeddings**: ~1KB per chunk (if using semantic search)

### Optimization Tips

1. **Raise the threshold** if you have large memory stores — reduces retrieval time
2. **Limit maxChunksPerSession** for shorter, faster extractions
3. **Use injectionFormat: "inline"** for reduced token overhead

## Hook vs. Manual: When Hooks Run

```
┌─────────────────────────────────────────────────────────┐
│                    Session Lifecycle                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Session Start                                           │
│      │                                                   │
│      ▼                                                   │
│  ┌─────────────────────┐                                 │
│  │ before_prompt_build │ ◀─── Runs BEFORE every prompt  │
│  │   (memory inject)   │                                 │
│  └─────────────────────┘                                 │
│      │                                                   │
│      ▼                                                   │
│  ┌─────────────────────┐                                 │
│  │   Agent Processing  │                                 │
│  └─────────────────────┘                                 │
│      │                                                   │
│      ▼                                                   │
│  ┌─────────────────────┐                                 │
│  │     agent_end       │ ◀─── Runs AFTER every session  │
│  │  (memory extract)   │                                 │
│  └─────────────────────┘                                 │
│      │                                                   │
│      ▼                                                   │
│  Session End                                             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Disabling Hooks

To disable hook-based capture while keeping MCP access:

```json
{
  "unified-memory": {
    "hook": "disabled",
    "config": {
      "mcpEnabled": true
    }
  }
}
```

## Troubleshooting

**Memories not being injected:**
- Check that `before_prompt_build.enabled` is `true`
- Verify the memory store has entries
- Lower `similarityThreshold` if memories exist but aren't matching

**Extraction seems poor:**
- Increase `maxChunksPerSession` for more thorough extraction
- Lower `minImportanceScore` to capture lower-confidence memories

**Performance is slow:**
- Raise `similarityThreshold` to reduce result set
- Reduce `maxMemories` to limit injection count
