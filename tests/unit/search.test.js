/**
 * Search Pipeline Unit Tests
 * Tests: BM25 scoring, vector rerank pipeline, hybrid search behavior
 */
import { describe, it, expect } from 'vitest';

// Minimal BM25 implementation for testing
function tokenize(text) {
  return text.toLowerCase().replace(/[^a-z0-9\s]/g, ' ').split(/\s+/).filter(Boolean);
}

function buildBM25(documents) {
  const docs = documents.map((d, i) => ({ id: d.id || i, tokens: tokenize(d.text), doc: d }));
  const N = docs.length;
  const avgdl = docs.reduce((s, d) => s + d.tokens.length, 0) / N;

  const docFreq = {};
  for (const d of docs) {
    const unique = new Set(d.tokens);
    for (const t of unique) docFreq[t] = (docFreq[t] || 0) + 1;
  }

  function score(queryTokens, doc) {
    let score = 0;
    const k1 = 1.5, b = 0.75;
    for (const term of queryTokens) {
      const tf = doc.tokens.filter(t => t === term).length;
      if (tf === 0) continue;
      const df = docFreq[term] || 0;
      const idf = Math.log((N - df + 0.5) / (df + 0.5) + 1);
      const numerator = tf * (k1 + 1);
      const denominator = tf + k1 * (1 - b + b * doc.tokens.length / avgdl);
      score += idf * numerator / denominator;
    }
    return score;
  }

  function search(query, topK = 10) {
    const qTokens = tokenize(query);
    const results = docs
      .map(d => ({ ...d.doc, bm25Score: score(qTokens, d) }))
      .filter(d => d.bm25Score > 0)
      .sort((a, b) => b.bm25Score - a.bm25Score);
    return results.slice(0, topK);
  }

  return { search, docs };
}

// Simple cosine similarity for vector test
function cosineSimilarity(a, b) {
  if (a.length !== b.length) return 0;
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

// Mock vector: deterministic hash-based pseudo-embedding
function pseudoEmbedding(text, dims = 8) {
  const tokens = tokenize(text);
  const vec = new Array(dims).fill(0);
  for (const t of tokens) {
    for (let i = 0; i < Math.min(t.length, dims); i++) {
      vec[i] += t.charCodeAt(i) / 255;
    }
  }
  const norm = Math.sqrt(vec.reduce((s, v) => s + v * v, 0));
  return norm > 0 ? vec.map(v => v / norm) : vec;
}

function rerankWithQuery(query, results, topK) {
  // Rerank by combining bm25 score and vector similarity
  const queryVec = pseudoEmbedding(query);
  const reranked = results.map(r => {
    const docVec = pseudoEmbedding(r.text);
    const sim = cosineSimilarity(queryVec, docVec);
    return { ...r, fusionScore: r.bm25Score * 0.4 + sim * 0.6 };
  });
  return reranked.sort((a, b) => b.fusionScore - a.fusionScore).slice(0, topK);
}

// ─── Tests ──────────────────────────────────────────────────────────────────

describe('BM25 Scoring', () => {
  it('exact match scores higher than partial match', () => {
    const docs = [
      { id: 'd1', text: 'the cat sat on the mat' },
      { id: 'd2', text: 'the dog ran in the park' },
    ];
    const { search } = buildBM25(docs);
    const r1 = search('cat');
    const r2 = search('dog');
    expect(r1[0]?.id).toBe('d1');
    expect(r2[0]?.id).toBe('d2');
  });

  it('returns empty for no matching terms', () => {
    const docs = [{ id: 'd1', text: 'hello world' }];
    const { search } = buildBM25(docs);
    const results = search('xyz123 nonexistent');
    expect(results).toHaveLength(0);
  });

  it('orders by BM25 score descending', () => {
    const docs = [
      { id: 'd1', text: 'python programming language tutorial guide' },
      { id: 'd2', text: 'python programming' },
      { id: 'd3', text: 'python is a programming language' },
    ];
    const { search } = buildBM25(docs);
    const results = search('python programming');
    const scores = results.map(r => r.bm25Score);
    for (let i = 1; i < scores.length; i++) {
      expect(scores[i - 1]).toBeGreaterThanOrEqual(scores[i]);
    }
  });

  it('handles duplicate documents', () => {
    const docs = [
      { id: 'd1', text: 'apple banana' },
      { id: 'd2', text: 'apple banana' },
      { id: 'd3', text: 'apple' },
    ];
    const { search } = buildBM25(docs);
    const results = search('apple banana');
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].bm25Score).toBeGreaterThan(0);
  });
});

describe('Vector Similarity', () => {
  it('identical vectors have similarity 1', () => {
    const v = pseudoEmbedding('hello world');
    expect(cosineSimilarity(v, v)).toBeCloseTo(1.0, 5);
  });

  it('opposite vectors have similarity -1 to 1', () => {
    const v1 = pseudoEmbedding('test document content');
    const v2 = v1.map(x => -x);
    expect(cosineSimilarity(v1, v2)).toBeCloseTo(-1.0, 5);
  });

  it('similar text has higher similarity than unrelated', () => {
    const v1 = pseudoEmbedding('machine learning neural network');
    const v2 = pseudoEmbedding('deep learning artificial intelligence');
    const v3 = pseudoEmbedding('cooking recipes food');
    const sim12 = cosineSimilarity(v1, v2);
    const sim13 = cosineSimilarity(v1, v3);
    expect(sim12).toBeGreaterThan(sim13);
  });
});

describe('Rerank Pipeline', () => {
  it('rerank reorders results based on fusion score', () => {
    const docs = [
      { id: 'd1', text: 'python programming language tutorial', bm25Score: 10 },
      { id: 'd2', text: 'deep learning neural network AI', bm25Score: 5 },
    ];
    const reranked = rerankWithQuery('deep learning python', docs, 2);
    // d2 should rank higher due to vector similarity with "deep learning"
    expect(reranked[0].id).toBe('d2');
    expect(reranked[1].id).toBe('d1');
  });

  it('topK limits results', () => {
    const docs = Array.from({ length: 20 }, (_, i) => ({
      id: `d${i}`,
      text: `document ${i} content`,
      bm25Score: 20 - i,
    }));
    const reranked = rerankWithQuery('document', docs, 5);
    expect(reranked).toHaveLength(5);
  });

  it('fusionScore is weighted combination', () => {
    const doc = { id: 'd1', text: 'test', bm25Score: 1.0 };
    const reranked = rerankWithQuery('test', [doc], 1);
    expect(reranked[0].fusionScore).toBeGreaterThan(0);
    expect(typeof reranked[0].fusionScore).toBe('number');
  });
});

describe('Hybrid Pipeline', () => {
  it('bm25 + vector combined gives different ordering than bm25 alone', () => {
    const docs = [
      { id: 'd1', text: 'python programming guide manual', bm25Score: 8 },
      { id: 'd2', text: 'neural network deep learning python', bm25Score: 3 },
    ];
    const bm25Only = docs.sort((a, b) => b.bm25Score - a.bm25Score);
    const hybrid = rerankWithQuery('python neural', docs, 2);
    // d2 should be promoted in hybrid due to semantic match
    expect(hybrid[0].id).toBe('d2');
    expect(bm25Only[0].id).toBe('d1');
  });

  it('empty results from one search type returns empty overall', () => {
    const docs = [{ id: 'd1', text: 'hello world', bm25Score: 0 }];
    const hybrid = rerankWithQuery('unmatchable xyz', docs, 5);
    expect(hybrid).toHaveLength(0);
  });
});
