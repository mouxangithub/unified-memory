/**
 * Unified Memory MCP Server v1.1 - Full-featured memory system
 * Complete port from Python unified-memory to Node.js
 */

import { z } from 'zod';
import { McpServer } from '/usr/local/lib/node_modules/mcporter/node_modules/@modelcontextprotocol/sdk/dist/cjs/server/mcp.js';
import { StdioServerTransport } from '/usr/local/lib/node_modules/mcporter/node_modules/@modelcontextprotocol/sdk/dist/cjs/server/stdio.js';
import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

import { config, log as configLog } from './config.js';
import { log as structuredLog, getLogger } from './logger.js';
import { metrics, recordSearchLatency, recordStore, recordError } from './metrics.js';
import { startTrace, endTrace, getTraceExport, clearTrace } from './tracer.js';
import { getAllMemories, getMemory, addMemory, deleteMemory, touchMemory, saveMemories } from './storage.js';
import { hybridSearch } from './fusion.js';
import { analyzeInsights } from './tools/insights.js';
import { exportMemories } from './tools/export.js';
import { dedupMemories } from './tools/dedup.js';
import { decayMemories } from './tools/decay.js';
import { askQuestion } from './tools/qa.js';
import { memoryPreferenceSlotsTool } from './preference_slots.js';
import { memoryLessonsTool } from './lesson.js';
import { extractImportantInfo, isSensitive, autoStore } from './tools/autostore.js';
import { ConcurrentSearch } from './tools/concurrent_search.js';
import { cmdPredict } from './tools/predict.js';
import { cmdRecommend } from './tools/recommend.js';
import { MemoryInference, cmdInference } from './tools/inference.js';
import { MemorySummarizer, cmdSummary } from './tools/summary.js';
import { FeedbackLearner, OUTCOME_HELPFUL, OUTCOME_IRRELEVANT, OUTCOME_WRONG, OUTCOME_OUTDATED } from './tools/feedback_learner.js';
import { qmdSearch } from './tools/qmd_search.js';
import { TemplateManager, cmdTemplates } from './tools/templates.js';
import { shouldStore, qualityScore, learnNoisePattern, getNoiseCount } from './noise.js';
import { routeSearch, INTENT_TYPES } from './intent.js';
import { extractMemories, batchExtract } from './extract.js';
import { addLearning, addError, getLearnings, getErrors, getStats } from './reflection.js';
import { initWal, flushWal, listWalFiles, logOp } from './wal.js';
import { assignTiers, partitionByTier, redistributeTiers, compressColdTier, autoMigrateTiers } from './tier.js';
import { memoryTierStatusTool, memoryTierMigrateTool, memoryTierCompressTool } from './tier_tools.js';
import { shouldSkipRetrieval } from './adaptive.js';
import { buildBM25Index, bm25Search } from './bm25.js';
import { getEmbedding, vectorSearch } from './vector_lancedb.js';
import { mmrSelect, mmrSelectWithEmbedding } from './mmr.js';
import { LlmReranker, keywordRerank } from './rerank.js';
import { CrossEncoderRerank, rerankResults } from './tools/rerank.js';
import { normalizeScope, filterByScope, SCOPE_LEVELS, SCOPE_HIERARCHY } from './scope.js';
import { getProactiveManager } from './proactive_manager.js';
import { getReminderScheduler } from './reminder.js';
import { enhancedPredictRecall, predictRelatedOnAccess, predictHighValueMemories } from './tools/predict.js';
import { registerMultimodalTools } from './multimodal.js';
import { registerEpisodeTools } from './episode/episode_tools.js';
import { registerRerankTools } from './rerank/rerank_tools.js';
import { registerRefreshTools } from './consolidate/refresh_tools.js';
import { registerProceduralTools } from './procedural/procedural_tools.js';
import { registerRuleTools } from './rule/rule_tools.js';
import { registerObservabilityTools } from './observability/observability_tools.js';
import { registerChunkTools } from './chunking/chunk_tools.js';
import { registerPluginTools } from './plugin/tools.js';
import { registerGitTools } from './integrations/git_tools.js';
import { registerCloudTools } from './integrations/cloud_tools.js';
import { registerDecayStatsTool } from './decay/weibull_tools.js';

// Feature #10: Preference Slots
import { memoryPreferenceGetTool, memoryPreferenceSetTool, memoryPreferenceInferTool, memoryPreferenceExplainTool } from './tools/preference_tools.js';

// Feature #11 + v2.7.0: Semantic Versioning + 完整修订历史
import { memoryVersionListTool, memoryVersionDiffTool, memoryVersionRestoreTool } from './tools/version_tools.js';

// P0-2: Entity Tools
import { memoryEntityExtractTool, memoryEntityLinkTool, memoryEntityNeighborsTool, memoryEntitySearchTool } from './tools/entity_tools.js';

// v2.7.0: Identity Memory Tools
import { memoryIdentityExtractTool, memoryIdentityUpdateTool, memoryIdentityGetTool } from './tools/identity_tools.js';

// P1-4: Git Notes
import { memoryGitnotesBackupTool, memoryGitnotesRestoreTool } from './tools/git_notes.js';

// P1-6: Auto Extractor
import { AutoExtractor } from './tools/auto_extractor.js';

// P1-5: Token Budget
import { calculateBudget } from './budget.js';

// P2-7: Cloud Backup (from existing collab/cloud.js)
import { MemoryBackup, CloudConfig } from './collab/cloud.js';

// P0-3: Transcript logging (simple file-based)
import { existsSync, mkdirSync, appendFileSync } from 'fs';
import { join } from 'path';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TRANSCRIPTS_DIR = join(__dirname, '..', 'transcripts');

function ensureTranscriptsDir() {
  if (!existsSync(TRANSCRIPTS_DIR)) mkdirSync(TRANSCRIPTS_DIR, { recursive: true });
}

function logTranscript(operation, data) {
  try {
    ensureTranscriptsDir();
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    const logFile = join(TRANSCRIPTS_DIR, `${today}.jsonl`);
    const entry = JSON.stringify({ op: operation, ...data, ts: new Date().toISOString() }) + '\n';
    appendFileSync(logFile, entry, 'utf8');
  } catch {
    // Best-effort logging
  }
}

const server = new McpServer(
  { name: 'unified-memory-mcp', version: '1.1.0' },
  { capabilities: { tools: {} } }
);

// ============ Core Search Tools ============

