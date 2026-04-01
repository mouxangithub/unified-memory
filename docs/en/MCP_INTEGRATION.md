# MCP Integration Guide

[中文](./zh/MCP_INTEGRATION.md) | [README](./README.md) | English

## Overview

The MCP (Model Context Protocol) integration provides **explicit, programmatic access** to the unified memory system. Use MCP tools when you want fine-grained control over what memories are stored, searched, or deleted.

## Available MCP Tools

### memory_search

Search for relevant memories using natural language queries.

```json
{
  "tool": "memory_search",
  "parameters": {
    "query": "What are the user's preferred coding languages?",
    "limit": 5,
    "similarityThreshold": 0.7
  }
}
```

**Response:**

```json
{
  "results": [
    {
      "id": "mem_abc123",
      "content": "User prefers Python and TypeScript for most projects",
      "timestamp": "2026-03-25T14:30:00Z",
      "sessionId": "sess_xyz789",
      "importance": 0.85,
      "tags": ["preferences", "coding"]
    }
  ],
  "totalMatches": 3
}
```

### memory_write

Store a new memory explicitly.

```json
{
  "tool": "memory_write",
  "parameters": {
    "content": "User works primarily on backend APIs using Go",
    "tags": ["preferences", "work"],
    "importance": 0.9
  }
}
```

### memory_update

Update an existing memory by ID.

```json
{
  "tool": "memory_update",
  "parameters": {
    "id": "mem_abc123",
    "content": "User prefers Python, TypeScript, and increasingly Go",
    "importance": 0.95
  }
}
```

### memory_delete

Delete specific memories.

```json
{
  "tool": "memory_delete",
  "parameters": {
    "id": "mem_abc123"
  }
}
```

### memory_list

List all memories with optional filtering.

```json
{
  "tool": "memory_list",
  "parameters": {
    "limit": 50,
    "offset": 0,
    "tags": ["preferences"],
    "sortBy": "importance"
  }
}
```

### memory_stats

Get statistics about the memory store.

```json
{
  "tool": "memory_stats",
  "parameters": {}
}
```

**Response:**

```json
{
  "totalMemories": 342,
  "totalChunks": 1287,
  "oldestMemory": "2026-01-15T09:00:00Z",
  "newestMemory": "2026-04-01T12:00:00Z",
  "storageSizeBytes": 4821932,
  "tagCounts": {
    "preferences": 45,
    "projects": 120,
    "decisions": 89
  }
}
```

## Configuration

### Enabling MCP in OpenClaw

Add to your OpenClaw configuration:

```json
{
  "plugins": {
    "entries": {
      "unified-memory": {
        "hook": "disabled",
        "config": {
          "mcpEnabled": true,
          "mcpServerPort": 3000
        }
      }
    }
  }
}
```

### MCP Server Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `mcpEnabled` | `true` | Enable MCP server |
| `mcpServerPort` | `3000` | Port for MCP server |
| `mcpServerHost` | `localhost` | Host binding |
| `maxConnections` | `10` | Max concurrent MCP connections |

## Usage Examples

### Example: Remember a User Preference

```javascript
// After a conversation where user mentions a preference
await mcp.callTool("memory_write", {
  content: "User prefers camelCase for variable naming",
  tags: ["preference", "coding-style"],
  importance: 0.8
});
```

### Example: Find All Memories About a Project

```javascript
const results = await mcp.callTool("memory_search", {
  query: "memories about the backend API project",
  limit: 20
});

console.log(`Found ${results.totalMatches} memories`);
results.results.forEach(m => console.log(`- ${m.content}`));
```

### Example: Clean Up Old Memories

```javascript
const stats = await mcp.callTool("memory_stats", {});

// Delete memories older than 90 days
const cutoff = new Date();
cutoff.setDate(cutoff.getDate() - 90);

const allMemories = await mcp.callTool("memory_list", {
  limit: 1000
});

for (const mem of allMemories.results) {
  if (new Date(mem.timestamp) < cutoff) {
    await mcp.callTool("memory_delete", { id: mem.id });
  }
}
```

### Example: Update Importance After Feedback

```javascript
// If user confirms a memory is useful, boost its importance
const current = await mcp.callTool("memory_list", {
  limit: 1,
  sortBy: "importance",
  sortOrder: "desc"
});

if (current.results[0]) {
  await mcp.callTool("memory_update", {
    id: current.results[0].id,
    importance: Math.min(1.0, current.results[0].importance + 0.1)
  });
}
```

## MCP vs Hook: Choosing Your Approach

See [Integration Comparison](../INTEGRATION_COMPARISON.md) for a detailed decision matrix.

**Use MCP when you want:**
- Explicit control over what's stored
- Programmatic memory management
- Ability to query memories in external tools
- Batch operations on memories

**Use Hooks when you want:**
- Completely automatic operation
- No code changes required
- Maximum simplicity
