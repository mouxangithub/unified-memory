/**
 * BM25搜索引擎 - 完全本地，不调用LLM
 * 参考: memory_bm25.py (274行)
 */

import { getAllMemories } from './storage.js';

/**
 * Simple tokenizer - 中英文分词
 * @param {string} text
 * @returns {string[]}
 */
function tokenize(text) {
  if (!text) return [];
  // 中文按字符，英文按单词
  const tokens = [];
  // 移除HTML标签
  text = text.replace(/<[^>]+>/g, ' ');
  // 英文单词
  const english = text.match(/[a-zA-Z_]+/g) || [];
  for (const word of english) {
    const lower = word.toLowerCase();
    if (lower.length > 1) tokens.push(lower);
  }
  // 中文字符（去除停用词）
  const chinese = text.match(/[\u4e00-\u9fa5]/g) || [];
  const stopChars = new Set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '么']);
  for (const char of chinese) {
    if (!stopChars.has(char)) tokens.push(char);
  }
  return tokens;
}

/**
 * BM25 Ranking Function
 * @param {string} query
 * @param {string} text
 * @param {object} index - { docLengths, avgDocLength, invertedIndex, docCount, idfCache }
 * @param {object} [options]
 * @returns {number}
 */
function bm25Score(query, text, index, options = {}) {
  const { k1 = 1.5, b = 0.75 } = options;
  const tokens = tokenize(text);
  const docLength = tokens.length;
  if (docLength === 0) return 0;

  const queryTokens = tokenize(query);
  let score = 0;

  for (const qtoken of queryTokens) {
    const termPostings = index.invertedIndex.get(qtoken);
    if (!termPostings) continue;

    const tf = termPostings.get(text) || 0;
    if (tf === 0) continue;

    // IDF
    let idf = index.idfCache.get(qtoken);
    if (idf === undefined) {
      const docWithTerm = termPostings.size;
      idf = Math.log((index.docCount - docWithTerm + 0.5) / (docWithTerm + 0.5) + 1);
      index.idfCache.set(qtoken, idf);
    }

    // TF normalization
    const tfNorm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (docLength / index.avgDocLength)));
    score += idf * tfNorm;
  }

  return score;
}

/**
 * Build BM25 index from all memories
 * @returns {object}
 */
export function buildBM25Index() {
  const memories = getAllMemories();
  const invertedIndex = new Map();
  const docLengths = new Map();
  const idfCache = new Map();
  let totalLength = 0;

  for (const mem of memories) {
    const text = mem.text || '';
    const tokens = tokenize(text);
    docLengths.set(text, tokens.length);
    totalLength += tokens.length;

    for (const token of tokens) {
      if (!invertedIndex.has(token)) {
        invertedIndex.set(token, new Map());
      }
      const postings = invertedIndex.get(token);
      postings.set(text, (postings.get(text) || 0) + 1);
    }
  }

  const docCount = memories.length;
  const avgDocLength = docCount > 0 ? totalLength / docCount : 1;

  return { invertedIndex, docLengths, avgDocLength, docCount, idfCache };
}

/**
 * Search using BM25
 * @param {string} query
 * @param {number} [topK=10]
 * @returns {Array<{memory: object, score: number, highlight: string}>}
 */
export function bm25Search(query, topK = 10) {
  const memories = getAllMemories();
  if (!query || memories.length === 0) return [];

  const index = buildBM25Index();
  const results = [];

  for (const mem of memories) {
    const score = bm25Score(query, mem.text, index);
    if (score > 0) {
      // Simple highlight - mark first occurrence
      const qTokens = tokenize(query);
      let highlight = mem.text.slice(0, 150);
      if (mem.text.length > 150) highlight += '...';

      results.push({ memory: mem, score, highlight });
    }
  }

  // Sort by score descending
  results.sort((a, b) => b.score - a.score);
  return results.slice(0, topK);
}