server.registerTool('memory_search', {
  description: 'Search memories using BM25 + Vector hybrid search powered by Ollama. Returns relevant memories ranked by relevance. Scope filtering enables true multi-tenant isolation. P2-8: scope=team searches TEAM scope + all USER scope memories.',
  inputSchema: z.object({
    query: z.string().describe('Search query text'),
    topK: z.number().optional().default(5).describe('Number of results to return'),
    mode: z.enum(['hybrid', 'bm25', 'vector']).optional().default('hybrid').describe('Search mode: hybrid=BM25+vector, bm25=keyword only, vector=semantic only'),
    scope: z.string().optional().describe('Scope filter: AGENT, USER, TEAM, GLOBAL, or team (P2-8: team = TEAM + all USER scopes)'),
  }),
}, async ({ query, topK = 5, mode = 'hybrid', scope }) => {
  const span = startTrace('memory_search', { query: query.slice(0, 50), scope: mode });
  const timer = metrics.timer('memory_search', { scope: mode });
    structuredLog.info( `Search: query="${query}" mode=${mode} topK=${topK} scope=${scope}`);
  try {
    // P2-8: scope=team → search TEAM scope + all USER scope memories
    let effectiveScope = scope || null;
    if (scope && scope.toLowerCase() === 'team') {
      // TEAM + all USER scope: pass TEAM for now (hybridSearch handles it)
      effectiveScope = 'TEAM';
    }

    const results = await hybridSearch(query, topK, mode, effectiveScope);

    // P1-5: token budget info
    const budget = calculateBudget({ query, topK });
    const maxTokens = budget.contextBudget;
    const usedTokens = budget.queryTokens + (results.reduce((acc, r) => acc + (r.memory?.text?.length || 0), 0) / 4);
    const remainingTokens = Math.max(0, maxTokens - usedTokens);
    const percentUsed = maxTokens > 0 ? Math.round((usedTokens / maxTokens) * 1000) / 10 : 0;
    const warning = percentUsed > 80 ? 'Token budget >80% utilized' : null;

    for (const r of results) {
      touchMemory(r.memory.id);
    }
    const duration = timer.end();
    recordSearchLatency(duration * 1000, mode);
    endTrace(span);
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: results.length,
          query,
          mode,
          scope: scope || null,
          results: results.map((r) => ({
            id: r.memory.id,
            text: r.memory.text,
            category: r.memory.category,
            importance: r.memory.importance,
            score: Math.round(r.fusionScore * 1000) / 1000,
            highlight: r.highlight,
            created_at: new Date(r.memory.created_at).toISOString(),
          })),
          token_budget: {
            used_tokens: Math.round(usedTokens),
            max_tokens: maxTokens,
            remaining_tokens: Math.round(remainingTokens),
            percent_used: percentUsed,
            warning,
          },
        }, null, 2),
      }],
    };
  } catch (err) {
    const duration = timer.end();
    recordSearchLatency(duration * 1000, mode);
    recordError('search');
    endTrace(span, { error: err.message }, 'error');
    structuredLog.error( `Search failed: ${err.message}`);
    return { content: [{ type: 'text', text: `Search error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_store', {
  description: 'Store a new memory with content, category, importance and tags. P0-1: WAL logging. P0-3: transcript logging. P1-6: auto-extracts structured facts when category=general and importance>0.7.',
  inputSchema: z.object({
    text: z.string().describe('Memory content (required)'),
    category: z.string().optional().default('general').describe('Category: preference, fact, decision, entity, reflection, or other'),
    importance: z.number().optional().default(0.5).describe('Importance score 0-1'),
    tags: z.array(z.string()).optional().default([]).describe('Tags for the memory'),
    scope: z.string().optional().describe('Scope: AGENT, USER, TEAM, GLOBAL (default GLOBAL)'),
    source: z.string().optional().default('manual').describe('Source of this store: manual, auto, extraction'),
  }),
}, async ({ text, category = 'general', importance = 0.5, tags = [], scope, source = 'manual' }) => {
  const span = startTrace('memory_store', { category });
    structuredLog.info( `Store: text="${text.slice(0, 50)}..." category=${category} source=${source}`);
  try {
    // P0-1: WAL logging before store
    logOp({ op: 'store', text: text.slice(0, 100), category, importance, scope, source, ts: Date.now() });

    // P0-3: transcript logging
    logTranscript('store', { text: text.slice(0, 200), category, importance, tags, scope, source });

    const mem = addMemory({ text, category, importance, tags, scope });
    recordStore(Buffer.byteLength(text, 'utf8'));

    // P1-6: Auto-extract when category=general and importance>0.7
    let autoExtracted = null;
    if (category === 'general' && importance > 0.7) {
      try {
        const extractor = new AutoExtractor();
        const extracted = await extractor.extractFromConversation(text, true);
        if (extracted && extracted.length > 0) {
          autoExtracted = extracted;
          // Store each extracted fact as a separate memory with extraction source
          for (const ex of extracted) {
            addMemory({
              text: ex.text,
              category: ex.category,
              importance: ex.importance,
              tags: ['auto-extracted', ...(ex.matched_keyword ? [ex.matched_keyword] : [])],
              scope,
              source: 'extraction',
            });
          }
        }
      } catch {
        // Auto-extract is best-effort; don't fail the store
      }
    }

    endTrace(span);
    const result = { success: true, id: mem.id };
    if (autoExtracted) {
      result.auto_extracted = autoExtracted.length;
    }
    return { content: [{ type: 'text', text: JSON.stringify(result) }] };
  } catch (err) {
    recordError('store');
    endTrace(span, { error: err.message }, 'error');
    structuredLog.error( `Store failed: ${err.message}`);
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
  description: 'Delete a memory by its ID. P0-1: WAL logged. P0-3: transcript logged.',
  inputSchema: z.object({
    id: z.string().describe('Memory ID to delete'),
  }),
}, async ({ id }) => {
  try {
    // P0-1: WAL logging before delete
    logOp({ op: 'delete', id, ts: Date.now() });
    // P0-3: transcript logging
    logTranscript('delete', { id });
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
    log.error(`Insights failed: ${err.message}`);
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
    log.error(`Export failed: ${err.message}`);
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
    log.error(`Dedup failed: ${err.message}`);
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
    log.error(`Decay failed: ${err.message}`);
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
    log.error(`QA failed: ${err.message}`);
    return { content: [{ type: 'text', text: `QA error: ${err.message}` }], isError: true };
  }
});

// ============ Preference Slots (v1.2) ============

server.registerTool('memory_preference_slots', {
  description: 'Structured user preference slots: get, update, merge, reset, or stats on preference key-value store. Used to personalise memory recall.',
  inputSchema: z.object({
    action: z.enum(['get', 'update', 'merge', 'delete', 'reset', 'stats']).describe('Action to perform'),
    key: z.string().optional().describe('Slot key (required for update/delete)'),
    value: z.unknown().optional().describe('Slot value (required for update)'),
    slots: z.record(z.string(), z.unknown()).optional().describe('Key-value map for merge action'),
  }),
}, async ({ action, key, value, slots }) => {
  try {
    return memoryPreferenceSlotsTool({ action, key, value, slots });
  } catch (err) {
    log.error(`Preference slots error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

// ============ Preference Slots Enhanced (Feature #10) ============

server.registerTool('memory_preference_get', {
  description: 'Get one or all preference slots with full metadata (value, confidence, source, lastUpdated).',
  inputSchema: z.object({
    key: z.string().optional().describe('Slot key to get (optional, returns all if not provided)'),
  }),
}, async ({ key }) => {
  try {
    return memoryPreferenceGetTool({ key });
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_preference_set', {
  description: 'Set a preference slot value with explicit source and confidence.',
  inputSchema: z.object({
    key: z.string().describe('Slot key to set'),
    value: z.unknown().describe('Value to set'),
    confidence: z.number().optional().describe('Confidence 0-1 (default 0.9)'),
    source: z.enum(['explicit', 'inferred', 'historical']).optional().describe('Source type (default explicit)'),
  }),
}, async ({ key, value, confidence, source }) => {
  try {
    return memoryPreferenceSetTool({ key, value, confidence, source });
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_preference_infer', {
  description: 'Infer preferences from recent conversation history using pattern analysis.',
  inputSchema: z.object({
    messageCount: z.number().optional().default(20).describe('Number of recent messages to analyze'),
  }),
}, async ({ messageCount }) => {
  try {
    return memoryPreferenceInferTool({ messageCount });
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_preference_explain', {
  description: 'Explain a preference slot: its source, confidence level, and how it was derived.',
  inputSchema: z.object({
    key: z.string().describe('Slot key to explain'),
  }),
}, async ({ key }) => {
  try {
    return memoryPreferenceExplainTool({ key });
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

// ============ Semantic Versioning (Feature #11) ============

server.registerTool('memory_version_list', {
  description: 'List version history for a memory or all memories with versions.',
  inputSchema: z.object({
    memoryId: z.string().optional().describe('Memory ID to list versions for'),
    limit: z.number().optional().default(10).describe('Max versions to return'),
    offset: z.number().optional().default(0).describe('Offset for pagination'),
    changeType: z.enum(['create', 'update', 'delete', 'rollback']).optional().describe('Filter by change type'),
  }),
}, async ({ memoryId, limit, offset, changeType }) => {
  try {
    return memoryVersionListTool({ memoryId, limit, offset, changeType });
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_version_diff', {
  description: 'Show diff between two versions of a memory or between adjacent versions.',
  inputSchema: z.object({
    memoryId: z.string().describe('Memory ID'),
    versionId1: z.string().optional().describe('First version ID (or compare with previous if only one)'),
    versionId2: z.string().optional().describe('Second version ID'),
  }),
}, async ({ memoryId, versionId1, versionId2 }) => {
  try {
    return memoryVersionDiffTool({ memoryId, versionId1, versionId2 });
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_version_restore', {
  description: 'Restore a memory to a specific version (v2.7.0). Set preview:true to preview without actually restoring. Use memory_version_list first to find versionId.',
  inputSchema: z.object({
    memoryId: z.string().describe('Memory ID to restore'),
    versionId: z.string().optional().describe('Version ID to restore to (latest if omitted)'),
    preview: z.boolean().optional().default(false).describe('Preview the restore without actually performing it'),
  }),
}, async ({ memoryId, versionId, preview }) => {
  try {
    return memoryVersionRestoreTool({ memoryId, versionId, preview });
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

// ============ Lesson System (v1.2) ============

server.registerTool('memory_lessons', {
  description: 'Lesson management: extract durable high-level principles from recurring memory recall patterns. Supports extract, recall, list, stats, delete.',
  inputSchema: z.object({
    action: z.enum(['extract', 'recall', 'list', 'stats', 'delete', 'touch', 'candidates']).describe('Action to perform'),
    memory_id: z.string().optional().describe('Source memory ID (for extract)'),
    title: z.string().optional().describe('Lesson title (for extract)'),
    body: z.string().optional().describe('Lesson body (for extract)'),
    tags: z.array(z.string()).optional().describe('Tags (for extract)'),
    query: z.string().optional().describe('Search query (for recall)'),
    lesson_id: z.string().optional().describe('Lesson ID (for delete/touch)'),
    limit: z.number().optional().describe('Max results (for list/recall)'),
    tag: z.string().optional().describe('Filter by tag (for list)'),
  }),
}, async (args) => {
  try {
    return memoryLessonsTool(args);
  } catch (err) {
    log.error(`Lesson system error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

// ============ AutoStore (v1.2) ============

server.registerTool('memory_autostore', {
  description: 'Auto-extract important information from conversation text and store as memories. Detects sensitive info and filters appropriately.',
  inputSchema: z.object({
    action: z.enum(['extract', 'stats']).describe('Action to perform'),
    text: z.string().optional().describe('Conversation text to extract from (for extract action)'),
  }),
}, async ({ action, text }) => {
  try {
    if (action === 'extract') {
      if (!text) {
        return { content: [{ type: 'text', text: 'Error: text is required for extract action' }], isError: true };
      }
      const extracted = extractImportantInfo(text);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            extracted: extracted.length,
            items: extracted.map(e => ({ text: e.text, category: e.category, source: e.source }))
          }, null, 2)
        }]
      };
    } else if (action === 'stats') {
      return {
        content: [{ type: 'text', text: JSON.stringify({ message: 'Autostore stats: extraction is rule-based, call extract action to process text' }, null, 2) }]
      };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Autostore error: ${err.message}`);
    return { content: [{ type: 'text', text: `Autostore error: ${err.message}` }], isError: true };
  }
});

// ============ Concurrent Search (v1.2) ============

server.registerTool('memory_concurrent_search', {
  description: 'Parallel BM25 + Vector + QMD hybrid search with multi-query support and timeout control.',
  inputSchema: z.object({
    action: z.enum(['search', 'multi', 'stats']).describe('Action to perform'),
    query: z.string().optional().describe('Search query (for search action)'),
    queries: z.array(z.string()).optional().describe('Multiple queries for parallel search (for search action)'),
    topK: z.number().optional().default(5).describe('Number of results to return'),
    text: z.string().optional().describe('Text to search (for multi action)'),
    tags: z.array(z.string()).optional().describe('Tags to filter by (for multi action)'),
    category: z.string().optional().describe('Category to filter by (for multi action)'),
  }),
}, async ({ action, query, queries, topK = 5, text, tags, category }) => {
  try {
    const searcher = new ConcurrentSearch();
    if (action === 'search') {
      const qList = queries || (query ? [query] : []);
      if (qList.length === 0) {
        return { content: [{ type: 'text', text: 'Error: query or queries is required' }], isError: true };
      }
      const results = await searcher.searchMultiple(qList, topK);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            count: results.length,
            results: results.slice(0, topK).map(r => ({
              id: r.memory?.id,
              text: (r.memory?.text || '').slice(0, 100),
              category: r.memory?.category,
              score: Math.round(r.score * 1000) / 1000,
              match_type: r.match_type
            }))
          }, null, 2)
        }]
      };
    } else if (action === 'multi') {
      if (!text) {
        return { content: [{ type: 'text', text: 'Error: text is required for multi action' }], isError: true };
      }
      const results = await searcher.multiSearch({ text, tags: tags || [], category }, topK);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            count: results.length,
            results: results.map(r => ({
              id: r.memory?.id,
              text: (r.memory?.text || '').slice(0, 100),
              score: Math.round(r.score * 1000) / 1000
            }))
          }, null, 2)
        }]
      };
    } else if (action === 'stats') {
      return { content: [{ type: 'text', text: JSON.stringify(searcher.getStats(), null, 2) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Concurrent search error: ${err.message}`);
    return { content: [{ type: 'text', text: `Concurrent search error: ${err.message}` }], isError: true };
  }
});

// ============ Predict (v1.2) ============

server.registerTool('memory_predict', {
  description: 'Predict user needs based on time patterns, behavior patterns, and project deadlines.',
  inputSchema: z.object({
    action: z.enum(['predict', 'patterns', 'trends', 'train', 'today', 'config']).describe('Action to perform'),
    topic: z.string().optional().describe('Topic for prediction (for predict action)'),
    json: z.boolean().optional().default(false).describe('Return JSON format'),
  }),
}, async ({ action, topic, json = false }) => {
  try {
    if (action === 'predict' || action === 'today') {
      const result = cmdPredict('today', { json });
      return { content: [{ type: 'text', text: result.type === 'json' ? JSON.stringify(result.data, null, 2) : result.text }] };
    } else if (action === 'patterns' || action === 'train') {
      const result = cmdPredict('train', { json });
      return { content: [{ type: 'text', text: result.type === 'json' ? JSON.stringify(result.data, null, 2) : result.text }] };
    } else if (action === 'trends') {
      const result = cmdPredict('week', { json });
      return { content: [{ type: 'text', text: result.text || result.error || 'Not implemented' }] };
    } else if (action === 'config') {
      const result = cmdPredict('config', { json });
      return { content: [{ type: 'text', text: result.type === 'json' ? JSON.stringify(result.data, null, 2) : result.text }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Predict error: ${err.message}`);
    return { content: [{ type: 'text', text: `Predict error: ${err.message}` }], isError: true };
  }
});

// ============ Recommend (v1.2) ============

server.registerTool('memory_recommend', {
  description: 'Smart memory recommendations based on vector similarity, co-occurrence, and tag correlation.',
  inputSchema: z.object({
    action: z.enum(['recommend', 'reason', 'hot', 'related']).describe('Action to perform'),
    context: z.string().optional().describe('Query/context for recommendation (for recommend action)'),
    id: z.string().optional().describe('Memory ID (for related action)'),
    k: z.number().optional().default(5).describe('Number of recommendations to return'),
    json: z.boolean().optional().default(false).describe('Return JSON format'),
  }),
}, async ({ action, context, id, k = 5, json = false }) => {
  try {
    if (action === 'recommend') {
      if (!context) {
        return { content: [{ type: 'text', text: 'Error: context is required for recommend action' }], isError: true };
      }
      const result = await cmdRecommend('recommend', { query: context, k: String(k), json });
      return { content: [{ type: 'text', text: result.type === 'json' ? JSON.stringify(result.data, null, 2) : result.text }] };
    } else if (action === 'reason') {
      return { content: [{ type: 'text', text: JSON.stringify({ explanation: 'Recommendations use vector similarity (50%), tag correlation (30%), and co-occurrence (20%) combined with importance weighting (30%)' }) }] };
    } else if (action === 'hot') {
      const result = await cmdRecommend('hot', { k: String(k), json });
      return { content: [{ type: 'text', text: result.type === 'json' ? JSON.stringify(result.data, null, 2) : result.text }] };
    } else if (action === 'related') {
      if (!id) {
        return { content: [{ type: 'text', text: 'Error: id is required for related action' }], isError: true };
      }
      const result = await cmdRecommend('related', { id, k: String(k), json });
      return { content: [{ type: 'text', text: result.type === 'json' ? JSON.stringify(result.data, null, 2) : result.text }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Recommend error: ${err.message}`);
    return { content: [{ type: 'text', text: `Recommend error: ${err.message}` }], isError: true };
  }
});

// ============ Inference (v1.2) ============

server.registerTool('memory_inference', {
  description: 'Joint inference combining vector search with ontology graph path expansion for enhanced memory retrieval.',
  inputSchema: z.object({
    action: z.enum(['infer', 'context', 'stats']).describe('Action to perform'),
    query: z.string().optional().describe('Query for inference (for infer action)'),
    entityId: z.string().optional().describe('Entity ID (for context action)'),
    limit: z.number().optional().default(10).describe('Max results (for infer action)'),
    depth: z.number().optional().default(2).describe('Graph traversal depth (for infer action)'),
    json: z.boolean().optional().default(false).describe('Return JSON format'),
  }),
}, async ({ action, query, entityId, limit = 10, depth = 2, json = false }) => {
  try {
    const inference = new MemoryInference();
    if (action === 'infer') {
      if (!query) {
        return { content: [{ type: 'text', text: 'Error: query is required for infer action' }], isError: true };
      }
      const result = await inference.inferRelated(query, limit, depth);
      return { content: [{ type: 'text', text: json ? JSON.stringify(result, null, 2) : JSON.stringify(result.merged?.slice(0, 5) || [], null, 2) }] };
    } else if (action === 'context') {
      if (!entityId) {
        return { content: [{ type: 'text', text: 'Error: entityId is required for context action' }], isError: true };
      }
      const chain = inference.getContextChain(entityId);
      return { content: [{ type: 'text', text: json ? JSON.stringify(chain, null, 2) : JSON.stringify(chain.slice(0, 10), null, 2) }] };
    } else if (action === 'stats') {
      const stats = inference.getStats();
      return { content: [{ type: 'text', text: JSON.stringify(stats, null, 2) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Inference error: ${err.message}`);
    return { content: [{ type: 'text', text: `Inference error: ${err.message}` }], isError: true };
  }
});

// ============ Summary (v1.2) ============

server.registerTool('memory_summary', {
  description: 'Generate memory summaries at different granularities using LLM or rule-based extraction.',
  inputSchema: z.object({
    action: z.enum(['summarize', 'stats']).describe('Action to perform'),
    text: z.string().optional().describe('Text to summarize (for summarize action)'),
    memoryId: z.string().optional().describe('Memory ID to summarize (for summarize action)'),
    style: z.enum(['short', 'medium', 'long']).optional().default('medium').describe('Summary style'),
  }),
}, async ({ action, text, memoryId, style = 'medium' }) => {
  try {
    const summarizer = new MemorySummarizer();
    if (action === 'summarize') {
      if (!text && !memoryId) {
        return { content: [{ type: 'text', text: 'Error: text or memoryId is required' }], isError: true };
      }
      let summary;
      if (memoryId) {
        summary = await summarizer.summarizeMemory(memoryId, style);
      } else {
        summary = await summarizer.generateSummary(text, style);
      }
      return { content: [{ type: 'text', text: JSON.stringify({ summary, style }, null, 2) }] };
    } else if (action === 'stats') {
      const cache = summarizer.cache || {};
      return { content: [{ type: 'text', text: JSON.stringify({ cached_summaries: Object.keys(cache.summaries || {}).length }, null, 2) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Summary error: ${err.message}`);
    return { content: [{ type: 'text', text: `Summary error: ${err.message}` }], isError: true };
  }
});

// ============ Feedback Learner (v1.2) ============

server.registerTool('memory_feedback', {
  description: 'Feedback learning闭环: record memory usage outcomes (helpful/irrelevant/wrong/outdated) and adjust importance accordingly.',
  inputSchema: z.object({
    action: z.enum(['record', 'recommendations', 'stats', 'learn']).describe('Action to perform'),
    memoryId: z.string().optional().describe('Memory ID to record feedback for'),
    outcome: z.enum(['helpful', 'irrelevant', 'wrong', 'outdated']).optional().describe('Outcome type (for record action)'),
    correction: z.string().optional().describe('Correction text (for learn action)'),
  }),
}, async ({ action, memoryId, outcome, correction }) => {
  try {
    const learner = new FeedbackLearner();
    if (action === 'record') {
      if (!memoryId || !outcome) {
        return { content: [{ type: 'text', text: 'Error: memoryId and outcome are required' }], isError: true };
      }
      const feedback = learner.track(memoryId, outcome);
      return { content: [{ type: 'text', text: JSON.stringify({ success: true, feedback }, null, 2) }] };
    } else if (action === 'recommendations') {
      const memories = getAllMemories();
      const adjustments = learner.adjustImportance(memories);
      const suggestions = learner.suggestForgetting(memories);
      return { content: [{ type: 'text', text: JSON.stringify({ adjustments: Object.keys(adjustments).length, forget_suggestions: suggestions.length }, null, 2) }] };
    } else if (action === 'stats') {
      const stats = learner.getFeedbackStats();
      return { content: [{ type: 'text', text: JSON.stringify(stats, null, 2) }] };
    } else if (action === 'learn') {
      if (!correction) {
        return { content: [{ type: 'text', text: 'Error: correction is required for learn action' }], isError: true };
      }
      const entry = learner.learn(correction);
      return { content: [{ type: 'text', text: JSON.stringify({ success: true, entry }, null, 2) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Feedback error: ${err.message}`);
    return { content: [{ type: 'text', text: `Feedback error: ${err.message}` }], isError: true };
  }
});

// ============ QMD Search (v1.2) ============

server.registerTool('memory_qmd_search', {
  description: 'QMD-style search using BM25 keyword matching with Ollama vector fallback.',
  inputSchema: z.object({
    action: z.enum(['search', 'status']).describe('Action to perform'),
    query: z.string().optional().describe('Search query (for search action)'),
    topK: z.number().optional().default(5).describe('Number of results to return'),
    mode: z.enum(['bm25', 'vector', 'hybrid', 'auto']).optional().default('hybrid').describe('Search mode'),
  }),
}, async ({ action, query, topK = 5, mode = 'hybrid' }) => {
  try {
    if (action === 'search') {
      if (!query) {
        return { content: [{ type: 'text', text: 'Error: query is required for search action' }], isError: true };
      }
      const results = await qmdSearch(query, { topK, mode });
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            count: results.length,
            query,
            mode,
            results: results.map(r => ({
              id: r.id,
              text: r.text,
              category: r.category,
              score: Math.round(r.score * 1000) / 1000,
              match_mode: r.mode
            }))
          }, null, 2)
        }]
      };
    } else if (action === 'status') {
      const { getQMDStatus } = await import('./tools/qmd_search.js');
      const status = await getQMDStatus();
      return { content: [{ type: 'text', text: JSON.stringify(status, null, 2) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`QMD search error: ${err.message}`);
    return { content: [{ type: 'text', text: `QMD search error: ${err.message}` }], isError: true };
  }
});

// ============ QMD File Access (v1.1) ============

server.registerTool('memory_qmd_get', {
  description: 'Get the content of a local file from QMD index. Use after memory_qmd_search finds relevant files.',
  inputSchema: z.object({
    path: z.string().describe('File path (from qmd_search results)'),
    maxLines: z.number().optional().default(100).describe('Max lines to return'),
    offset: z.number().optional().default(0).describe('Line offset to start from'),
  }),
}, async ({ path, maxLines = 100, offset = 0 }) => {
  try {
    const { qmdGet } = await import('./tools/qmd_search.js');
    const result = await qmdGet(path, { maxLines, offset });
    if (result.error) {
      return { content: [{ type: 'text', text: `Error: ${result.error}` }], isError: true };
    }
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          path: result.path,
          content: result.content,
          lines: result.lines,
          truncated: result.truncated,
          source: 'qmd',
        }, null, 2)
      }]
    };
  } catch (err) {
    log.error(`QMD get error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_qmd_vsearch', {
  description: 'Vector semantic search of local markdown files via QMD (requires pre-embedded files).',
  inputSchema: z.object({
    query: z.string().describe('Semantic search query'),
    topK: z.number().optional().default(5).describe('Number of results'),
  }),
}, async ({ query, topK = 5 }) => {
  try {
    const { qmdVSearch } = await import('./tools/qmd_search.js');
    const results = await qmdVSearch(query, { topK });
    if (results.error) {
      return { content: [{ type: 'text', text: `Error: ${results.error}` }], isError: true };
    }
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: results.length,
          query,
          mode: 'vector',
          results: results.map(r => ({
            id: r.id,
            path: r.path,
            title: r.title,
            score: Math.round(r.score * 1000) / 1000,
            snippet: r.snippet,
          }))
        }, null, 2)
      }]
    };
  } catch (err) {
    log.error(`QMD vsearch error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_qmd_list', {
  description: 'List indexed markdown files from QMD collection.',
  inputSchema: z.object({
    pattern: z.string().optional().describe('Glob pattern (e.g. **/*.md)'),
    limit: z.number().optional().default(20).describe('Max files to return'),
  }),
}, async ({ pattern = '**/*.md', limit = 20 }) => {
  try {
    const { qmdListFiles } = await import('./tools/qmd_search.js');
    const result = await qmdListFiles(pattern, limit);
    if (result.error) {
      return { content: [{ type: 'text', text: `Error: ${result.error}` }], isError: true };
    }
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: Array.isArray(result.files) ? result.files.length : result.length || 0,
          files: result.files || result || [],
          source: 'qmd',
        }, null, 2)
      }]
    };
  } catch (err) {
    log.error(`QMD list error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

// ============ Templates (v1.2) ============

server.registerTool('memory_templates', {
  description: 'Memory template system for structured memory creation (project, meeting, decision, preference, task, contact, learning).',
  inputSchema: z.object({
    action: z.enum(['list', 'generate', 'get']).describe('Action to perform'),
    command: z.string().optional().describe('Template type (for generate action)'),
    templateType: z.string().optional().describe('Template type to get (for get action)'),
    data: z.record(z.string(), z.unknown()).optional().describe('Template data (for generate action)'),
  }),
}, async ({ action, command, templateType, data }) => {
  try {
    if (action === 'list') {
      const result = cmdTemplates('list', { json: true });
      return { content: [{ type: 'text', text: JSON.stringify(result.data, null, 2) }] };
    } else if (action === 'get') {
      if (!templateType) {
        return { content: [{ type: 'text', text: 'Error: templateType is required for get action' }], isError: true };
      }
      const result = cmdTemplates('get', { type: templateType, json: true });
      return { content: [{ type: 'text', text: JSON.stringify(result.data || result.error, null, 2) }] };
    } else if (action === 'generate') {
      if (!command) {
        return { content: [{ type: 'text', text: 'Error: command (template type) is required for generate action' }], isError: true };
      }
      const result = cmdTemplates('fill', { type: command, data: data ? JSON.stringify(data) : '{}', json: true });
      return { content: [{ type: 'text', text: result.type === 'json' ? JSON.stringify(result.data, null, 2) : result.text }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Templates error: ${err.message}`);
    return { content: [{ type: 'text', text: `Templates error: ${err.message}` }], isError: true };
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

    // Category distribution (mapped to standard categories)
    const categoryMap = { fact: 0, decision: 0, preference: 0, reflection: 0, other: 0 };
    for (const m of memories) {
      const cat = m.category || 'other';
      if (cat === 'fact' || cat === 'entity') categoryMap.fact++;
      else if (cat === 'decision') categoryMap.decision++;
      else if (cat === 'preference') categoryMap.preference++;
      else if (cat === 'reflection') categoryMap.reflection++;
      else categoryMap.other++;
    }

    // Quality distribution (by importance score)
    const qualityMap = { high: 0, medium: 0, low: 0 };
    for (const m of memories) {
      const imp = m.importance || 0.5;
      if (imp > 0.6) qualityMap.high++;
      else if (imp >= 0.3) qualityMap.medium++;
      else qualityMap.low++;
    }

    // Tier distribution and size by tier
    const tierMap = { HOT: 0, WARM: 0, COLD: 0 };
    const sizeByTier = { HOT: 0, WARM: 0, COLD: 0 };
    const DAY_MS = 86400000;
    const now = Date.now();
    for (const m of memories) {
      const raw = m.timestamp || m.created_at || m.createdAt || now;
      const ts = typeof raw === 'string' ? new Date(raw).getTime() : raw;
      const ageDays = (now - ts) / DAY_MS;
      let tier;
      if (ageDays <= 7) tier = 'HOT';
      else if (ageDays <= 30) tier = 'WARM';
      else tier = 'COLD';
      tierMap[tier]++;
      const size = Buffer.byteLength(JSON.stringify(m), 'utf8');
      sizeByTier[tier] += size;
    }

    // Scope distribution
    const scopeMap = { USER: 0, TEAM: 0, AGENT: 0, GLOBAL: 0 };
    for (const m of memories) {
      const scope = (m.scope || 'GLOBAL').toUpperCase();
      if (scope in scopeMap) scopeMap[scope]++;
      else scopeMap.GLOBAL++;
    }

    // Read storage version from package.json
    let storageVersion = '2.0.0';
    try {
      const { readFileSync } = await import('fs');
      const pkgPath = new URL('../package.json', import.meta.url);
      const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
      storageVersion = pkg.version || '2.0.0';
    } catch { /* use default */ }

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          total: memories.length,
          categories,
          topTags: Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([tag, count]) => ({ tag, count })),
          // Enhanced fields (v2.0)
          category_distribution: categoryMap,
          quality_distribution: qualityMap,
          tier_distribution: tierMap,
          size_by_tier: sizeByTier,
          scope_distribution: scopeMap,
          memory_count: memories.length,
          storage_version: storageVersion,
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

    // WAL integrity check
    const walChecks = { status: 'ok', walRecordCount: 0, actualOpsCount: 0, discrepancy: 0, withinTolerance: true };
    try {
      const walFiles = listWalFiles();
      let totalWalRecords = 0;
      for (const wf of walFiles) {
        try {
          const content = await import('fs').then(fs => fs.readFileSync(new URL(`../wal/${wf}`, import.meta.url), 'utf8'));
          totalWalRecords += content.trim().split('\n').filter(Boolean).length;
        } catch { /* skip unreadable files */ }
      }
      walChecks.walRecordCount = totalWalRecords;
      walChecks.actualOpsCount = memories.length;
      walChecks.discrepancy = Math.abs(totalWalRecords - memories.length);
      walChecks.withinTolerance = memories.length === 0
        ? totalWalRecords === 0
        : (walChecks.discrepancy / memories.length) <= 0.05;
    } catch { walChecks.status = 'unknown'; }

    // Vector cache completeness (memories with embeddings)
    let vectorCount = 0;
    for (const m of memories) {
      if (m.embedding && Array.isArray(m.embedding) && m.embedding.length > 0) {
        vectorCount++;
      }
    }
    const vectorCompleteRate = memories.length > 0 ? Math.round((vectorCount / memories.length) * 1000) / 10 : 100;
    const vectorStatus = vectorCompleteRate >= 95 ? 'ok' : (vectorCompleteRate >= 50 ? 'degraded' : 'critical');

    // Tier distribution reasonableness
    const DAY_MS = 86400000;
    const now = Date.now();
    const tierCounts = { HOT: 0, WARM: 0, COLD: 0 };
    for (const m of memories) {
      const raw = m.timestamp || m.created_at || m.createdAt || now;
      const ts = typeof raw === 'string' ? new Date(raw).getTime() : raw;
      const ageDays = (now - ts) / DAY_MS;
      if (ageDays <= 7) tierCounts.HOT++;
      else if (ageDays <= 30) tierCounts.WARM++;
      else tierCounts.COLD++;
    }
    const totalMemories = memories.length || 1;
    const coldRatio = tierCounts.COLD / totalMemories;
    const hotRatio = tierCounts.HOT / totalMemories;
    const tierWarnings = [];
    if (coldRatio > 0.8) tierWarnings.push({ level: 'warning', message: `COLD tier占比${Math.round(coldRatio * 100)}% > 80%，分级可能有问题` });
    if (hotRatio > 0.8) tierWarnings.push({ level: 'warning', message: `HOT tier占比${Math.round(hotRatio * 100)}% > 80%，没有正常衰减` });

    // Long-time-no-access memories (>30 days)
    const staleMemories = [];
    const thirtyDaysAgo = now - 30 * DAY_MS;
    for (const m of memories) {
      const lastAcc = m.last_access || m.lastAccess || m.timestamp || m.created_at || m.createdAt || now;
      const accTs = typeof lastAcc === 'string' ? new Date(lastAcc).getTime() : lastAcc;
      if (accTs < thirtyDaysAgo) {
        staleMemories.push({ id: m.id, last_access: new Date(accTs).toISOString() });
        if (staleMemories.length >= 10) break;
      }
    }

    // Corrupted memory detection
    const corruptedMemories = [];
    const requiredFields = ['id', 'text', 'category'];
    for (const m of memories) {
      let isCorrupted = false;
      try {
        // JSON parse check (already parsed by getAllMemories, so we check structural validity)
        if (!m.id || typeof m.text !== 'string' || !m.category) {
          isCorrupted = true;
        }
        // Check for essential numeric fields being valid
        if (m.importance !== undefined && (typeof m.importance !== 'number' || m.importance < 0 || m.importance > 1)) {
          isCorrupted = true;
        }
      } catch {
        isCorrupted = true;
      }
      if (isCorrupted) {
        corruptedMemories.push({ id: m.id || 'unknown', reason: 'missing required fields or invalid structure' });
      }
    }

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
          // Enhanced health checks (v2.0)
          wal_integrity: walChecks,
          vector_cache_complete_rate: `${vectorCompleteRate}%`,
          vector_cache_status: vectorStatus,
          tier_distribution: {
            HOT: tierCounts.HOT,
            WARM: tierCounts.WARM,
            COLD: tierCounts.COLD,
            warnings: tierWarnings,
          },
          stale_memories: staleMemories,
          corrupted_memories: corruptedMemories,
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Health error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_metrics', {
  description: 'View operational metrics: search latency, store counts, error rates.',
  inputSchema: z.object({}),
  handler: async () => {
    const m = metrics.collect();
    const trace = getTraceExport();
    return { content: [{ type: 'text', text: JSON.stringify({ metrics: m, trace }, null, 2) }] };
  }
});

server.registerTool('memory_trace', {
  description: 'Export recent trace spans for debugging.',
  inputSchema: z.object({ clear: z.boolean().default(false) }),
  handler: async ({ clear }) => {
    const t = getTraceExport();
    if (clear) clearTrace();
    return { content: [{ type: 'text', text: JSON.stringify(t, null, 2) }] };
  }
});

// ============ Extended Search & Processing ============

server.registerTool('memory_noise', {
  description: 'Manage noise filtering and quality scoring for memories. Learn noise patterns, check if text should be stored, and get quality scores.',
  inputSchema: z.object({
    action: z.enum(['should_store', 'quality', 'learn', 'stats', 'clear']).describe('Action: should_store=text to check, quality=score memories, learn=add noise pattern, stats=noise count, clear=reset learned'),
    text: z.string().optional().describe('Text content for should_store or learn actions'),
    memories: z.array(z.object({ id: z.string(), content: z.string() })).optional().describe('Memories to score (for quality action)'),
  }),
}, async ({ action, text, memories }) => {
  try {
    if (action === 'should_store') {
      const result = shouldStore(text || '', {});
      return { content: [{ type: 'text', text: JSON.stringify({ should_store: result }) }] };
    }
    if (action === 'quality') {
      const scores = (memories || []).map(m => ({ id: m.id, score: qualityScore(m) }));
      return { content: [{ type: 'text', text: JSON.stringify({ scores }) }] };
    }
    if (action === 'learn') {
      learnNoisePattern(text || '');
      return { content: [{ type: 'text', text: 'Noise pattern learned' }] };
    }
    if (action === 'stats') {
      return { content: [{ type: 'text', text: JSON.stringify({ noise_count: getNoiseCount() }) }] };
    }
    if (action === 'clear') {
      const { clearLearnedNoise } = await import('./noise.js');
      clearLearnedNoise();
      return { content: [{ type: 'text', text: 'Learned noise patterns cleared' }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Noise error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_intent', {
  description: 'Route a search query to determine intent type (FACT, PREFERENCE, RECENT, PROJECT, etc.). Returns null to skip retrieval for non-retrieval queries.',
  inputSchema: z.object({
    query: z.string().describe('The search query to classify'),
  }),
}, async ({ query }) => {
  try {
    const intent = routeSearch(query);
    const type = intent?.type || 'UNKNOWN';
    const skip = intent === null;
    return { content: [{ type: 'text', text: JSON.stringify({ intent_type: type, skip_retrieval: skip, intent }) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Intent error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_extract', {
  description: 'Extract structured memories from raw text using LLM. Supports batch extraction with progress callbacks.',
  inputSchema: z.object({
    texts: z.array(z.string()).describe('Texts to extract memories from'),
    batch: z.boolean().default(false).describe('Use batch extraction with progress'),
    onProgress: z.boolean().default(false).describe('Report progress per text'),
  }),
}, async ({ texts, batch, onProgress }) => {
  try {
    const { default: llmCall } = await import('./config.js');
    if (batch) {
      const results = await batchExtract(texts, async (p) => { if (onProgress) process.stderr.write(`[extract] ${p}\n`); }, llmCall);
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    } else {
      const results = await Promise.all(texts.map(t => extractMemories(t, llmCall)));
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    }
  } catch (err) {
    return { content: [{ type: 'text', text: `Extract error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_reflection', {
  description: 'Self-improvement system: track learnings, errors, and patterns. Store lessons from operations and retrieve them.',
  inputSchema: z.object({
    action: z.enum(['learn', 'error', 'get', 'stats']).describe('Action: learn=add learning, error=log error, get=retrieve all, stats=summary'),
    text: z.string().optional().describe('Content for learn or error'),
    category: z.string().default('general').describe('Category for learn action'),
    errorType: z.string().default('unknown').describe('Error type for error action'),
  }),
}, async ({ action, text, category, errorType }) => {
  try {
    if (action === 'learn') {
      addLearning(text || '', category || 'general');
      return { content: [{ type: 'text', text: 'Learning added' }] };
    }
    if (action === 'error') {
      addError(text || '', errorType || 'unknown');
      return { content: [{ type: 'text', text: 'Error logged' }] };
    }
    if (action === 'get') {
      return { content: [{ type: 'text', text: JSON.stringify({ learnings: getLearnings(), errors: getErrors() }) }] };
    }
    if (action === 'stats') {
      return { content: [{ type: 'text', text: JSON.stringify(getStats()) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Reflection error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_wal', {
  description: 'Write-Ahead Log operations for crash recovery. Initialize WAL, flush pending ops, or list WAL files.',
  inputSchema: z.object({
    action: z.enum(['init', 'flush', 'list']).describe('Action: init=create new WAL, flush=flush pending ops, list=list WAL files'),
    runId: z.string().optional().describe('Run ID for init'),
  }),
}, async ({ action, runId }) => {
  try {
    if (action === 'init') {
      initWal(runId || `run-${Date.now()}`);
      return { content: [{ type: 'text', text: 'WAL initialized' }] };
    }
    if (action === 'flush') {
      const count = flushWal();
      return { content: [{ type: 'text', text: `Flushed ${count} operations` }] };
    }
    if (action === 'list') {
      return { content: [{ type: 'text', text: JSON.stringify(listWalFiles()) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `WAL error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_tier', {
  description: 'HOT/WARM/COLD tier management. Automatically partition memories into temperature tiers, redistribute, or compress cold tier.',
  inputSchema: z.object({
    action: z.enum(['assign', 'partition', 'redistribute', 'compress']).describe('Action: assign=assign tiers to all, partition=split by tier, redistribute=full rebalance, compress=compact cold tier'),
    memories: z.array(z.object({ id: z.string(), content: z.string(), accessedAt: z.number(), importance: z.number().optional() })).optional().describe('Memories to process (for assign/partition/compress)'),
  }),
}, async ({ action, memories }) => {
  try {
    if (action === 'assign') {
      const result = assignTiers(memories || []);
      return { content: [{ type: 'text', text: JSON.stringify(result) }] };
    }
    if (action === 'partition') {
      const result = partitionByTier(memories || []);
      return { content: [{ type: 'text', text: JSON.stringify(result) }] };
    }
    if (action === 'redistribute') {
      const result = redistributeTiers(memories || []);
      return { content: [{ type: 'text', text: JSON.stringify(result) }] };
    }
    if (action === 'compress') {
      const cold = (memories || []).filter(m => m.tier === 'COLD');
      const result = compressColdTier(cold);
      return { content: [{ type: 'text', text: JSON.stringify(result) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Tier error: ${err.message}` }], isError: true };
  }
});

// ============ Tier Management Tools (v2.7.0) ============

server.registerTool('memory_tier_status', {
  description: 'View tier statistics: memory count, size, and recent access stats per tier (HOT/WARM/COLD). Shows distribution, tier config, and per-tier details.',
  inputSchema: z.object({}),
}, async () => {
  try {
    return memoryTierStatusTool();
  } catch (err) {
    structuredLog.error(`memory_tier_status error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_tier_migrate', {
  description: 'Manually trigger automatic tier migration. Uses access frequency and importance heuristics to promote or demote memories between HOT/WARM/COLD tiers. Supports dry-run mode.',
  inputSchema: z.object({
    apply: z.boolean().optional().default(false).describe('If true, apply changes to storage; if false (default), only preview'),
  }),
}, async ({ apply }) => {
  try {
    return memoryTierMigrateTool({ apply });
  } catch (err) {
    structuredLog.error(`memory_tier_migrate error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_tier_compress', {
  description: 'Compress COLD tier memories to reduce storage. Truncates text to 200 chars, drops embeddings and access metadata. Supports dry-run mode.',
  inputSchema: z.object({
    apply: z.boolean().optional().default(false).describe('If true, apply compression to storage; if false (default), only preview'),
  }),
}, async ({ apply }) => {
  try {
    return memoryTierCompressTool({ apply });
  } catch (err) {
    structuredLog.error(`memory_tier_compress error: ${err.message}`);
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_adaptive', {
  description: 'Adaptive retrieval control. Check if a query should skip vector search (non-informational queries like greetings).',
  inputSchema: z.object({
    query: z.string().describe('Query to check for adaptive skip'),
  }),
}, async ({ query }) => {
  try {
    const skip = shouldSkipRetrieval(query);
    return { content: [{ type: 'text', text: JSON.stringify({ skip_retrieval: skip }) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Adaptive error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_bm25', {
  description: 'BM25 keyword-based search. Build index and search using Okapi BM25 algorithm (pure keyword, no embedding required).',
  inputSchema: z.object({
    query: z.string().describe('Query string'),
    topK: z.number().default(10).describe('Number of results'),
    build: z.boolean().default(false).describe('Rebuild the BM25 index first'),
  }),
}, async ({ query, topK, build }) => {
  try {
    if (build) buildBM25Index();
    const results = bm25Search(query, topK);
    return { content: [{ type: 'text', text: JSON.stringify(results) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `BM25 error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_vector', {
  description: 'Dense vector semantic search using Ollama embeddings. Get embedding for text or search by semantic similarity. Supports scope filtering for multi-tenant isolation.',
  inputSchema: z.object({
    action: z.enum(['embed', 'search']).describe('Action: embed=get vector for text, search=semantic similarity search'),
    text: z.string().optional().describe('Text to embed (for embed action)'),
    query: z.string().optional().describe('Query for search (for search action)'),
    topK: z.number().default(10).describe('Number of results for search'),
    scope: z.string().optional().describe('Scope filter: AGENT, USER, TEAM, GLOBAL (only for search action)'),
  }),
}, async ({ action, text, query, topK, scope }) => {
  try {
    if (action === 'embed') {
      const embedding = await getEmbedding(text || '');
      return { content: [{ type: 'text', text: JSON.stringify({ embedding, dimensions: embedding.length }) }] };
    }
    if (action === 'search') {
      const results = await vectorSearch(query || '', topK || 10, scope || null);
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Vector error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_mmr', {
  description: 'Maximal Marginal Relevance diversity selection. Select diverse top-K results to reduce redundancy from BM25 or vector search.',
  inputSchema: z.object({
    documents: z.array(z.object({ id: z.string(), content: z.string(), score: z.number().optional() })).describe('Documents with scores'),
    topK: z.number().default(5).describe('Number of diverse results to return'),
    lambda: z.number().default(0.5).describe('Balance parameter (0= max diversity, 1= max relevance)'),
    useEmbedding: z.boolean().default(false).describe('Use embedding-based MMR (slower but accurate)'),
  }),
}, async ({ documents, topK, lambda, useEmbedding }) => {
  try {
    if (useEmbedding) {
      const { getEmbedding: ge } = await import('./vector.js');
      const results = await mmrSelectWithEmbedding(documents, topK, lambda, ge);
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    } else {
      const results = mmrSelect(documents, topK, lambda);
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    }
  } catch (err) {
    return { content: [{ type: 'text', text: `MMR error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_scope', {
  description: 'Filter and manage memory scope levels (AGENT, USER, TEAM, GLOBAL). Normalize scope strings and filter memories by scope.',
  inputSchema: z.object({
    action: z.enum(['normalize', 'filter', 'levels']).describe('Action: normalize=normalize scope string, filter=filter memories by scope, levels=list all levels'),
    scope: z.string().optional().describe('Scope value (for normalize/filter)'),
    memories: z.array(z.object({ id: z.string(), scope: z.string() })).optional().describe('Memories to filter (for filter action)'),
  }),
}, async ({ action, scope, memories }) => {
  try {
    if (action === 'normalize') {
      return { content: [{ type: 'text', text: JSON.stringify({ normalized: normalizeScope(scope || 'GLOBAL') }) }] };
    }
    if (action === 'filter') {
      const filtered = filterByScope(memories || [], scope || 'GLOBAL');
      return { content: [{ type: 'text', text: JSON.stringify({ filtered }) }] };
    }
    if (action === 'levels') {
      return { content: [{ type: 'text', text: JSON.stringify({ levels: SCOPE_LEVELS, hierarchy: SCOPE_HIERARCHY }) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Scope error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_rerank_llm', {
  description: 'LLM-based result reranking using cross-encoder or keyword matching. Rerank results from BM25/vector search for better relevance.',
  inputSchema: z.object({
    query: z.string().describe('Original query'),
    documents: z.array(z.object({ id: z.string(), content: z.string(), score: z.number().optional() })).describe('Documents to rerank'),
    topK: z.number().default(10).describe('Return top-K after reranking'),
    method: z.enum(['keyword', 'llm', 'cross']).default('keyword').describe('Reranking method'),
  }),
}, async ({ query, documents, topK, method }) => {
  try {
    if (method === 'keyword') {
      const results = keywordRerank(query, documents, topK);
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    }
    if (method === 'llm') {
      const reranker = new LlmReranker();
      const results = await reranker.rerank(query, documents, topK);
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    }
    if (method === 'cross') {
      const reranker = new CrossEncoderRerank();
      const results = await rerankResults(query, documents, topK, reranker);
      return { content: [{ type: 'text', text: JSON.stringify(results) }] };
    }
    return { content: [{ type: 'text', text: 'Unknown method' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Rerank error: ${err.message}` }], isError: true };
  }
});

// ============ Proactive Memory Tools (v1.2) ============

server.registerTool('memory_proactive_status', {
  description: 'Check proactive memory system status: running state, recent predictions, care alerts.',
  inputSchema: z.object({}),
}, async () => {
  try {
    const m = getProactiveManager();
    return { content: [{ type: 'text', text: JSON.stringify(m.getStatus(), null, 2) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Proactive status error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_proactive_trigger', {
  description: 'Manually trigger a proactive memory tick (run care checks + recall predictions).',
  inputSchema: z.object({}),
}, async () => {
  try {
    const m = getProactiveManager();
    const result = await m.trigger();
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Proactive trigger error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_proactive_start', {
  description: 'Start the proactive memory background manager (auto care checks every N minutes).',
  inputSchema: z.object({
    intervalMinutes: z.number().optional().default(5).describe('Check interval in minutes (default 5)'),
  }),
}, async ({ intervalMinutes = 5 }) => {
  try {
    const m = getProactiveManager();
    if (m.timer) {
      return { content: [{ type: 'text', text: 'Already running' }] };
    }
    m.intervalMs = intervalMinutes * 60000;
    m.start();
    return { content: [{ type: 'text', text: `Started with ${intervalMinutes}min interval` }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Proactive start error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_proactive_stop', {
  description: 'Stop the proactive memory background manager.',
  inputSchema: z.object({}),
}, async () => {
  try {
    const m = getProactiveManager();
    m.stop();
    return { content: [{ type: 'text', text: 'Stopped' }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Proactive stop error: ${err.message}` }], isError: true };
  }
});

// ============ Proactive Care & Recall (v1.2 - wired from core stubs) ============

// Import the proactive care check function
import { runCheck as runProactiveCareCheck } from './core/proactive_care.js';
import { predictRecall as corePredictRecall, printRecallReport } from './core/proactive_recall.js';

server.registerTool('memory_proactive_care', {
  description: 'Proactive care: detect Liu总 status changes and send caring messages. Checks meeting density, continuous work, negative keywords, and deadline pressure.',
  inputSchema: z.object({
    action: z.enum(['check', 'config', 'enable', 'disable', 'cache', 'test']).describe('Action to perform'),
    text: z.string().optional().describe('Text to test for negative keywords (for test action)'),
  }),
}, async ({ action, text }) => {
  try {
    if (action === 'check') {
      const results = await runProactiveCareCheck();
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            care_alerts: results.length,
            alerts: results.map(r => ({
              type: r.type,
              message: r.message,
              count: r.count,
              hours: r.hours,
            }))
          }, null, 2)
        }]
      };
    } else if (action === 'config') {
      const { loadConfig } = await import('./core/proactive_care.js');
      const config = await loadConfig();
      return { content: [{ type: 'text', text: JSON.stringify(config, null, 2) }] };
    } else if (action === 'enable') {
      const { loadConfig, saveConfig } = await import('./core/proactive_care.js');
      const config = await loadConfig();
      config.enabled = true;
      await saveConfig(config);
      return { content: [{ type: 'text', text: 'Proactive care enabled' }] };
    } else if (action === 'disable') {
      const { loadConfig, saveConfig } = await import('./core/proactive_care.js');
      const config = await loadConfig();
      config.enabled = false;
      await saveConfig(config);
      return { content: [{ type: 'text', text: 'Proactive care disabled' }] };
    } else if (action === 'cache') {
      const { saveCache } = await import('./core/proactive_care.js');
      await saveCache({ meetings: [], messages: [], tasks: [], timestamp: null });
      return { content: [{ type: 'text', text: 'Cache cleared' }] };
    } else if (action === 'test') {
      if (!text) {
        return { content: [{ type: 'text', text: 'Error: text is required for test action' }], isError: true };
      }
      const { loadConfig } = await import('./core/proactive_care.js');
      const config = await loadConfig();
      const keywords = config.rules?.negative_keywords?.keywords || [];
      const matched = keywords.filter(kw => (text || '').includes(kw));
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            text,
            matched_keywords: matched,
            detected: matched.length > 0,
          }, null, 2)
        }]
      };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    log.error(`Proactive care error: ${err.message}`);
    return { content: [{ type: 'text', text: `Proactive care error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_proactive_recall', {
  description: 'Predict which memories to proactively recall based on current context. Uses keyword matching and importance scoring.',
  inputSchema: z.object({
    action: z.enum(['predict', 'report']).describe('Action: predict=run prediction, report=print human-readable report'),
    context: z.string().optional().describe('Context string to match memories against (for predict action)'),
    topK: z.number().optional().default(10).describe('Number of predictions to return'),
  }),
}, async ({ action, context, topK = 10 }) => {
  try {
    if (action === 'report') {
      // Print human-readable report to console, return confirmation
      printRecallReport(context || undefined);
      return { content: [{ type: 'text', text: 'Report printed to stdout' }] };
    }
    // Default: predict
    const predictions = corePredictRecall(context || 'recent');
    const top = predictions.slice(0, topK);
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          context: context || 'time-based',
          predictions: top.map(p => ({
            id: p.memory?.id,
            text: (p.memory?.text || '').slice(0, 100),
            category: p.memory?.category,
            importance: p.memory?.importance,
            relevance: Math.round(p.relevance * 1000) / 1000,
            reason: p.reason,
          }))
        }, null, 2)
      }]
    };
  } catch (err) {
    log.error(`Proactive recall error: ${err.message}`);
    return { content: [{ type: 'text', text: `Proactive recall error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_reminder_add', {
  description: 'Add a reminder: one-time or recurring. Reminders are checked every 30 seconds.',
  inputSchema: z.object({
    text: z.string().describe('Reminder text'),
    type: z.enum(['once', 'recurring']).default('once').describe('Reminder type'),
    hours: z.number().optional().default(24).describe('Hours until reminder (default 24)'),
  }),
}, async ({ text, type = 'once', hours = 24 }) => {
  try {
    const scheduler = getReminderScheduler();
    let id;
    if (type === 'recurring') {
      id = scheduler.addRecurringReminder(text, hours);
    } else {
      id = scheduler.add({ type: 'once', text, dueAt: Date.now() + hours * 3600 * 1000, repeat: null });
    }
    return { content: [{ type: 'text', text: JSON.stringify({ success: true, id }) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Reminder add error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_reminder_list', {
  description: 'List all active reminders.',
  inputSchema: z.object({}),
}, async () => {
  try {
    const scheduler = getReminderScheduler();
    const reminders = scheduler.list();
    return { content: [{ type: 'text', text: JSON.stringify({ count: reminders.length, reminders }, null, 2) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Reminder list error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_reminder_cancel', {
  description: 'Cancel a reminder by ID.',
  inputSchema: z.object({
    id: z.string().describe('Reminder ID to cancel'),
  }),
}, async ({ id }) => {
  try {
    const scheduler = getReminderScheduler();
    const removed = scheduler.cancel(id);
    return { content: [{ type: 'text', text: JSON.stringify({ success: removed }) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Reminder cancel error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_predict_enhanced', {
  description: 'Enhanced prediction with time-awareness, TTL warnings, and importance scoring. Includes anniversary and high-value memory predictions.',
  inputSchema: z.object({
    action: z.enum(['predict', 'related', 'high_value']).describe('Action to perform'),
    context: z.string().optional().describe('Context for prediction (for predict action)'),
    memoryId: z.string().optional().describe('Memory ID for related predictions (for related action)'),
    topK: z.number().optional().default(5).describe('Number of predictions to return'),
  }),
}, async ({ action, context, memoryId, topK = 5 }) => {
  try {
    if (action === 'predict') {
      const results = await enhancedPredictRecall(context || '', { topK, includeTTL: true });
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            count: results.length,
            predictions: results.map(r => ({
              id: r.memory.id,
              text: r.memory.text,
              relevance: Math.round(r.relevance * 1000) / 1000,
              reasons: r.reasons,
              type: r.type,
            }))
          }, null, 2)
        }]
      };
    } else if (action === 'related') {
      if (!memoryId) {
        return { content: [{ type: 'text', text: 'Error: memoryId required for related action' }], isError: true };
      }
      const results = predictRelatedOnAccess(memoryId, topK);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            count: results.length,
            predictions: results.map(r => ({
              id: r.memory.id,
              text: r.memory.text,
              relevance: Math.round(r.relevance * 1000) / 1000,
              reasons: r.reasons,
            }))
          }, null, 2)
        }]
      };
    } else if (action === 'high_value') {
      const results = predictHighValueMemories(topK);
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            count: results.length,
            predictions: results.map(r => ({
              id: r.memory.id,
              text: r.memory.text,
              score: Math.round(r.score * 1000) / 1000,
              reasons: r.reasons,
            }))
          }, null, 2)
        }]
      };
    }
    return { content: [{ type: 'text', text: 'Unknown action' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Enhanced predict error: ${err.message}` }], isError: true };
  }
});


// ============ Knowledge Graph Tools (Entity + Relation Extraction) ============

import { extractEntities } from './graph/entity.js';
import { extractRelations } from './graph/relation.js';
import {
  loadGraph,
  addEntity,
  addRelation,
  findEntity,
  findEntityById,
  getNeighbors,
  queryGraph,
  getGraphStats,
  mergeIntoGraph,
  clearGraph,
} from './graph/graph_store.js';

server.registerTool('memory_graph_entity', {
  description: 'Extract entities (person/org/project/tool) from text or memories. Builds knowledge graph.',
  inputSchema: z.object({
    source: z.enum(['text', 'memory', 'all']).default('all').describe('Source to extract from'),
    text: z.string().optional().describe('Text to extract from (for text source)'),
    memoryId: z.string().optional().describe('Memory ID (for memory source)'),
    useLLM: z.boolean().optional().default(false).describe('Use LLM for enhanced extraction'),
  }),
}, async ({ source, text, memoryId, useLLM = false }) => {
  try {
    let textsToProcess = [];

    if (source === 'text' && text) {
      textsToProcess = [{ id: 'inline', text }];
    } else if (source === 'memory' && memoryId) {
      const mem = getMemory(memoryId);
      if (!mem) {
        return { content: [{ type: 'text', text: `Memory not found: ${memoryId}` }], isError: true };
      }
      textsToProcess = [mem];
    } else if (source === 'all') {
      const memories = getAllMemories();
      textsToProcess = memories.map(m => ({ id: m.id, text: m.text }));
    }

    if (textsToProcess.length === 0) {
      return { content: [{ type: 'text', text: JSON.stringify({ entities: [], count: 0 }) }] };
    }

    /** @type {Array<{ id: string, name: string, type: string, method: string, memory_ids: string[] }>} */
    const allEntities = [];

    for (const item of textsToProcess) {
      if (!item.text?.trim()) continue;
      try {
        const entities = await extractEntities(item.text, { useLLM });
        for (const e of entities) {
          const existing = allEntities.find(n => n.name === e.name && n.type === e.type);
          if (existing) {
            existing.memory_ids.push(item.id);
          } else {
            allEntities.push({ ...e, memory_ids: [item.id] });
          }
        }
      } catch {
        // Skip on error
      }
    }

    // Add entities to graph store
    for (const e of allEntities) {
      addEntity(e);
    }

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: allEntities.length,
          entities: allEntities.map(e => ({
            id: e.id,
            name: e.name,
            type: e.type,
            method: e.method,
            memory_ids: e.memory_ids.slice(0, 5),
          })),
          stats: getGraphStats(),
        }, null, 2),
      }],
    };
  } catch (err) {
    structuredLog.error(`memory_graph_entity error: ${err.message}`);
    return { content: [{ type: 'text', text: `Entity extraction error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_graph_relation', {
  description: 'Extract relationships between entities in the knowledge graph.',
  inputSchema: z.object({
    text: z.string().optional().describe('Text to extract relations from'),
    memoryId: z.string().optional().describe('Memory ID to extract from'),
    entityIds: z.array(z.string()).optional().describe('Entity IDs to find relations between'),
    useLLM: z.boolean().optional().default(false).describe('Use LLM for relation extraction'),
  }),
}, async ({ text, memoryId, entityIds, useLLM = false }) => {
  try {
    let sourceText = '';

    if (memoryId) {
      const mem = getMemory(memoryId);
      if (!mem) {
        return { content: [{ type: 'text', text: `Memory not found: ${memoryId}` }], isError: true };
      }
      sourceText = mem.text;
    } else if (text) {
      sourceText = text;
    } else {
      return { content: [{ type: 'text', text: 'Error: text or memoryId is required' }], isError: true };
    }

    // Get entities from the source text
    const entities = await extractEntities(sourceText, { useLLM });

    // Extract relations between entities in the text
    const relations = await extractRelations(sourceText, entities, {});

    // Add to graph store
    for (const r of relations) {
      addRelation(r);
    }

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: relations.length,
          relations: relations.map(r => ({
            id: r.id,
            from: r.from,
            to: r.to,
            relation: r.relation,
            confidence: r.confidence,
            source: r.source,
          })),
          entities_found: entities.map(e => ({ id: e.id, name: e.name, type: e.type })),
        }, null, 2),
      }],
    };
  } catch (err) {
    structuredLog.error(`memory_graph_relation error: ${err.message}`);
    return { content: [{ type: 'text', text: `Relation extraction error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_graph_query', {
  description: 'Query the knowledge graph: find entity neighbors, paths, or related entities.',
  inputSchema: z.object({
    entity: z.string().describe('Entity name or ID'),
    depth: z.number().default(1).describe('Query depth'),
    relationType: z.string().optional().describe('Filter by relation type'),
  }),
}, async ({ entity, depth = 1, relationType }) => {
  try {
    const graph = loadGraph();

    // Try to find entity by name or ID
    let entityObj = graph.entities.find(e => e.id === entity || e.name === entity);

    if (!entityObj) {
      return {
        content: [{
          type: 'text',
          text: JSON.stringify({
            error: `Entity not found: ${entity}`,
            available_entities: graph.entities.slice(0, 20).map(e => ({ id: e.id, name: e.name, type: e.type })),
          }, null, 2),
        }],
      };
    }

    // Get neighbors
    const neighbors = getNeighbors(entityObj.id, relationType || null);

    // Query paths
    const pathResult = queryGraph(entity, relationType, depth);

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          entity: { id: entityObj.id, name: entityObj.name, type: entityObj.type, count: entityObj.count },
          neighbors: neighbors.map(n => ({ id: n.entity.id, name: n.entity.name, type: n.entity.type, relation: n.relation, weight: n.weight })),
          paths: (pathResult?.paths || []).map(p => ({
            path: p.path,
            relations: p.relations,
            weight: p.totalWeight,
          })),
          stats: getGraphStats(),
        }, null, 2),
      }],
    };
  } catch (err) {
    structuredLog.error(`memory_graph_query error: ${err.message}`);
    return { content: [{ type: 'text', text: `Graph query error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_graph_stats', {
  description: 'Get knowledge graph statistics: entity counts, relation types, graph density.',
  inputSchema: z.object({}),
}, async () => {
  try {
    const stats = getGraphStats();
    const graph = loadGraph();

    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          ...stats,
          sample_entities: graph.entities.slice(0, 10).map(e => ({ id: e.id, name: e.name, type: e.type })),
          sample_relations: graph.relations.slice(0, 10).map(r => ({ id: r.id, from: r.from, to: r.to, relation: r.relation })),
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Graph stats error: ${err.message}` }], isError: true };
  }
});


// ============ Graph Add / Delete (v1.1) ============

server.registerTool('memory_graph_add', {
  description: 'Add a new entity or relation to the knowledge graph manually.',
  inputSchema: z.object({
    entity: z.object({
      name: z.string().describe('Entity name'),
      type: z.enum(['person', 'organization', 'project', 'topic', 'tool', 'location', 'date', 'event', 'other']).describe('Entity type'),
      description: z.string().optional().describe('Optional description'),
    }).optional().describe('Entity to add'),
    relation: z.object({
      from: z.string().describe('Source entity name or ID'),
      to: z.string().describe('Target entity name or ID'),
      type: z.enum(['worked_with', 'belongs_to', 'uses_tool', 'participated_in', 'decided', 'created', 'related_to', 'knows', 'owns']).describe('Relation type'),
      confidence: z.number().min(0).max(1).optional().default(0.8).describe('Confidence score'),
    }).optional().describe('Relation to add'),
  }),
}, async ({ entity, relation }) => {
  try {
    const { addEntity, addRelation } = await import('./graph/graph_store.js');
    const { loadGraph } = await import('./graph/graph_store.js');

    const results = [];

    if (entity) {
      const existing = loadGraph().entities.find(
        e => e.name === entity.name && e.type === entity.type
      );
      if (existing) {
        results.push({ action: 'skipped', reason: 'entity_exists', entity: existing.name });
      } else {
        const added = addEntity({
          name: entity.name,
          type: entity.type,
          description: entity.description || null,
        });
        results.push({ action: 'added', entity: added });
      }
    }

    if (relation) {
      const graph = loadGraph();
      const fromEntity = graph.entities.find(
        e => e.name === relation.from || e.id === relation.from
      );
      const toEntity = graph.entities.find(
        e => e.name === relation.to || e.id === relation.to
      );

      if (!fromEntity || !toEntity) {
        results.push({ action: 'error', reason: 'entity_not_found', from: relation.from, to: relation.to });
      } else {
        const added = addRelation({
          from: fromEntity.id,
          to: toEntity.id,
          relation: relation.type,
          confidence: relation.confidence ?? 0.8,
          source: 'manual',
        });
        results.push({ action: 'added', relation: { from: fromEntity.name, to: toEntity.name, type: relation.type } });
      }
    }

    return { content: [{ type: 'text', text: JSON.stringify({ results }, null, 2) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_graph_delete', {
  description: 'Delete an entity (and its relations) or a specific relation from the knowledge graph.',
  inputSchema: z.object({
    entityName: z.string().optional().describe('Entity name to delete'),
    entityId: z.string().optional().describe('Entity ID to delete'),
    relationId: z.string().optional().describe('Relation ID to delete'),
  }),
}, async ({ entityName, entityId, relationId }) => {
  try {
    const { loadGraph, saveGraph } = await import('./graph/graph_store.js');

    if (relationId) {
      const graph = loadGraph();
      const before = graph.relations.length;
      graph.relations = graph.relations.filter(r => r.id !== relationId);
      graph.version++;
      saveGraph(graph);
      return { content: [{ type: 'text', text: JSON.stringify({ deleted: 'relation', count: before - graph.relations.length }) }] };
    }

    if (entityName || entityId) {
      const graph = loadGraph();
      const entity = graph.entities.find(
        e => (entityName && e.name === entityName) || (entityId && e.id === entityId)
      );
      if (!entity) {
        return { content: [{ type: 'text', text: JSON.stringify({ error: 'entity_not_found' }) }] };
      }

      const beforeE = graph.entities.length;
      const beforeR = graph.relations.length;
      graph.entities = graph.entities.filter(e => e.id !== entity.id);
      graph.relations = graph.relations.filter(r => r.from !== entity.id && r.to !== entity.id);
      graph.version++;
      saveGraph(graph);

      return { content: [{ type: 'text', text: JSON.stringify({
        deleted: 'entity',
        entity: entity.name,
        entities_removed: beforeE - graph.entities.length,
        relations_removed: beforeR - graph.relations.length,
      }) }] };
    }

    return { content: [{ type: 'text', text: 'Provide entityName/entityId or relationId' }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

// ============ P0-2: Entity Tools ============

server.registerTool('memory_entity_extract', {
  description: 'Extract entities (person/organization/project/topic/tool/date/location) from text using rule-based extraction. Adds entities to the knowledge graph.',
  inputSchema: z.object({
    text: z.string().describe('Text to extract entities from'),
  }),
}, async ({ text }) => {
  return memoryEntityExtractTool({ text });
});

server.registerTool('memory_entity_link', {
  description: 'Create a directed relation between two entities in the knowledge graph. If entities do not exist they will be auto-created.',
  inputSchema: z.object({
    from: z.string().describe('Source entity name or ID'),
    to: z.string().describe('Target entity name or ID'),
    relation: z.string().describe('Relation type: worked_with, related_to, belongs_to, uses_tool, participated_in, decided, created, knows, owns'),
    strength: z.number().optional().default(0.8).describe('Relation strength/confidence 0-1'),
  }),
}, async ({ from, to, relation, strength }) => {
  return memoryEntityLinkTool({ from, to, relation, strength });
});

server.registerTool('memory_entity_neighbors', {
  description: 'Get neighbor entities connected to a given entity via graph relations.',
  inputSchema: z.object({
    entity: z.string().describe('Entity name or ID to look up'),
    relationType: z.string().optional().describe('Filter by relation type'),
  }),
}, async ({ entity, relationType }) => {
  return memoryEntityNeighborsTool({ entity, relationType });
});

server.registerTool('memory_entity_search', {
  description: 'Graph-expanded search: uses the knowledge graph to expand the query with related entity names before searching.',
  inputSchema: z.object({
    query: z.string().describe('Search query'),
    topK: z.number().optional().default(5).describe('Number of results'),
    scope: z.string().optional().describe('Scope filter'),
  }),
}, async ({ query, topK, scope }) => {
  return memoryEntitySearchTool({ query, topK, scope });
});

// ============ v2.7.0: Identity Memory Tools ============

server.registerTool('memory_identity_extract', {
  description: 'Extract identity/preference/habit/requirement statements from text. Rules: "我喜欢..."→preference, "我讨厌..."→preference/dislike, "我是..."→identity, "我习惯..."→habit, "我需要..."→requirement, "我会..."→skill. Returns extracted statements with suggested importance scores.',
  inputSchema: z.object({
    text: z.string().describe('Text to extract identity statements from'),
  }),
}, async ({ text }) => {
  return memoryIdentityExtractTool({ text });
});

server.registerTool('memory_identity_update', {
  description: 'Store extracted identity statements as high-priority memories. Identity memories always use importance >= 0.9.',
  inputSchema: z.object({
    extractions: z.array(z.object({
      content: z.string().describe('Extracted text content'),
      type: z.string().optional().describe('Category: identity, preference, habit, requirement, skill, goal'),
      importance: z.number().optional().describe('Importance (default 0.9 for identity types)'),
      subType: z.string().optional().describe('Sub-type label'),
      label: z.string().optional().describe('Human-readable label'),
    })).describe('Array of extracted identity statements from memory_identity_extract'),
  }),
}, async ({ extractions }) => {
  return memoryIdentityUpdateTool({ extractions });
});

server.registerTool('memory_identity_get', {
  description: 'Get a summary of the user\'s identity profile from stored identity memories. Returns all memories categorized as identity, preference, habit, requirement, skill, or goal, grouped by category with importance scores.',
  inputSchema: z.object({
    type: z.string().optional().describe('Filter by specific identity type (identity/preference/habit/requirement/skill/goal)'),
  }),
}, async ({ type }) => {
  return memoryIdentityGetTool({ type });
});

// ============ P1-4: Git Notes Backup/Restore ============

server.registerTool('memory_gitnotes_backup', {
  description: 'Backup memories to git notes for cold storage. Exports memories to .git/notes/memories ref.',
  inputSchema: z.object({
    scope: z.string().optional().describe('Scope to backup: USER, TEAM, AGENT, GLOBAL, or all (default all)'),
  }),
}, async ({ scope }) => {
  return memoryGitnotesBackupTool({ scope });
});

server.registerTool('memory_gitnotes_restore', {
  description: 'Restore memories from git notes backup.',
  inputSchema: z.object({
    scope: z.string().optional().describe('Scope to restore: USER, TEAM, AGENT, GLOBAL, or all (default all)'),
  }),
}, async ({ scope }) => {
  return memoryGitnotesRestoreTool({ scope });
});

// ============ P1-6: Smart Extraction ============

server.registerTool('memory_auto_extract', {
  description: 'Manually trigger structured fact extraction from text. Extracts preferences, facts, decisions, entities from text using LLM + rules.',
  inputSchema: z.object({
    text: z.string().describe('Text to extract structured facts from'),
    useLLM: z.boolean().optional().default(true).describe('Use LLM for extraction (default true)'),
  }),
}, async ({ text, useLLM = true }) => {
  try {
    const extractor = new AutoExtractor();
    const results = await extractor.extractFromConversation(text, useLLM);
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          count: results.length,
          extracted: results.map(r => ({
            category: r.category,
            text: r.text,
            importance: r.importance,
            source: r.source,
            matched_keyword: r.matched_keyword,
          })),
        }, null, 2),
      }],
    };
  } catch (err) {
    return { content: [{ type: 'text', text: `Auto extract error: ${err.message}` }], isError: true };
  }
});

// ============ P2-7: Cloud Backup/Restore ============

server.registerTool('memory_cloud_backup', {
  description: 'Backup all memories to cloud storage (local/s3/webdav). Uses MemoryBackup class.',
  inputSchema: z.object({
    scope: z.string().optional().describe('Scope to backup: USER, TEAM, AGENT, GLOBAL, or all'),
  }),
}, async ({ scope }) => {
  try {
    const cfg = new CloudConfig();
    const backup = new MemoryBackup(cfg);
    const result = backup.createBackup();
    return { content: [{ type: 'text', text: JSON.stringify({ success: true, ...result }, null, 2) }] };
  } catch (err) {
    return { content: [{ type: 'text', text: `Cloud backup error: ${err.message}` }], isError: true };
  }
});

server.registerTool('memory_cloud_restore', {
  description: 'Restore memories from cloud backup. Lists available backups or restores a specific one.',
  inputSchema: z.object({
    scope: z.string().optional().describe('Scope to restore'),
    backupId: z.string().optional().describe('Specific backup timestamp to restore'),
    action: z.enum(['list', 'restore']).optional().default('list').describe('Action: list available backups or restore'),
  }),
}, async ({ scope, backupId, action = 'list' }) => {
  try {
    const cfg = new CloudConfig();
    const backup = new MemoryBackup(cfg);
    if (action === 'list') {
      const backups = backup.listBackups();
      return { content: [{ type: 'text', text: JSON.stringify({ count: backups.length, backups }, null, 2) }] };
    } else {
      if (!backupId) {
        return { content: [{ type: 'text', text: 'Error: backupId is required for restore action' }], isError: true };
      }
      const result = backup.restoreBackup(backupId);
      return { content: [{ type: 'text', text: JSON.stringify({ success: true, ...result }, null, 2) }] };
    }
  } catch (err) {
    return { content: [{ type: 'text', text: `Cloud restore error: ${err.message}` }], isError: true };
  }
});

// ============ HTTP Dashboard Server (Optional) ============

function startDashboardServer(port = 3848) {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const dashboardPath = path.join(__dirname, 'dashboard.html');

  const mimeTypes = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
  };

  const server = http.createServer((req, res) => {
    const url = req.url.split('?')[0];

    // Serve dashboard
    if (url === '/' || url === '/dashboard') {
      fs.readFile(dashboardPath, 'utf8', (err, data) => {
        if (err) {
          res.writeHead(404, { 'Content-Type': 'text/plain' });
          res.end('Dashboard not found');
          return;
        }
        res.writeHead(200, { 'Content-Type': mimeTypes['.html'] });
        res.end(data);
      });
      return;
    }

    // ---- API Routes ----
    let apiResult;
    try {
      if (url === '/memories' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(getAllMemories()));
        return;
      }
      if (url === '/stats') {
        const all = getAllMemories();
        const byCategory = {};
        const byTier = { HOT: 0, WARM: 0, COLD: 0 };
        const byScope = {};
        all.forEach(m => {
          byCategory[m.category || 'unknown'] = (byCategory[m.category || 'unknown'] || 0) + 1;
          if (m.tier) byTier[m.tier] = (byTier[m.tier] || 0) + 1;
          if (m.scope) byScope[m.scope] = (byScope[m.scope] || 0) + 1;
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          total: all.length,
          byCategory,
          byTier,
          byScope,
          memoryCount: all.length
        }));
        return;
      }
      const deleteMatch = url.match(/^\/memories\/([^/?]+)/);
      if (deleteMatch && req.method === 'DELETE') {
        const id = decodeURIComponent(deleteMatch[1]);
        deleteMemory(id);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: true }));
        return;
      }
      if (url === '/memories' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
          try {
            const { text, category, importance, tags } = JSON.parse(body);
            const mem = addMemory({ text, category, importance, tags });
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(mem));
          } catch {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Invalid JSON' }));
          }
        });
        return;
      }
    } catch (e) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: e.message }));
      return;
    }

    // 404
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  });

  server.listen(port, () => {
    structuredLog.info(`Dashboard server listening on http://localhost:${port}`);
  });

  return server;
}

// Expose startDashboardServer so it can be called from outside
global._startMemoryDashboard = startDashboardServer;

// ============ Start ============

async function main() {
    structuredLog.info( `Starting unified-memory-mcp v1.1.0`);
    structuredLog.info( `Memory file: ${config.memoryFile}`);
    structuredLog.info( `Ollama: ${config.ollamaUrl}`);

  // Register multimodal tools (image/audio/file analysis)
  registerMultimodalTools(server);

  // Register Episode v2 tools (conversation session management)
  registerEpisodeTools(server);

  // Register Rerank v2 tools (LLM cross-encoder reranking)
  registerRerankTools(server);

  // Register Refresh v2 tools (48h reconsolidation)
  registerRefreshTools(server);

  // Register Procedural Memory v2 tools
  registerProceduralTools(server);

  // Register Rule Memory v2 tools
  registerRuleTools(server);

  // Register Observability v2 tools (HTTP API)
  registerObservabilityTools(server);

  // Register Chunking v2 tools (context chunking)
  registerChunkTools(server);

  // Register Phase 3 tools: OpenClaw Plugin, Git, Cloud, Weibull
  registerPluginTools(server);
  registerGitTools(server);
  registerCloudTools(server);
  registerDecayStatsTool(server);

  const transport = new StdioServerTransport();
  await server.connect(transport);
    structuredLog.info( 'MCP Server connected via stdio');
}

main().catch((err) => {
  console.error('Fatal:', err);
  process.exit(1);
});
