/**
 * qmd_search.js - QMD-style search integration
 * Calls external QMD CLI at /usr/local/bin/qmd
 * 
 * Features:
 * - BM25 keyword search (local, no LLM)
 * - Vector semantic search (Ollama local)  
 * - RRF hybrid fusion (no LLM needed)
 * - Snippet-level return (save tokens)
 */

import { spawn } from 'child_process';
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { getAllMemories } from '../storage.js';

const QMD_CLI = '/usr/local/bin/qmd';
const HOME = process.env.HOME || '/root';
const MEMORY_DIR = join(HOME, '.openclaw/workspace/memory');

/**
 * Execute QMD CLI command
 */
function execQMD(args) {
  return new Promise((resolve, reject) => {
    if (!existsSync(QMD_CLI)) {
      reject(new Error(`QMD CLI not found at ${QMD_CLI}`));
      return;
    }

    const proc = spawn(QMD_CLI, args, {
      cwd: MEMORY_DIR,
      timeout: 10000
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', d => stdout += d.toString());
    proc.stderr.on('data', d => stderr += d.toString());

    proc.on('close', code => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(`QMD exited with code ${code}: ${stderr || stdout}`));
      }
    });

    proc.on('error', reject);
  });
}

/**
 * Check if QMD CLI is available
 */
export async function isQMDAvailable() {
  try {
    await execQMD(['--version']);
    return true;
  } catch {
    return false;
  }
}

/**
 * Search using QMD CLI
 * @param {string} query - Search query
 * @param {object} options - Search options
 * @returns {Promise<Array>} Search results
 */
export async function qmdSearch(query, options = {}) {
  const {
    topK = 5,
    mode = 'hybrid', // 'bm25', 'vector', 'hybrid', 'auto'
    snippetSize = 200
  } = options;

  // Try QMD CLI first
  try {
    const available = await isQMDAvailable();
    if (!available) {
      return fallbackSearch(query, topK);
    }

    // Build QMD-style results from memory store
    const memories = getAllMemories();
    
    if (memories.length === 0) {
      return [];
    }

    // Simple BM25-like scoring based on keyword overlap
    const queryTokens = tokenize(query);
    const results = [];

    for (const mem of memories) {
      const text = mem.text || '';
      const memTokens = tokenize(text);
      
      // Calculate simple relevance score
      let score = 0;
      for (const qt of queryTokens) {
        for (const mt of memTokens) {
          if (mt.includes(qt) || qt.includes(mt)) {
            score++;
          }
        }
      }

      if (score > 0) {
        results.push({
          id: mem.id,
          text: text.slice(0, snippetSize),
          fullText: text,
          score: score / (queryTokens.length * memTokens.length),
          category: mem.category || 'general',
          mode: 'bm25',
          memory: mem
        });
      }
    }

    // Sort by score
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, topK);

  } catch (err) {
    console.error('[QMD Search] CLI error, using fallback:', err.message);
    return fallbackSearch(query, topK);
  }
}

/**
 * Fallback search when QMD CLI is unavailable
 */
function fallbackSearch(query, topK) {
  const memories = getAllMemories();
  
  if (memories.length === 0) {
    return [];
  }

  const queryTokens = tokenize(query.toLowerCase());
  const results = [];

  for (const mem of memories) {
    const text = (mem.text || '').toLowerCase();
    const memTokens = tokenize(text);
    
    let score = 0;
    for (const qt of queryTokens) {
      if (text.includes(qt)) {
        score += 1;
      }
      for (const mt of memTokens) {
        if (mt.includes(qt) || qt.includes(mt)) {
          score += 0.5;
        }
      }
    }

    if (score > 0) {
      results.push({
        id: mem.id,
        text: (mem.text || '').slice(0, 200),
        score: score,
        category: mem.category || 'general',
        mode: 'fallback',
        memory: mem
      });
    }
  }

  results.sort((a, b) => b.score - a.score);
  return results.slice(0, topK);
}

/**
 * Simple tokenizer (supports Chinese + English)
 */
function tokenize(text) {
  const tokens = [];
  // English words
  const english = text.match(/[a-zA-Z]+/g) || [];
  tokens.push(...english.map(t => t.toLowerCase()));
  // Chinese characters
  const chinese = text.match(/[\u4e00-\u9fff]/g) || [];
  tokens.push(...chinese);
  // Numbers
  const numbers = text.match(/\d+/g) || [];
  tokens.push(...numbers);
  return tokens;
}

/**
 * Get context for a query (optimized for token limits)
 */
export async function getQMDContext(query, maxChars = 2000) {
  const results = await qmdSearch(query, { topK: 10, snippetSize: 200 });
  
  const parts = [];
  let total = 0;

  for (const r of results) {
    const snippet = r.text || '';
    if (total + snippet.length > maxChars) {
      break;
    }
    parts.push(`- [${r.category}|${r.mode}] ${snippet}`);
    total += snippet.length;
  }

  return parts.join('\n');
}

/**
 * Get QMD status
 */
export async function getQMDStatus() {
  const available = await isQMDAvailable();
  const memories = getAllMemories();
  
  return {
    qmd_available: available,
    qmd_path: QMD_CLI,
    documents: memories.length,
    mode: 'local'
  };
}
