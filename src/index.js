/**
 * Unified Memory MCP Server v1.1 - Full-featured memory system
 * Complete port from Python unified-memory to Node.js
 */

import { z } from 'zod';
import { McpServer } from '/usr/local/lib/node_modules/mcporter/node_modules/@modelcontextprotocol/sdk/dist/cjs/server/mcp.js';
import { StdioServerTransport } from '/usr/local/lib/node_modules/mcporter/node_modules/@modelcontextprotocol/sdk/dist/cjs/server/stdio.js';

import { config, log } from './config.js';
import { getAllMemories, addMemory, deleteMemory, touchMemory, saveMemories } from './storage.js';
import { hybridSearch } from './fusion.js';
import { analyzeInsights } from './tools/insights.js';
import { exportMemories } from './tools/export.js';
import { dedupMemories } from './tools/dedup.js';
import { decayMemories } from './tools/decay.js';
import { askQuestion } from './tools/qa.js';

const server = new McpServer(
  { name: 'unified-memory-mcp', version: '1.1.0' },
  { capabilities: { tools: {} } }
);

// ============ Core Search Tools ============

server.registerTool('memory_search', {
  description: 'Search memories using BM25 + Vector hybrid search powered by Ollama. Returns relevant memories ranked by relevance.',
  inputSchema: z.object({
    query: z.string().describe('Search query text'),
    topK: z.number().optional().default(5).describe('Number of results to return'),
    mode: z.enum(['hybrid', 'bm25', 'vector']).optional().default('hybrid').describe('Search mode: hybrid=BM25+vector, bm25=keyword only, vector=semantic only'),
  }),
}, async ({ query, topK = 5, mode = 'hybrid' }) => {
  log('INFO', `Search: query="${query}" mode=${mode} topK=${topK}`);
  try {
    const results = await hybridSearch(query, topK, mode);
    for (const r of results) {
      touchMemory(r.memory.id);
    }
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: results.length,
          query,
          mode,
          results: results.map((r) => ({
            id: r.memory.id,
            text: r.memory.text,
            category: r.memory.category,
            importance: r.memory.importance,
            score: Math.round(r.fusionScore * 1000) / 1000,
            highlight: r.highlight,
            created_at: new Date(r.memory.created_at).toISOString(),
          })),
        }, null, 2),
      }],
    };
  } catch (err) {
    log('ERROR', `Search failed: ${err.message}`);
    return { content: [{ type: 'text', text: `Search error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_store', {
  description: 'Store a new memory with content, category, importance and tags.',
  inputSchema: z.object({
    text: z.string().describe('Memory content (required)'),
    category: z.string().optional().default('general').describe('Category: preference, fact, decision, entity, reflection, or other'),
    importance: z.number().optional().default(0.5).describe('Importance score 0-1'),
    tags: z.array(z.string()).optional().default([]).describe('Tags for the memory'),
  }),
}, async ({ text, category = 'general', importance = 0.5, tags = [] }) => {
  log('INFO', `Store: text="${text.slice(0, 50)}..." category=${category}`);
  try {
    const mem = addMemory({ text, category, importance, tags });
    return { content: [{ type: 'text', text: JSON.stringify({ success: true, id: mem.id }) }] };
  } catch (err) {
    log('ERROR', `Store failed: ${err.message}`);
    return { content: [{ type: 'text', text: `Store error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_list', {
  description: 'List all stored memories with their metadata.',
  inputSchema: z.object({}),
}, async () => {
  try {
    const memories = getAllMemories();
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: memories.length,
          memories: memories.map((m) => ({
            id: m.id,
            text: m.text.slice(0, 100),
            category: m.category,
            importance: m.importance,
            created_at: new Date(m.created_at).toISOString(),
          })),
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `List error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_delete', {
  description: 'Delete a memory by its ID.',
  inputSchema: z.object({
    id: z.string().describe('Memory ID to delete'),
  }),
}, async ({ id }) => {
  try {
    const success = deleteMemory(id);
    return { content: [{ type: 'text', text: JSON.stringify({ success }) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Delete error: ${err.message}` }], isError: true };
  }
});

