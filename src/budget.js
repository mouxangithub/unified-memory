/**
 * budget.js - Memory Budget Calculator
 * 
 * Calculates how many memories can fit within a given context window budget.
 * This enables dynamic top-K selection based on actual token limits rather
 * than a fixed number.
 * 
 * Formula:
 *   maxMemories = floor((contextBudget - queryTokens - responseReserved) / avgMemoryTokens)
 * 
 * Usage:
 *   const budget = calculateBudget({ query, contextBudget: 120000 });
 *   const results = await search(query, { topK: budget.limit, ... });
 */

import { estimateTokensSimple, estimateQueryTokens } from './utils/token_estimator.js';
import { config } from './config.js';

// Default budget configuration
const DEFAULT_CONTEXT_BUDGET = 120000;   // 120k tokens (e.g., GPT-4 Turbo context)
const DEFAULT_RESPONSE_RESERVED = 20000; // Reserve 20k tokens for response generation
const DEFAULT_AVG_MEMORY_TOKENS = 500;    // Average memory size in tokens

// Standard context budgets for various models
export const CONTEXT_BUDGETS = {
  '32k': 32000,
  '64k': 64000,
  '128k': 128000,
  '200k': 200000,
  '1M': 1000000,
};

/**
 * Memory budget calculation result
 * @typedef {Object} BudgetResult
 * @property {number} limit - maximum number of memories to retrieve
 * @property {number} contextBudget - total context window size
 * @property {number} queryTokens - tokens used by the query
 * @property {number} responseReserved - tokens reserved for response
 * @property {number} availableForMemories - tokens available for memory content
 * @property {number} avgMemoryTokens - assumed average tokens per memory
 * @property {number} estimatedTotalTokens - estimated total if all memories used
 */

/**
 * Calculate how many memories can fit within a context budget
 * 
 * @param {Object} params
 * @param {string} params.query - search query text
 * @param {number} [params.contextBudget] - total available tokens (default: from config or 120k)
 * @param {number} [params.responseReserved] - tokens to reserve for response (default: 20k)
 * @param {number} [params.avgMemoryTokens] - average tokens per memory (default: 500)
 * @param {number} [params.topK] - optional fixed upper bound (limit won't exceed this)
 * @returns {BudgetResult}
 */
export function calculateBudget({
  query = '',
  contextBudget = null,
  responseReserved = null,
  avgMemoryTokens = null,
  topK = null,
}) {
  // Resolve defaults from config or constants
  const effectiveBudget = contextBudget ?? config.contextBudget ?? DEFAULT_CONTEXT_BUDGET;
  const effectiveResponseReserved = responseReserved ?? config.responseReserved ?? DEFAULT_RESPONSE_RESERVED;
  const effectiveAvgMemoryTokens = avgMemoryTokens ?? config.avgMemoryTokens ?? DEFAULT_AVG_MEMORY_TOKENS;

  // Estimate query token cost
  const queryTokens = estimateQueryTokens(query);

  // Calculate available space for memory content
  const availableForMemories = Math.max(0, effectiveBudget - queryTokens - effectiveResponseReserved);

  // Calculate max memories that can fit
  let limit = Math.floor(availableForMemories / effectiveAvgMemoryTokens);

  // Apply upper bound if specified
  if (topK !== null && topK > 0) {
    limit = Math.min(limit, topK);
  }

  // Ensure at least 1 if budget allows
  limit = Math.max(0, limit);

  return {
    limit,
    contextBudget: effectiveBudget,
    queryTokens,
    responseReserved: effectiveResponseReserved,
    availableForMemories,
    avgMemoryTokens: effectiveAvgMemoryTokens,
    estimatedTotalTokens: queryTokens + (limit * effectiveAvgMemoryTokens),
  };
}

/**
 * Calculate budget and estimate how many memories fit for multiple context sizes
 * Useful for providing users with budget recommendations
 * 
 * @param {string} query - search query
 * @param {number} [topK] - optional upper bound
 * @returns {Object} budget estimates for standard context sizes
 */
export function estimateBudgets(query, topK = null) {
  const budgets = {};
  for (const [name, budget] of Object.entries(CONTEXT_BUDGETS)) {
    budgets[name] = calculateBudget({ query, contextBudget: budget, topK });
  }
  return budgets;
}

/**
 * Budget-aware result trimmer
 * 
 * Takes search results and trims them if they exceed the token budget.
 * Trims lowest-scoring memories first.
 * 
 * @param {Array} results - search results with memory and score fields
 * @param {number} budget - token budget for memories
 * @param {number} [minResults=3] - minimum results to keep if budget allows
 * @returns {Array} trimmed results
 */
export function trimResultsByBudget(results, budget, minResults = 3) {
  if (!Array.isArray(results) || results.length === 0) return results;
  if (!budget || budget <= 0) return results;

  // Sort by score descending (keep highest scoring)
  const sorted = [...results].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));

  let totalTokens = 0;
  const kept = [];

  for (const result of sorted) {
    const text = result.memory?.text || result.memory?.content || '';
    const tokens = estimateTokensSimple(text);

    if (kept.length < minResults || totalTokens + tokens <= budget) {
      kept.push(result);
      totalTokens += tokens;
    } else {
      break; // Budget exhausted
    }
  }

  return kept;
}
