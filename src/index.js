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
import { initWal, flushWal, listWalFiles } from './wal.js';
import { assignTiers, partitionByTier, redistributeTiers, compressColdTier } from './tier.js';
import { shouldSkipRetrieval } from './adaptive.js';
import { buildBM25Index, bm25Search } from './bm25.js';
import { getEmbedding, vectorSearch } from './vector.js';
import { mmrSelect, mmrSelectWithEmbedding } from './mmr.js';
import { LlmReranker, keywordRerank } from './rerank.js';
import { CrossEncoderRerank, rerankResults } from './tools/rerank.js';
import { normalizeScope, filterByScope, SCOPE_LEVELS, SCOPE_HIERARCHY } from './scope.js';

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
    log('ERROR', `Preference slots error: ${err.message}`);
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
    log('ERROR', `Lesson system error: ${err.message}`);
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
    log('ERROR', `Autostore error: ${err.message}`);
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
    log('ERROR', `Concurrent search error: ${err.message}`);
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
    log('ERROR', `Predict error: ${err.message}`);
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
    log('ERROR', `Recommend error: ${err.message}`);
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
    log('ERROR', `Inference error: ${err.message}`);
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
    log('ERROR', `Summary error: ${err.message}`);
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
    log('ERROR', `Feedback error: ${err.message}`);
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
    log('ERROR', `QMD search error: ${err.message}`);
    return { content: [{ type: 'text', text: `QMD search error: ${err.message}` }], isError: true };
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
    log('ERROR', `Templates error: ${err.message}`);
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
  description: 'Dense vector semantic search using Ollama embeddings. Get embedding for text or search by semantic similarity.',
  inputSchema: z.object({
    action: z.enum(['embed', 'search']).describe('Action: embed=get vector for text, search=semantic similarity search'),
    text: z.string().optional().describe('Text to embed (for embed action)'),
    query: z.string().optional().describe('Query for search (for search action)'),
    topK: z.number().default(10).describe('Number of results for search'),
  }),
}, async ({ action, text, query, topK }) => {
  try {
    if (action === 'embed') {
      const embedding = await getEmbedding(text || '');
      return { content: [{ type: 'text', text: JSON.stringify({ embedding, dimensions: embedding.length }) }] };
    }
    if (action === 'search') {
      const results = await vectorSearch(query || '', topK || 10);
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
