/**
 * config.js - 配置管理
 */

import { readFileSync, existsSync, mkdirSync, appendFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const HOME = process.env.HOME || '/root';
const WORKSPACE = join(HOME, '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');
const VECTOR_CACHE_DIR = join(MEMORY_DIR, 'vector_cache');
const LOG_DIR = join(MEMORY_DIR, 'logs');

// ─── Provider 配置 ───
// Embedding providers: env var 或直接填值都行
const EMBED_PROVIDERS = [
  {
    name: 'ollama',
    baseURL: process.env.OLLAMA_BASE_URL || process.env.OLLAMA_HOST || 'http://localhost:11434',
    model: process.env.OLLAMA_EMBED_MODEL || 'nomic-embed-text',
    apiKey: null, // Ollama 不需要 key
  },
  {
    name: 'openai',
    baseURL: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
    model: process.env.OPENAI_EMBED_MODEL || 'text-embedding-3-small',
    apiKey: process.env.OPENAI_API_KEY || null,
  },
  {
    name: 'jina',
    baseURL: process.env.JINA_BASE_URL || 'https://api.jina.ai/v1',
    model: process.env.JINA_EMBED_MODEL || 'jina-embeddings-v3',
    apiKey: process.env.JINA_API_KEY || null,
  },
  {
    name: 'siliconflow',
    baseURL: process.env.SILICONFLOW_BASE_URL || 'https://api.siliconflow.cn/v1',
    model: process.env.SILICONFLOW_EMBED_MODEL || 'BAAI/bge-m3',
    apiKey: process.env.SILICONFLOW_API_KEY || null,
  },
];

// LLM providers
const LLM_PROVIDERS = [
  {
    name: 'ollama',
    baseURL: process.env.OLLAMA_BASE_URL || process.env.OLLAMA_HOST || 'http://localhost:11434',
    model: process.env.OLLAMA_LLM_MODEL || 'qwen2.5:7b',
    apiKey: null,
  },
  {
    name: 'openai',
    baseURL: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
    model: process.env.OPENAI_LLM_MODEL || 'gpt-4o-mini',
    apiKey: process.env.OPENAI_API_KEY || null,
  },
  {
    name: 'siliconflow',
    baseURL: process.env.SILICONFLOW_BASE_URL || 'https://api.siliconflow.cn/v1',
    model: process.env.SILICONFLOW_LLM_MODEL || 'Qwen/Qwen2.5-7B-Instruct',
    apiKey: process.env.SILICONFLOW_API_KEY || null,
  },
];

const defaultConfig = {
  memoryDir: MEMORY_DIR,
  memoryFile: join(MEMORY_DIR, 'memories.json'),
  vectorCacheDir: VECTOR_CACHE_DIR,
  logDir: LOG_DIR,
  logLevel: process.env.LOG_LEVEL || 'info',  // debug/info/warn/error
  topK: 10,
  rrfK: 60,
  embedProviders: EMBED_PROVIDERS,
  llmProviders: LLM_PROVIDERS,

  // ─── Phase 3: Search Backend ───
  qmd: {
    enabled: false,  // true = use QMD CLI, false = use built-in BM25+vector
    collections: ['workspace', 'daily-logs', 'projects', 'intelligence'],
  },

  // ─── Phase 3: Git Integration ───
  git: {
    enabled: false,
    repo_path: join(MEMORY_DIR, '.git-repo'),
    remote_url: null,
    auto_commit: false,  // auto-commit on each memory write
  },

  // ─── Phase 3: Cloud Backup ───
  cloud: {
    enabled: false,
    provider: 'supermemory',  // 'supermemory' | 'custom'
    supermemory_api_key: null,
    supermemory_endpoint: 'https://api.supermemory.ai',
    rest_endpoint: null,
    rest_api_key: null,
  },

  // ─── Phase 3: Weibull Decay ───
  weibull_decay: {
    shape: 1.5,   // 形状参数 k (1.0-3.0，越大记忆越持久)
    scale: 30,    // 尺度参数 λ（天数，越大衰减越慢）
  },
};

// Load config from file
function loadConfig() {
  const configFile = join(MEMORY_DIR, 'config.json');
  if (existsSync(configFile)) {
    try {
      return JSON.parse(readFileSync(configFile, 'utf-8'));
    } catch { }
  }
  return {};
}

export const config = { ...defaultConfig, ...loadConfig() };

// Ensure directories exist
for (const dir of [MEMORY_DIR, VECTOR_CACHE_DIR, LOG_DIR]) {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

export function log(/** @type {string} */ level, /** @type {string} */ msg) {
  const now = new Date().toISOString();
  const line = `[${now}] [${level}] ${msg}`;
  if (process.env.NODE_ENV !== 'test') {
    try {
      const logFile = join(LOG_DIR, `mcp-${new Date().toISOString().slice(0, 10)}.log`);
      appendFileSync(logFile, line + '\n');
    } catch { }
  }
  if (level === 'ERROR') {
    console.error(line);
  }
}
