/**
 * LanceDB Vector Store - True persistent vector database for unified-memory
 * Uses embedded LanceDB with nomic-embed-text (768-dim) embeddings
 *
 * Features:
 * - Embedded LanceDB at ~/.unified-memory/vector.lance
 * - IVF_PQ ANN index on vector column
 * - Batch upsert by id (mergeInsert)
 * - nomic-embed-text via TransformersEmbeddingFunction
 */

import { connect } from '@lancedb/lancedb';
import { TransformersEmbeddingFunction } from '@lancedb/lancedb/embedding/transformers';
import { Schema, Float32, Int64, Utf8 } from 'apache-arrow';
import { dirname, join } from 'path';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const VECTOR_DB_DIR = join(process.env.HOME || '/root', '.unified-memory', 'vector.lance');
const TABLE_NAME = 'memories';
const DIMENSIONS = 768;

// Singleton embedding function (nomic-embed-text)
let _embeddingFunction = null;

async function getEmbeddingFunction() {
  if (_embeddingFunction === null) {
    _embeddingFunction = new TransformersEmbeddingFunction({
      model: 'nomic-ai/nomic-embed-text-v1.5',
    });
    await _embeddingFunction.init();
  }
  return _embeddingFunction;
}

/**
 * LanceDB Vector Store class
 * Provides ANN vector search backed by LanceDB with IVF_PQ indexing
 */
export class VectorMemory {
  constructor(uri = VECTOR_DB_DIR) {
    this.uri = uri;
    this._db = null;
    this._table = null;
    this._initialized = false;
  }

  /** Initialize LanceDB connection, create table + ANN index if needed */
  async initialize() {
    if (this._initialized) return;

    // Ensure directory exists
    if (!existsSync(this.uri)) {
      mkdirSync(this.uri, { recursive: true });
    }

    // Connect to embedded LanceDB
    this._db = await connect(this.uri);

    // Check if table exists, create if not
    const tableNames = await this._db.tableNames();
    if (!tableNames.includes(TABLE_NAME)) {
      const embeddingFunc = await getEmbeddingFunction();

      // Define explicit Arrow schema for the table
      const schema = new Schema([
        { name: 'id', type: new Utf8(), nullable: false },
        { name: 'text', type: new Utf8(), nullable: false },
        { name: 'category', type: new Utf8(), nullable: false },
        { name: 'scope', type: new Utf8(), nullable: false },
        { name: 'importance', type: new Float32(), nullable: false },
        { name: 'created_at', type: new Int64(), nullable: false },
      ]);

      // Create empty table with schema and embedding function
      // LanceDB will auto-create the vector column from the embedding function
      this._table = await this._db.createEmptyTable(TABLE_NAME, schema, {
        embeddingFunction: embeddingFunc,
      });

      // Create ANN index (IVF_PQ) on the vector column for fast ANN search
      try {
        await this._table.createIndex('vector', {
          type: 'ivf',
          numPartitions: 128,
          numSubVectors: 96,
        });
      } catch (e) {
        // Index creation may fail on empty table; that's ok
        console.warn('[vector_lancedb] Index creation warning:', e.message);
      }
    } else {
      this._table = await this._db.openTable(TABLE_NAME);
    }

    this._initialized = true;
    console.log(`[vector_lancedb] Initialized at ${this.uri}, table: ${TABLE_NAME}`);
  }

  /**
   * Add or update a vector entry (upsert by id)
   * @param {string} id - Unique memory id
   * @param {string} text - Memory text content
   * @param {number[]} embedding - 768-dim float32 vector
   * @param {object} metadata - { category, scope, importance, created_at }
   */
  async addVector(id, text, embedding, metadata = {}) {
    await this.initialize();
    if (!embedding || embedding.length !== DIMENSIONS) {
      throw new Error(`Embedding must be ${DIMENSIONS}-dimensional float array`);
    }

    const record = {
      id,
      text,
      vector: embedding,
      category: metadata.category || 'general',
      scope: metadata.scope || 'agent',
      importance: metadata.importance ?? 0.5,
      created_at: BigInt(metadata.created_at ?? Date.now()),
    };

    // Use mergeInsert (upsert) - if id exists, update; otherwise insert
    try {
      await this._table
        .mergeInsert(['id'])
        .values([record])
        .map(({ inserted }) => inserted)
        .execute();
    } catch (e) {
      // Fallback: delete then insert on mergeInsert failure
      try {
        await this._table.delete(`id = "${id}"`);
      } catch {
        // ignore
      }
      await this._table.add([record]);
    }
  }