// ============ Advanced Tools (NEW in v1.1) ============

server.registerTool('memory_insights', {
  description: 'Analyze user memory insights: category distribution, tool usage patterns, project trends, and personalized suggestions.',
  inputSchema: z.object({}),
}, async () => {
  try {
    return await analyzeInsights();
  } catch (err) {
    log('ERROR', `Insights failed: ${err.message}`);
    return { content: [{ type: 'text', text: `Insights error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_export', {
  description: 'Export memories to JSON, Markdown, or CSV format. Supports filtering by category and minimum importance.',
  inputSchema: z.object({
    format: z.enum(['json', 'markdown', 'csv']).optional().default('json').describe('Export format'),
    output: z.string().optional().describe('Output file path'),
    category: z.string().optional().describe('Filter by category'),
    minImportance: z.number().optional().describe('Minimum importance threshold'),
  }),
}, async (args) => {
  try {
    return await exportMemories(args);
  } catch (err) {
    log('ERROR', `Export failed: ${err.message}`);
    return { content: [{ type: 'text', text: `Export error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_dedup', {
  description: 'Detect and merge duplicate memories using hash + Levenshtein similarity.',
  inputSchema: z.object({
    threshold: z.number().optional().default(0.85).describe('Similarity threshold 0-1'),
    dryRun: z.boolean().optional().default(true).describe('If true, only preview changes'),
  }),
}, async ({ threshold = 0.85, dryRun = true }) => {
  try {
    return await dedupMemories({ threshold, dryRun });
  } catch (err) {
    log('ERROR', `Dedup failed: ${err.message}`);
    return { content: [{ type: 'text', text: `Dedup error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_decay', {
  description: 'Apply time-based importance decay based on memory category half-life rules.',
  inputSchema: z.object({
    apply: z.boolean().optional().default(false).describe('If true, apply decay to memories'),
  }),
}, async ({ apply = false }) => {
  try {
    return await decayMemories({ apply });
  } catch (err) {
    log('ERROR', `Decay failed: ${err.message}`);
    return { content: [{ type: 'text', text: `Decay error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_qa', {
  description: 'Answer questions based on relevant memories using RAG.',
  inputSchema: z.object({
    question: z.string().describe('Question to answer based on memories'),
  }),
}, async ({ question }) => {
  try {
    return await askQuestion({ question });
  } catch (err) {
    log('ERROR', `QA failed: ${err.message}`);
    return { content: [{ type: 'text', text: `QA error: ${err.message}` }], isError: true };
  }
});

// ============ Stats & Health ============

server.registerTool('memory_stats', {
  description: 'Get memory system statistics: count, categories, tags, access patterns.',
  inputSchema: z.object({}),
}, async () => {
  try {
    const memories = getAllMemories();
    const categories = {};
    const tagCounts = {};
    for (const m of memories) {
      categories[m.category] = (categories[m.category] || 0) + 1;
      for (const tag of m.tags || []) {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      }
    }
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          total: memories.length,
          categories,
          topTags: Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([tag, count]) => ({ tag, count })),
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Stats error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_health', {
  description: 'Health check for the MCP server and its dependencies.',
  inputSchema: z.object({}),
}, async () => {
  try {
    const memories = getAllMemories();
    let ollamaOk = false;
    try {
      const res = await fetch(`${config.ollamaUrl}/api/tags`);
      ollamaOk = res.ok;
    } catch { ollamaOk = false; }
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          status: 'ok',
          version: '1.1.0',
          memoryCount: memories.length,
          ollama: ollamaOk ? 'connected' : 'disconnected',
          embedModel: config.embedModel,
          llmModel: config.llmModel,
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Health error: ${err.message}` }], isError: true };
  }
});

// ============ Start ============

async function main() {
  log('INFO', `Starting unified-memory-mcp v1.1.0`);
  log('INFO', `Memory file: ${config.memoryFile}`);
  log('INFO', `Ollama: ${config.ollamaUrl}`);

  const transport = new StdioServerTransport();
  await server.connect(transport);
  log('INFO', 'MCP Server connected via stdio');
}

main().catch((err) => {
  console.error('Fatal:', err);
  process.exit(1);
});
