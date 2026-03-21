# Unified Memory MCP Server

Model Context Protocol (MCP) server for unified-memory, allowing AI agents to search and manage memories via MCP.

## Installation

```bash
# Install MCP SDK
pip install mcp

# Verify installation
python3 scripts/memory_mcp_server.py --help
```

## Usage

### Stdio Mode (for Claude Desktop, etc.)

Add to your MCP client config (e.g., Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "unified-memory": {
      "command": "python3",
      "args": ["/home/node/.openclaw/workspace/skills/unified-memory/scripts/memory_mcp_server.py"]
    }
  }
}
```

### Command Line Test

```bash
# Start the MCP server
python3 scripts/memory_mcp_server.py
```

## Available Tools

### 1. memory_search

Search memories using QMD-style layered search.

**Arguments:**
- `query` (required): Search query
- `mode` (optional): `auto` | `bm25` | `vector` | `hybrid` (default: `auto`)
- `top_k` (optional): Number of results (default: 5)
- `use_rerank` (optional): Enable LLM reranking (default: false)

**Token Consumption:**
- BM25 mode: 0 Token
- Vector/ hybrid: ~100 Token
- With rerank: +300 Token

**Example:**
```json
{
  "name": "memory_search",
  "arguments": {
    "query": "项目进度",
    "mode": "hybrid",
    "top_k": 5
  }
}
```

### 2. memory_store

Store a new memory.

**Arguments:**
- `text` (required): Memory content
- `category` (optional): `preference` | `fact` | `decision` | `entity` | `learning` | `other`
- `importance` (optional): 0-1 score (default: 0.5)

**Example:**
```json
{
  "name": "memory_store",
  "arguments": {
    "text": "用户偏好使用飞书进行项目管理",
    "category": "preference",
    "importance": 0.8
  }
}
```

### 3. memory_status

Get system status.

**Returns:**
- Total memories
- BM25 index status
- Vector search config
- LLM rerank config

### 4. memory_config

View or update configuration.

**Arguments:**
- `action`: `get` | `set`
- `config` (for set): Configuration object

**Example:**
```json
{
  "name": "memory_config",
  "arguments": {
    "action": "set",
    "config": {
      "use_vector": true,
      "use_llm_rerank": false
    }
  }
}
```

### 5. memory_health

Check memory system health.

**Returns:**
- Health score
- Orphaned memories
- Contradictions
- Redundancy
- Outdated memories
- Recommendations

## Available Resources

Memories are accessible via `memory://` URIs:

```
memory://<memory_id>
```

Example:
```
memory://96310fdf-c6a0-482f-953a-edfe4a2fea3a
```

## Integration with AI Agents

### Claude Desktop

1. Open Claude Desktop settings
2. Edit `claude_desktop_config.json`
3. Add the server config above
4. Restart Claude Desktop

### OpenClaw

OpenClaw automatically detects and uses unified-memory. No MCP configuration needed.

### Other MCP Clients

The server follows MCP specification 2025-06-18 and should work with any MCP-compliant client.

## Comparison with QMD MCP

| Feature | unified-memory MCP | QMD MCP |
|---------|-------------------|---------|
| Search Tool | ✅ | ✅ |
| Store Tool | ✅ | ❌ |
| Status Tool | ✅ | ✅ |
| Config Tool | ✅ | ❌ |
| Health Tool | ✅ | ❌ |
| Resources | ✅ memory:// | ✅ qmd:// |
| Language | Python | TypeScript |

## Architecture

```
MCP Client (Claude / OpenClaw / etc.)
         │
         ▼
┌─────────────────────────────┐
│   memory_mcp_server.py      │
│   (MCP Protocol Handler)    │
├─────────────────────────────┤
│   Tools:                    │
│   - memory_search           │
│   - memory_store            │
│   - memory_status           │
│   - memory_config           │
│   - memory_health           │
├─────────────────────────────┤
│   Resources:                │
│   - memory://<id>           │
├─────────────────────────────┤
│   memory_qmd_search.py      │
│   (QMD-style Search Engine) │
│   - BM25                    │
│   - Vector                  │
│   - RRF Fusion              │
│   - LLM Rerank              │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│   LanceDB (Vector Store)    │
│   ~/.openclaw/workspace/    │
│   memory/vector/            │
└─────────────────────────────┘
```

## Troubleshooting

### MCP SDK not found

```bash
pip install mcp
```

### Vector search not working

Check Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

### No memories found

Initialize the index:
```bash
python3 scripts/memory_qmd_search.py index
```

---

*Made with ❤️ for AI Agents*