  /**
   * Batch upsert vectors
   * @param {Array<{id, text, embedding, metadata}>} records
   */
  async addVectors(records) {
    await this.initialize();
    for (const r of records) {
      await this.addVector(r.id, r.text, r.embedding, r.metadata);
    }
  }

  /**
   * Search ANN vectors by embedding
   * @param {number[]} queryEmbedding - 768-dim query vector
   * @param {number} topK - Number of results to return
   * @returns {Array<{id, text, score, metadata}>}
   */
  async searchVectors(queryEmbedding, topK = 10) {
    await this.initialize();
    if (!queryEmbedding || queryEmbedding.length !== DIMENSIONS) {
      throw new Error(`Query embedding must be ${DIMENSIONS}-dimensional float array`);
    }

    const results = await this._table
      .query()
      .nearestTo(queryEmbedding)
      .limit(topK)
      .execute();

    return results.map((row) => ({
      id: row.id,
      text: row.text,
      score: row._score ?? row.score ?? 0,
      metadata: {
        category: row.category,
        scope: row.scope,
        importance: row.importance,
        created_at: Number(row.created_at),
      },
    }));
  }

  /**
   * Delete a vector by id
   * @param {string} id
   */
  async deleteVector(id) {
    await this.initialize();
    await this._table.delete(`id = "${id}"`);
  }

  /**
   * Get a vector by id
   * @param {string} id
   * @returns {{id, text, embedding, metadata}|null}
   */
  async getVector(id) {
    await this.initialize();
    const results = await this._table
      .query()
      .where(`id = "${id}"`)
      .limit(1)
      .execute();

    if (results.length === 0) return null;
    const row = results[0];
    return {
      id: row.id,
      text: row.text,
      embedding: row.vector,
      metadata: {
        category: row.category,
        scope: row.scope,
        importance: row.importance,
        created_at: Number(row.created_at),
      },
    };
  }

  /** Get total count of vectors in the store */
  async count() {
    await this.initialize();
    return await this._table.countRows();
  }
}

// Singleton instance
let _instance = null;

export function getVectorStore() {
  if (_instance === null) {
    _instance = new VectorMemory();
  }
  return _instance;
}

// ============ Compatibility layer for vector.js API ============

const vectorStore = new VectorMemory();

/**
 * Get embedding for text using nomic-embed-text via TransformersEmbeddingFunction
 * @param {string} text
 * @returns {Promise<number[]|null>}
 */
export async function getEmbedding(text) {
  try {
    const func = await getEmbeddingFunction();
    const embeddings = await func.computeQueryEmbeddings([text]);
    return embeddings[0] ?? null;
  } catch (e) {
    console.error('[vector_lancedb] getEmbedding error:', e.message);
    return null;
  }
}

function hashText(text) {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash).toString(36);
}

/**
 * Get embedding with file caching (backward compatible)
 * @param {string} text
 * @returns {Promise<number[]|null>}
 */
export async function getEmbeddingCached(text) {
  const cacheDir = join(VECTOR_DB_DIR, '..', 'embeddings');
  const hash = hashText(text);
  const cacheFile = join(cacheDir, `${hash}.json`);

  if (existsSync(cacheFile)) {
    try {
      const cached = JSON.parse(readFileSync(cacheFile, 'utf8'));
      return cached.embedding;
    } catch {
      // ignore
    }
  }

  const embedding = await getEmbedding(text);
  if (embedding) {
    try {
      if (!existsSync(cacheDir)) mkdirSync(cacheDir, { recursive: true });
      writeFileSync(cacheFile, JSON.stringify({ embedding, text: text.slice(0, 100) }), 'utf8');
    } catch {
      // ignore
    }
  }
  return embedding;
}

/**
 * Vector search using LanceDB ANN (backward compatible with vector.js API)
 * @param {string} query
 * @param {number} topK
 * @returns {Promise<Array<{memory: object, score: number, highlight: string}>>}
 */
export async function vectorSearch(query, topK = 10) {
  const queryEmbedding = await getEmbeddingCached(query);
  if (!queryEmbedding) return [];

  const results = await vectorStore.searchVectors(queryEmbedding, topK);

  return results.map((r) => {
    let highlight = r.text.slice(0, 150);
    if (r.text.length > 150) highlight += '...';
    return {
      memory: {
        id: r.id,
        text: r.text,
        category: r.metadata.category,
        importance: r.metadata.importance,
        created_at: r.metadata.created_at,
      },
      score: r.score,
      highlight,
    };
  });
}
