# Quick Start Guide

> Get started with Unified Memory in 5 minutes.

## 🚀 Installation (One Command)

```bash
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

Verify installation:
```bash
unified-memory --version
# Output: v5.2.0
```

## 💡 Your First Memory

### Using the CLI

```bash
# Add a memory
unified-memory add "Remember to review quarterly reports" --tags work,reminder

# Search memories
unified-memory search "quarterly reports"

# List all memories
unified-memory list

# View a specific memory
unified-memory get <memory-id>

# Delete a memory
unified-memory delete <memory-id>
```

### Using JavaScript/TypeScript

```javascript
const { addMemory, searchMemories, getAllMemories, getMemory, deleteMemory } = require('unified-memory');

async function main() {
  // Add a memory
  const memoryId = await addMemory({
    text: "User prefers morning meetings",
    category: "preference",
    importance: 0.8,
    tags: ["meetings", "schedule"],
    metadata: { priority: "high" }
  });
  console.log(`Added memory: ${memoryId}`);

  // Search memories
  const results = await searchMemories("meeting schedule");
  console.log("Search results:", results);

  // Get all memories
  const allMemories = await getAllMemories();
  console.log(`Total memories: ${allMemories.length}`);

  // Get specific memory
  const memory = await getMemory(memoryId);
  console.log(memory);

  // Delete memory
  await deleteMemory(memoryId);
  console.log("Deleted memory");
}

main().catch(console.error);
```

### Using MCP Tools

```javascript
// Via MCP client (e.g., OpenClaw)
const result = await mcp.call('unified-memory', 'memory_store', {
  text: "Important meeting tomorrow at 9 AM",
  category: "fact",
  importance: 0.9,
  tags: ["meeting", "important"]
});

const searchResult = await mcp.call('unified-memory', 'memory_search', {
  query: "meeting tomorrow",
  topK: 5,
  mode: "hybrid"
});
```

## 🔍 Search Examples

### Simple Search
```javascript
const results = await searchMemories("quarterly reports");
```

### Hybrid Search (BM25 + Vector)
```javascript
const results = await searchMemories("important deadlines", {
  mode: "hybrid",
  vectorWeight: 0.7,
  bm25Weight: 0.3,
  topK: 10
});
```

### Search with Filters
```javascript
const results = await searchMemories("project update", {
  filters: {
    category: "fact",
    tags: ["work"],
    importance: { min: 0.7 }
  }
});
```

## 🔄 Atomic Transactions

Guarantee data consistency when storing multiple related memories:

```javascript
const { beginTransaction, commitTransaction, rollbackTransaction, addMemory } = require('unified-memory');

async function storeTransaction() {
  const tx = await beginTransaction();
  
  try {
    await addMemory({
      text: "Project kickoff meeting",
      tags: ["project", "meeting"]
    }, { transaction: tx });
    
    await addMemory({
      text: "Project deadline is Dec 31",
      tags: ["project", "deadline"]
    }, { transaction: tx });
    
    await commitTransaction(tx);
    console.log("Transaction committed successfully");
  } catch (error) {
    await rollbackTransaction(tx);
    console.error("Transaction rolled back:", error);
  }
}
```

## 🏷️ Memory Categories

Memories are categorized for better organization:

| Category | Description |
|----------|-------------|
| `preference` | User preferences and likes |
| `fact` | Factual information |
| `decision` | Decisions made |
| `entity` | People, places, things |
| `reflection` | Thoughts and reflections |

## 📊 View Statistics

```bash
unified-memory stats
```

Output:
```
Total Memories: 150
Categories: 5
Tags: 42

By Tier:
  HOT: 45 (30%)
  WARM: 60 (40%)
  COLD: 45 (30%)

By Scope:
  USER: 120
  AGENT: 20
  TEAM: 10
```

## 🔌 Plugin Quick Start

### Enable Workspace Sync

```bash
# Sync memories with Workspace Memory
npm run sync:manual

# Schedule automatic sync
npm run sync
```

### Health Monitoring

```bash
# Check system health
npm run monitor

# Start monitoring dashboard
npm run monitor:dashboard
```

## 🧪 Verify Installation

```bash
# Run verification tests
npm run verify

# Run unit tests
npm run test:unit

# Test atomic writes
npm run test:atomic
```

## 🚨 Common Issues

### "Command not found"
```bash
# Reinstall
npm install -g unified-memory
# Or add to PATH
export PATH="$(npm root -g)/bin:$PATH"
```

### Vector store error
```bash
# Reinitialize vector store
rm -rf ~/.unified-memory/vector.lance
unified-memory init
```

### Ollama connection failed
```bash
# Start Ollama
ollama serve

# Pull embedding model
ollama pull nomic-embed-text
```

## 📈 Next Steps

| Goal | Guide |
|------|-------|
| Learn more operations | [Basic Usage Guide](../guides/basic-usage.md) |
| Advanced features | [Advanced Usage](../guides/advanced-usage.md) |
| Build plugins | [Plugin Development](../guides/plugins.md) |
| Understand internals | [Architecture Overview](../architecture/overview.md) |
| API reference | [API Reference](../api/overview.md) |

## 💬 Need Help?

- [Troubleshooting Guide](../reference/troubleshooting.md)
- [FAQ](../reference/faq.md)
- [GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)
