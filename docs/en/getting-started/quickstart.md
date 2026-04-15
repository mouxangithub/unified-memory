# Quick Start Guide

[English](./quickstart.md) · [中文](../../zh/getting-started/quickstart.md)

This guide will help you get started with Unified Memory in under 5 minutes.

## 🚀 Installation

### Option 1: Using Install Script (Recommended)
```bash
# Install with one command
curl -fsSL https://raw.githubusercontent.com/mouxangithub/unified-memory/main/install.sh | bash
```

### Option 2: Using npm
```bash
# Install globally
npm install -g unified-memory

# Or install locally in your project
npm install unified-memory
```

### Option 3: Manual Installation
```bash
# Clone the repository
git clone https://github.com/mouxangithub/unified-memory.git
cd unified-memory

# Install dependencies
npm install

# Build the project
npm run deploy
```

## 📦 Verify Installation

```bash
# Check if installation was successful
unified-memory --version
# Should output: v5.2.0

# Or if installed locally
node -e "console.log(require('unified-memory').version)"
```

## 🔧 Basic Configuration

Create a configuration file at `~/.unified-memory/config.json`:

```json
{
  "storage": {
    "mode": "json",
    "memoryFile": "~/.unified-memory/memories.json",
    "vectorStore": {
      "backend": "lancedb",
      "path": "~/.unified-memory/vector.lance"
    }
  },
  "transaction": {
    "enable": true,
    "recoveryLog": "~/.unified-memory/transaction-recovery.log"
  }
}
```

## 💡 Your First Memory

### Using JavaScript/TypeScript
```javascript
import { addMemory, searchMemories } from 'unified-memory';

// Add your first memory
const memoryId = await addMemory({
  text: "Remember to check the quarterly reports",
  tags: ["work", "reminder", "reports"],
  metadata: {
    priority: "high",
    category: "work",
    createdBy: "user123"
  }
});

console.log(`Memory added with ID: ${memoryId}`);

// Search for memories
const results = await searchMemories("quarterly reports");
console.log("Search results:", results);
```

### Using CLI
```bash
# Add a memory via CLI
unified-memory add "Remember to check the quarterly reports" --tags work,reminder,reports

# Search memories
unified-memory search "quarterly reports"

# List all memories
unified-memory list
```

## 🔍 Basic Search Examples

### Simple Text Search
```javascript
const results = await searchMemories("meeting notes");
```

### Search with Filters
```javascript
const results = await searchMemories("project", {
  filters: {
    tags: ["work", "urgent"],
    metadata: {
      priority: "high"
    }
  },
  limit: 10
});
```

### Hybrid Search (BM25 + Vector)
```javascript
const results = await searchMemories("important deadlines", {
  searchType: "hybrid",  // Options: "bm25", "vector", "hybrid"
  vectorWeight: 0.7,     // Weight for vector similarity (0-1)
  bm25Weight: 0.3        // Weight for BM25 relevance (0-1)
});
```

## 📊 Viewing Memories

### Get All Memories
```javascript
const allMemories = await getAllMemories({
  limit: 50,
  offset: 0,
  sortBy: "createdAt",
  sortOrder: "desc"
});
```

### Get Memory by ID
```javascript
const memory = await getMemory(memoryId);
console.log(memory);
```

### Get Memory Statistics
```javascript
const stats = await getMemoryStats();
console.log(stats);
// Output: { total: 150, byTag: { work: 50, personal: 100 }, ... }
```

## 🔄 Atomic Transactions Example

Unified Memory v5.2.0 guarantees atomic writes:

```javascript
import { beginTransaction, commitTransaction, rollbackTransaction } from 'unified-memory';

try {
  // Start a transaction
  const tx = await beginTransaction();
  
  // Add multiple memories atomically
  await addMemory({
    text: "First memory in transaction",
    tags: ["transaction", "test"]
  }, { transaction: tx });
  
  await addMemory({
    text: "Second memory in transaction",
    tags: ["transaction", "test"]
  }, { transaction: tx });
  
  // Commit - both memories are saved atomically
  await commitTransaction(tx);
  console.log("Transaction committed successfully");
  
} catch (error) {
  // If anything fails, the transaction is rolled back
  await rollbackTransaction(tx);
  console.error("Transaction rolled back:", error);
}
```

## 🔌 Plugin System Quick Start

### Sync with Workspace Memory
```bash
# Manual sync
npm run sync:manual

# Schedule daily sync at 2 AM
npm run sync
```

### Unified Query Interface
```bash
# Search across all memory systems
npm run query:unified -- "search keywords"

# Start query server on port 3851
npm run query:unified -- --server 3851
```

### Health Monitoring
```bash
# Check system health
npm run monitor

# View dashboard
npm run monitor:dashboard
```

## 🧪 Testing Your Setup

### Run Basic Tests
```bash
# Verify core functionality
npm run verify

# Run unit tests
npm run test:unit

# Run integration tests
npm run test:integration
```

### Test Atomic Writes
```bash
# Test transaction safety
npm run test:unit -- --test atomic-transactions
```

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found" error**
   ```bash
   # Reinstall dependencies
   npm install
   ```

2. **Vector store initialization failed**
   ```bash
   # Reinitialize vector store
   rm -rf ~/.unified-memory/vector.lance
   unified-memory init
   ```

3. **Permission errors**
   ```bash
   # Fix permissions
   chmod 755 ~/.unified-memory
   ```

### Getting Help

- Check the [Troubleshooting Guide](../guides/troubleshooting.md)
- Search [GitHub Issues](https://github.com/mouxangithub/unified-memory/issues)
- Review the [FAQ](../reference/faq.md)

## 📈 Next Steps

Now that you've completed the quick start, explore:

1. **[Advanced Features](../guides/advanced-features.md)** - Learn about advanced capabilities
2. **[API Documentation](../api/overview.md)** - Full API reference
3. **[Plugin System](../guides/plugins.md)** - Extend functionality with plugins
4. **[Performance Tuning](../reference/configuration.md)** - Optimize for your use case

---

**Need help?** Join our community or open an issue on GitHub!

[← Back to Documentation](../../README.md) · [Next: Advanced Features →](../guides/advanced-features.md)