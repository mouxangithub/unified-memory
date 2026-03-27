/**
 * Cross-encoder/LLM Reranking
 * Re-scores BM25+Vector results using LLM understanding
 * Reads from config.js (env vars or hardcoded)
 */
import { config } from './config.js';

function getLlmProvider() {
  const providers = config.llmProviders || [];
  // Prefer ollama if available
  return providers.find(p => p.name === 'ollama') || providers[0] || {
    baseURL: process.env.OLLAMA_HOST || 'http://localhost:11434',
    model: 'qwen2.5:7b',
    apiKey: null,
  };
}

export class LlmReranker {
  constructor(llmUrl = null, model = null) {
    const defaultProvider = getLlmProvider();
    this.llmUrl = llmUrl || defaultProvider.baseURL;
    this.model = model || defaultProvider.model;
    this.initialized = true;
  }

  /**
   * Rerank documents by asking LLM to score relevance to query
   * @param {string} query
   * @param {Array} documents - Array of {memory: {text, id}, score} objects
   * @param {number} topK
   * @returns {Array} reranked documents
   */
  async rerank(query, documents, topK = 5) {
    if (!documents || documents.length === 0) return [];
    if (documents.length === 1) return documents.slice(0, topK);

    const scored = await Promise.all(documents.map(async (doc) => {
      const text = doc.memory?.text || doc.memory?.content || '';
      if (!text) return { ...doc, rerankScore: doc.score || 0 };
      
      const prompt = `Query: ${query}\nDocument: ${text.slice(0, 500)}\nScore 1-10 how relevant is this document to the query. Reply only with the number:`;
      
      let rerankScore = doc.score || 0;
      try {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 3000);
        const res = await fetch(`${this.llmUrl}/api/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model: this.model, prompt, stream: false, options: { num_predict: 8 } }),
          signal: controller.signal,
        });
        clearTimeout(timer);
        if (res.ok) {
          const json = await res.json();
          const match = json.response?.match(/\d+/);
          if (match) rerankScore = parseInt(match[0]) / 10;
        }
      } catch { /* fallback to original score */ }
      
      return { ...doc, rerankScore };
    }));

    return scored
      .sort((a, b) => b.rerankScore - a.rerankScore)
      .slice(0, topK);
  }
}

/**
 * Simple keyword-based rerank (fallback when LLM unavailable)
 */
export function keywordRerank(query, documents, topK = 5) {
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  if (queryWords.length === 0) return documents.slice(0, topK);

  return documents
    .map(doc => {
      const text = (doc.memory?.text || doc.memory?.content || '').toLowerCase();
      const matches = queryWords.filter(w => text.includes(w)).length;
      return { ...doc, rerankScore: (doc.score || 0) + matches * 0.1 };
    })
    .sort((a, b) => b.rerankScore - a.rerankScore)
    .slice(0, topK);
}
