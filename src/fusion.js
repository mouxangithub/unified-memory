/**
 * RRF (Reciprocal Rank Fusion) - 混合 BM25 和向量搜索结果
 * 参考: memory_qmd_search.py 的 RRF 融合部分
 */

import { config } from './config.js';
import { bm25Search } from './bm25.js';
import { vectorSearch } from './vector.js';

/**
 * Reciprocal Rank Fusion
 * @param {Array<{memory: object, score: number}>[]} resultLists
 * @param {number} [k=60]
 * @returns {Array<{memory: object, fusionScore: number, highlight: string}>}
 */
function reciprocalRankFusion(resultLists, k = 60) {
  const scores = new Map();

  for (const results of resultLists) {
    for (let i = 0; i < results.length; i++) {
      const mem = results[i].memory;
      const memId = mem.id;
      const rank = i + 1;
      const rrfScore = 1 / (k + rank);

      if (scores.has(memId)) {
        scores.get(memId).fusionScore += rrfScore;
      } else {
        scores.set(memId, {
          memory: mem,
          fusionScore: rrfScore,
          highlight: results[i].highlight || mem.text?.slice(0, 150),
        });
      }
    }
  }

  return Array.from(scores.values()).sort((a, b) => b.fusionScore - a.fusionScore);
}

/**
 * Hybrid search: BM25 + Vector with RRF fusion
 * @param {string} query
 * @param {number} [topK=10]
 * @param {string} [mode='hybrid']
 * @returns {Promise<Array<{memory: object, fusionScore: number, highlight: string, bm25Score?: number, vectorScore?: number}>>}
 */
export async function hybridSearch(query, topK = 10, mode = 'hybrid', scope = null) {
  const k = config.rrfK || 60;

  if (mode === 'bm25') {
    // BM25 has no scope filtering — return all (BM25 is scope-agnostic in this implementation)
    const results = bm25Search(query, topK * 2);
    return results.map((r, i) => ({
      memory: r.memory,
      fusionScore: 1 / (k + i + 1),
      highlight: r.highlight,
      bm25Score: r.score,
    }));
  }

  if (mode === 'vector') {
    const results = await vectorSearch(query, topK * 2, scope);
    return results.map((r, i) => ({
      memory: r.memory,
      fusionScore: 1 / (k + i + 1),
      highlight: r.highlight,
      vectorScore: r.score,
    }));
  }

  // Hybrid: BM25 + Vector RRF — vector search gets scope filter, BM25 is scope-agnostic
  const [bm25Results, vectorResults] = await Promise.all([
    Promise.resolve(bm25Search(query, topK * 2)),
    vectorSearch(query, topK * 2, scope),
  ]);

  const fused = reciprocalRankFusion([bm25Results, vectorResults], k);
  return fused.slice(0, topK).map((r) => ({
    ...r,
    highlight: r.highlight || r.memory.text?.slice(0, 150),
  }));
}
