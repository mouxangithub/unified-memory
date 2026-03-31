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

// ─── Embedding Queue + Batching (P2-4) ──────────────────────────────────────
// Debounce window (ms): collect texts for this long before sending one batch
const BATCH_WINDOW_MS = 100;
const MAX_BATCH_SIZE = 20;       // Max texts per Ollama /api/embed call
const BATCH_CONCURRENCY = 3;    // Max parallel Ollama requests

let _batchQueue = null;
let _batchTimer = null;
let _batchSemaphore = null;
let _semaphoreCount = 0;

/**
 * Acquire a semaphore slot for concurrent Ollama requests
 * @returns {Promise<void>}
 */
function acquireSemaphore() {
  return new Promise(resolve => {
    const tryAcquire = () => {
      if (_semaphoreCount < BATCH_CONCURRENCY) {
        _semaphoreCount++;
        resolve();
      } else {
        setTimeout(tryAcquire, 20);
      }
    };
    tryAcquire();
  });
}

/**
 * Release a semaphore slot
 */
function releaseSemaphore() {
  _semaphoreCount = Math.max(0, _semaphoreCount - 1);
}

/**
 * Flush one batch of texts to Ollama (called with semaphore held)
 * @param {string[]} batch
 * @param {object} p
 * @returns {Promise<Float32Array[]>}
 */
async function _flushBatch(batch, p) {
  try {
    const res = await fetch(`${p.baseURL}/api/embed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: batch }),
    });
    if (!res.ok) throw new Error(`Ollama batch embed failed: ${res.status}`);
    const data = await res.json();
    return data.embeddings || [];
  } catch (err) {
    console.warn('[embed_providers] Batch embed failed, falling back to individual:', err.message);
    // Fallback: embed one by one
    const results = [];
    for (const text of batch) {
      const emb = await fetchEmbedding(text, 'ollama');
      results.push(emb);
    }
    return results;
  } finally {
    releaseSemaphore();
  }
}

/**
 * Flush the current pending batch (called when timer fires or max size reached)
 */
async function _flushPendingBatch() {
  if (!_batchQueue || _batchQueue.texts.length === 0) return;
  const queue = _batchQueue;
  _batchQueue = null;
  _batchTimer = null;

  // Split into chunks of MAX_BATCH_SIZE
  const texts = queue.texts;
  const results = new Array(texts.length);

  // Process chunks in parallel within semaphore limit
  const chunks = [];
  for (let i = 0; i < texts.length; i += MAX_BATCH_SIZE) {
    chunks.push(texts.slice(i, i + MAX_BATCH_SIZE));
  }

  await Promise.all(
    chunks.map(async (chunk, chunkIdx) => {
      const baseIdx = chunkIdx * MAX_BATCH_SIZE;
      await acquireSemaphore();
      try {
        const embeddings = await _flushBatch(chunk, queue.provider);
        for (let j = 0; j < chunk.length; j++) {
          results[baseIdx + j] = embeddings[j];
        }
      } catch (err) {
        // Fill with zeros on complete failure
        for (let j = 0; j < chunk.length; j++) {
          results[baseIdx + j] = new Float32Array(768).fill(0);
        }
      }
    })
  );

  queue.resolve(results);
}

/**
 * Embed multiple texts using queued + batched Ollama requests (P2-4 fix).
 * Uses debounce batching: texts arriving within BATCH_WINDOW_MS are collected
 * and sent as a single /api/embed call. Falls back to individual requests
 * if Ollama doesn't support batching.
 *
 * @param {string[]} texts
 * @param {string} provider
 * @param {function} onProgress
 * @returns {Promise<Float32Array[]>}
 */
export async function embedTexts(texts, provider = 'ollama', onProgress) {
  if (!texts || texts.length === 0) return [];
  if (texts.length === 1) {
    // Fast path: no batching needed for single text
    const emb = await fetchEmbedding(texts[0], provider);
    if (onProgress) onProgress(1, 1);
    return [emb];
  }

  // Initialize batch queue on first call
  if (!_batchQueue) {
    _batchQueue = { texts: [], resolve: null };
  }

  // If a batch is already being processed, fall back to individual requests
  if (_batchTimer !== null) {
    clearTimeout(_batchTimer);
    _batchTimer = null;
  }

  // Queue all texts
  const startIdx = _batchQueue.texts.length;
  _batchQueue.texts.push(...texts);

  // If queue exceeds MAX_BATCH_SIZE, flush immediately
  if (_batchQueue.texts.length >= MAX_BATCH_SIZE) {
    return new Promise(async (resolve) => {
      _batchQueue.resolve = resolve;
      await _flushPendingBatch();
    });
  }

  // Otherwise debounce
  return new Promise((resolve) => {
    _batchQueue.resolve = (results) => {
      if (onProgress) onProgress(texts.length, texts.length);
      resolve(results);
    };
    if (_batchTimer) clearTimeout(_batchTimer);
    _batchTimer = setTimeout(() => _flushPendingBatch(), BATCH_WINDOW_MS);
  });
}

export default { getEmbedding, embedTexts };
