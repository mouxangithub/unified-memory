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

const defaultConfig = {
  memoryDir: MEMORY_DIR,
  memoryFile: join(MEMORY_DIR, 'memories.json'),
  vectorCacheDir: VECTOR_CACHE_DIR,
  logDir: LOG_DIR,
  ollamaUrl: process.env.OLLAMA_HOST || 'http://localhost:11434',
  embedModel: process.env.OLLAMA_EMBED_MODEL || 'nomic-embed-text:latest',
  llmModel: process.env.OLLAMA_LLM_MODEL || 'minimax-m2.7:cloud',
  topK: 10,
  rrfK: 60,
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
