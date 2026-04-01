# Integration Comparison

[中文](./zh/INTEGRATION_COMPARISON.md) | [README](./README.md) | English

## Three Integration Modes

Unified Memory supports three integration approaches. Choose based on your needs:

| Mode | Auto-Capture | Manual Recall | Complexity | Control |
|------|:------------:|:-------------:|:----------:|:-------:|
| **Hook + MCP** | ✅ | ✅ | Medium | High |
| **MCP Only** | ❌ | ✅ | Low | Full |
| **Hook Only** | ✅ | ❌ | Low | Low |

---

## Mode 1: Hook + MCP (Recommended)

**Best for:** Most users who want automatic capture with the ability to also search/manage memories.

```json
{
  "plugins": {
    "entries": {
      "unified-memory": {
        "hook": "enabled",
        "config": {
          "mcpEnabled": true,
          "autoExtract": true
        }
      }
    }
  }
}
```

### Pros
- ✅ Automatic capture via hooks
- ✅ Explicit recall via MCP tools
- ✅ Most flexible — use either or both
- ✅ Best of both worlds

### Cons
- ⚠️ Slightly higher resource usage (both systems running)
- ⚠️ More configuration options to understand

### Performance Impact
- Memory retrieval: 5-30ms per query
- Storage writes: 2-10ms per session end
- Additional memory: ~5-20MB for dual-system cache

---

## Mode 2: MCP Only

**Best for:** Developers who want full programmatic control, or when hooks aren't available.

```json
{
  "plugins": {
    "entries": {
      "unified-memory": {
        "hook": "disabled",
        "config": {
          "mcpEnabled": true
        }
      }
    }
  }
}
```

### Pros
- ✅ Full control over memory operations
- ✅ Programmatic access from external tools
- ✅ No automatic writes — everything is explicit
- ✅ Lower resource usage than dual mode

### Cons
- ❌ No automatic capture — must call `memory_write` manually
- ❌ More code required for same functionality
- ❌ Requires developer integration

### Performance Impact
- Only pays cost when tools are called
- No background retrieval overhead
- Memory: ~2-10MB (single system)

---

## Mode 3: Hook Only

**Best for:** Simple transparent operation where you never want to think about memory management.

```json
{
  "plugins": {
    "entries": {
      "unified-memory": {
        "hook": "enabled",
        "config": {
          "mcpEnabled": false,
          "autoExtract": true
        }
      }
    }
  }
}
```

### Pros
- ✅ Zero configuration — works out of the box
- ✅ No code changes ever needed
- ✅ Completely transparent to user
- ✅ Lowest complexity

### Cons
- ❌ Cannot explicitly search or manage memories
- ❌ All recall is automatic (hook injection only)
- ❌ No programmatic access

### Performance Impact
- Background retrieval still runs
- No MCP server overhead
- Memory: ~5-15MB

---

## Feature Comparison Matrix

| Feature | Hook + MCP | MCP Only | Hook Only |
|---------|:----------:|:--------:|:---------:|
| Auto-extract after session | ✅ | ❌ | ✅ |
| Auto-inject at prompt | ✅ | ❌ | ✅ |
| Search memories | ✅ | ✅ | ❌ |
| Update specific memory | ✅ | ✅ | ❌ |
| Delete specific memory | ✅ | ✅ | ❌ |
| Batch operations | ✅ | ✅ | ❌ |
| External tool access | ✅ | ✅ | ❌ |
| Stats/monitoring | ✅ | ✅ | ❌ |
| Memory importance scoring | ✅ | ✅ | ✅ |
| Tag-based filtering | ✅ | ✅ | ❌ |

---

## Resource Usage Comparison

| Resource | Hook + MCP | MCP Only | Hook Only |
|----------|:----------:|:--------:|:---------:|
| **Memory** | ~15-30MB | ~5-15MB | ~10-20MB |
| **CPU (idle)** | ~0.5-2% | ~0.1-0.5% | ~0.5-2% |
| **CPU (active)** | ~2-5% | ~1-3% | ~2-4% |
| **Storage/conversation** | ~5-15KB | ~0-10KB | ~5-15KB |
| **Latency overhead** | ~15-120ms | ~0-50ms | ~10-80ms |

---

## Scenario Recommendations

### Use Hook + MCP when:

- ✅ You're an end user who wants memory to "just work"
- ✅ You occasionally want to search old memories
- ✅ You're not sure which mode to choose
- ✅ You want automatic capture but also programmatic access

### Use MCP Only when:

- ✅ You're building an application on top of unified memory
- ✅ You need to integrate with external tools or CI/CD
- ✅ You want complete control over what gets stored
- ✅ Hooks are blocked in your environment

### Use Hook Only when:

- ✅ You want maximum simplicity
- ✅ You never need to manually search memories
- ✅ You don't want any extra UI or tools
- ✅ You're okay with purely automatic recall

---

## Migration Between Modes

Switching modes is straightforward — memories are shared across all modes:

```
Hook + MCP  ←→  MCP Only  ←→  Hook Only
     │              │             │
     └──────────────┴─────────────┘
                (Same memory store)
```

**To switch:** Just update the configuration. No data migration needed.
