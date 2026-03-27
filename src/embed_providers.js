/**
 * Multi-Provider Embeddings - Ollama / OpenAI / Jina / SiliconFlow
 * Auto-fallback on failure. Reads from config.js (env vars or hardcoded)
 */
import { config } from './config.js';

const PROVIDERS = {};
for (const p of (config.embedProviders || [])) {
  PROVIDERS[p.name] = p;
}

function getProvider(name = 'ollama') {
  const p = PROVIDERS[name];
  if (!p) throw new Error(`Unknown embed provider: ${name}`);
  return p;
}

async function fetchEmbedding(text, providerName = 'ollama') {
  const p = getProvider(providerName);
  if (providerName === 'ollama') {
    const res = await fetch(`${p.baseURL}/api/embed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: p.model, input: text }),
      signal: AbortSignal.timeout(15000),
    });
    if (!res.ok) throw new Error(`Ollama error: ${res.status}`);
    const data = await res.json();
    return data.embeddings?.[0] || data.embedding || [];
  }
  // OpenAI / Jina / SiliconFlow compatible
  const apiKey = p.apiKey;
  if (!apiKey) throw new Error(`No API key for ${providerName}`);
  const res = await fetch(`${p.baseURL}/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
    body: JSON.stringify({ model: p.model, input: text }),
    signal: AbortSignal.timeout(20000),
  });
  if (!res.ok) throw new Error(`${providerName} error: ${res.status}`);
  const data = await res.json();
  return data.data?.[0]?.embedding || [];
}

/**
 * Get embedding with auto-fallback through providers
 * @param {string} text
 * @param {string[]} [providers]
 * @returns {Promise<number[]>}
 */
export async function getEmbedding(text, providers = ['ollama', 'openai', 'jina', 'siliconflow']) {
  for (const provider of providers) {
    try {
      const emb = await fetchEmbedding(text, provider);
      if (emb && emb.length > 0) return emb;
    } catch (e) {
      console.warn(`[embed_providers] ${provider} failed: ${e.message}`);
    }
  }
  throw new Error('All embedding providers failed');
}

export async function embedTexts(texts, provider = 'ollama', onProgress) {
  const results = [];
  for (let i = 0; i < texts.length; i++) {
    const emb = await fetchEmbedding(texts[i], provider);
    results.push(emb);
    if (onProgress) onProgress(i + 1, texts.length);
  }
  return results;
}

export default { getEmbedding, embedTexts };
