// hybrid-search.js - 混合搜索模块
// BM25 + 向量搜索 + RRF (Reciprocal Rank Fusion)
// 位置: /root/.openclaw/skills/unified-memory/hybrid-search.js

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ========== 工具函数 ==========

/**
 * 简单的中文/英文分词器
 * 支持中英文混合文本
 */
function tokenize(text) {
  if (!text) return [];
  
  // 中文：按字符拆分，保留 2 字以上词组
  const chinesePattern = /[\u4e00-\u9fff]+/g;
  // 英文/数字：按单词分割
  const englishPattern = /[a-zA-Z0-9_]+/g;
  
  const tokens = [];
  
  // 提取中文词
  let lastIndex = 0;
  let match;
  const textCopy = text;
  
  // 处理中文字符序列 - 滑动窗口取 2-4 字词
  while ((match = chinesePattern.exec(text)) !== null) {
    const chinesePart = match[0];
    // 滑动窗口提取 2-4 字词
    for (let len = 2; len <= 4 && len <= chinesePart.length; len++) {
      for (let i = 0; i <= chinesePart.length - len; i++) {
        tokens.push(chinesePart.slice(i, i + len));
      }
    }
  }
  
  // 提取英文词
  while ((match = englishPattern.exec(text)) !== null) {
    const word = match[0].toLowerCase();
    if (word.length > 1) {
      tokens.push(word);
    }
  }
  
  return tokens;
}

// 停用词列表
const STOPWORDS = new Set([
  '的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
  '或', '一个', '没有', '我们', '你们', '他们', '她们', '它们',
  '这个', '那个', '这些', '那些', '自己', '什么', '怎么', '怎样',
  'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
  'could', 'should', 'may', 'might', 'must', 'shall', 'can',
  'of', 'in', 'to', 'for', 'with', 'on', 'at', 'by', 'from',
  'up', 'out', 'about', 'into', 'through', 'during', 'before',
  'after', 'above', 'below', 'between', 'under', 'again',
  'further', 'then', 'once', 'here', 'there', 'when', 'where',
  'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
  'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
  'so', 'than', 'too', 'very', 'just', 'but', 'also', 'if',
  'or', 'because', 'as', 'until', 'while', 'although',
  'though', 'since', 'this', 'that', 'these', 'those',
  'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
  'you', 'your', 'yours', 'yourself', 'yourselves',
  'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
  'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
  'themselves', 'what', 'which', 'who', 'whom', 'when', 'where',
  'why', 'how'
]);

function removeStopwords(tokens) {
  return tokens.filter(t => !STOPWORDS.has(t));
}

// ========== BM25 搜索引擎 ==========

class BM25Engine {
  constructor(documents = [], options = {}) {
    this.documents = documents;
    this.k1 = options.k1 || 1.5;        // BM25 k1 参数
    this.b = options.b || 0.75;         // BM25 b 参数
    this.avgDocLength = 0;
    this.docLengths = [];
    this.termFreq = [];                 // 每个文档的词频
    this.inverseDocFreq = {};           // IDF 表
    this.vocabulary = new Set();
    this._buildIndex();
  }

  _buildIndex() {
    if (this.documents.length === 0) return;

    // 计算平均文档长度
    const totalLength = this.documents.reduce((sum, doc) => {
      const tokens = removeStopwords(tokenize(doc.content || doc.text || ''));
      this.docLengths.push(tokens.length);
      return sum + tokens.length;
    }, 0);
    this.avgDocLength = totalLength / this.documents.length;

    // 构建词频和逆文档频率
    const docCount = this.documents.length;
    const termDocCount = {};

    this.documents.forEach((doc, docId) => {
      const tokens = removeStopwords(tokenize(doc.content || doc.text || ''));
      const freq = {};
      
      tokens.forEach(token => {
        this.vocabulary.add(token);
        freq[token] = (freq[token] || 0) + 1;
      });
      
      this.termFreq[docId] = freq;

      // 统计词出现在多少文档中
      Object.keys(freq).forEach(term => {
        termDocCount[term] = (termDocCount[term] || 0) + 1;
      });
    });

    // 计算 IDF
    Object.entries(termDocCount).forEach(([term, count]) => {
      // BM25 IDF 公式：log((N - n + 0.5) / (n + 0.5))
      this.inverseDocFreq[term] = Math.log((docCount - count + 0.5) / (count + 0.5) + 1);
    });
  }

  /**
   * 计算单个文档对查询的 BM25 得分
   */
  _scoreDoc(queryTokens, docId) {
    const docFreq = this.termFreq[docId];
    const docLength = this.docLengths[docId] || 1;
    let score = 0;

    queryTokens.forEach(term => {
      if (!this.vocabulary.has(term)) return;
      
      const tf = docFreq[term] || 0;
      if (tf === 0) return;

      const idf = this.inverseDocFreq[term] || 0;
      
      // BM25 公式：IDF * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |d| / avgdl))
      const numerator = tf * (this.k1 + 1);
      const denominator = tf + this.k1 * (1 - this.b + this.b * docLength / this.avgDocLength);
      
      score += idf * numerator / denominator;
    });

    return score;
  }

  /**
   * 搜索接口
   * @param {string} query - 查询文本
   * @param {number} limit - 返回结果数量
   * @returns {Array} 排序后的结果
   */
  search(query, limit = 10) {
    const queryTokens = removeStopwords(tokenize(query));
    if (queryTokens.length === 0) return [];

    const scores = this.documents.map((doc, docId) => ({
      docId,
      doc,
      score: this._scoreDoc(queryTokens, docId)
    }));

    return scores
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(item => ({
        ...item.doc,
        bm25Score: item.score,
        matchedTerms: queryTokens.filter(t => (this.termFreq[item.docId] || {})[t] > 0)
      }));
  }

  /**
   * 添加文档到索引（增量更新）
   */
  addDocument(doc) {
    const docId = this.documents.length;
    this.documents.push(doc);
    
    const tokens = removeStopwords(tokenize(doc.content || doc.text || ''));
    this.docLengths.push(tokens.length);
    
    const freq = {};
    tokens.forEach(token => {
      this.vocabulary.add(token);
      freq[token] = (freq[token] || 0) + 1;
    });
    this.termFreq[docId] = freq;

    // 更新 IDF（简化：重新计算受影响的词）
    const termCount = {};
    Object.keys(freq).forEach(term => termCount[term] = 1);
    Object.entries(termCount).forEach(([term]) => {
      let count = 0;
      this.documents.forEach((_, i) => {
        if ((this.termFreq[i] || {})[term]) count++;
      });
      const n = count;
      const N = this.documents.length;
      this.inverseDocFreq[term] = Math.log((N - n + 0.5) / (n + 0.5) + 1);
    });

    // 更新平均长度
    const totalLength = this.docLengths.reduce((a, b) => a + b, 0);
    this.avgDocLength = totalLength / this.documents.length;
  }

  getStats() {
    return {
      docCount: this.documents.length,
      vocabSize: this.vocabulary.size,
      avgDocLength: this.avgDocLength.toFixed(2),
      idfEntries: Object.keys(this.inverseDocFreq).length
    };
  }
}

// ========== 向量搜索原型 ==========

/**
 * 简化的向量搜索
 * 使用预计算的嵌入或模拟嵌入
 * 预留了真实嵌入模型的接口
 */
class VectorSearchEngine {
  constructor(documents = [], options = {}) {
    this.documents = documents;
    this.dimension = options.dimension || 384;  // 默认嵌入维度
    this.embeddings = [];                        // 预计算嵌入
    this.embeddingCache = new Map();             // 查询嵌入缓存
    this.useSimulated = options.useSimulated !== false;  // 默认使用模拟嵌入
    this._buildIndex();
  }

  /**
   * 模拟嵌入生成（基于词哈希的简单嵌入）
   * 真实场景中应使用 OpenAI embeddings / BGE / M3 等模型
   */
  _simulateEmbedding(text) {
    const tokens = removeStopwords(tokenize(text));
    const vector = new Array(this.dimension).fill(0);
    
    // 简单的基于词的哈希嵌入
    tokens.forEach((token, i) => {
      let hash = 0;
      for (let j = 0; j < token.length; j++) {
        hash = ((hash << 5) - hash) + token.charCodeAt(j);
        hash = hash & hash;
      }
      
      // 用哈希值填充向量
      const seed = Math.abs(hash);
      for (let d = 0; d < this.dimension; d++) {
        // 简单的伪随机分布
        vector[d] += Math.sin((seed * (d + 1) * 0.1) % 1) * 0.1;
      }
    });
    
    // 归一化
    const magnitude = Math.sqrt(vector.reduce((sum, v) => sum + v * v, 0));
    if (magnitude > 0) {
      for (let d = 0; d < this.dimension; d++) {
        vector[d] /= magnitude;
      }
    }
    
    return vector;
  }

  _buildIndex() {
    this.documents.forEach((doc, docId) => {
      const text = doc.content || doc.text || '';
      if (this.useSimulated) {
        this.embeddings[docId] = this._simulateEmbedding(text);
      }
      // 真实嵌入：embeddings[docId] = await externalEmbeddingAPI(text)
    });
  }

  /**
   * 计算余弦相似度
   */
  _cosineSimilarity(a, b) {
    if (a.length !== b.length) return 0;
    
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;
    
    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i];
      normA += a[i] * a[i];
      normB += b[i] * b[i];
    }
    
    const denom = Math.sqrt(normA) * Math.sqrt(normB);
    return denom === 0 ? 0 : dotProduct / denom;
  }

  /**
   * 搜索接口
   * @param {string} query - 查询文本
   * @param {number} limit - 返回结果数量
   * @returns {Array} 排序后的结果
   */
  search(query, limit = 10) {
    // 缓存查询嵌入
    let queryEmbedding = this.embeddingCache.get(query);
    if (!queryEmbedding) {
      queryEmbedding = this._simulateEmbedding(query);
      this.embeddingCache.set(query, queryEmbedding);
    }

    const scores = this.documents.map((doc, docId) => ({
      docId,
      doc,
      score: this._cosineSimilarity(queryEmbedding, this.embeddings[docId])
    }));

    return scores
      .filter(item => item.score > 0.01)  // 过滤低分
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(item => ({
        ...item.doc,
        vectorScore: item.score
      }));
  }

  /**
   * 添加文档
   */
  addDocument(doc) {
    const docId = this.documents.length;
    this.documents.push(doc);
    
    const text = doc.content || doc.text || '';
    this.embeddings[docId] = this._simulateEmbedding(text);
  }

  getStats() {
    return {
      docCount: this.documents.length,
      dimension: this.dimension,
      cachedQueries: this.embeddingCache.size,
      mode: this.useSimulated ? 'simulated' : 'production'
    };
  }
}

// ========== RRF 融合 ==========

/**
 * Reciprocal Rank Fusion - 多路搜索结果融合
 * 
 * RRF 公式：score(d) = Σ 1 / (k + rank(d))
 * - k: 常数（通常 60）
 * - rank(d): 文档在第 i 路结果中的排名（从 1 开始）
 */
class RRFFusion {
  constructor(options = {}) {
    this.k = options.k || 60;  // RRF 常数
  }

  /**
   * 融合多路搜索结果
   * @param {Array<Array>} resultSets - 多路搜索结果，每路是排序后的文档数组
   * @param {Object} weights - 各路权重（可选）
   * @returns {Array} 融合后的排序结果
   */
  fuse(resultSets, weights = {}) {
    if (!resultSets || resultSets.length === 0) return [];
    
    // 文档得分映射：docId -> {doc, rrfScore, sources}
    const docScores = new Map();

    resultSets.forEach((results, setIndex) => {
      const weight = weights[setIndex] || 1;
      
      results.forEach((result, rank) => {
        const docId = result.id || result.docId || JSON.stringify(result);
        
        if (!docScores.has(docId)) {
          docScores.set(docId, {
            doc: result,
            rrfScore: 0,
            sources: []
          });
        }
        
        const entry = docScores.get(docId);
        // RRF 得分 = 权重 * 1 / (k + rank)
        const rrfContribution = weight / (this.k + rank + 1);
        entry.rrfScore += rrfContribution;
        entry.sources.push({
          setIndex,
          rank,
          score: result.bm25Score || result.vectorScore || 0
        });
      });
    });

    // 按 RRF 得分排序
    return Array.from(docScores.values())
      .sort((a, b) => b.rrfScore - a.rrfScore)
      .map(item => ({
        ...item.doc,
        rrfScore: item.rrfScore,
        sourceCount: item.sources.length,
        sources: item.sources
      }));
  }

  /**
   * 设置 RRF k 参数
   */
  setK(k) {
    this.k = k;
  }
}

// ========== 混合搜索引擎 ==========

class HybridSearchEngine {
  constructor(options = {}) {
    this.documents = [];
    this.bm25 = null;
    this.vector = null;
    this.rrf = new RRFFusion({ k: options.rrfK || 60 });
    this.cache = new Map();
    this.maxCacheSize = options.maxCacheSize || 500;
    this.stats = {
      searches: 0,
      cacheHits: 0,
      cacheMisses: 0,
      avgLatency: 0
    };
  }

  /**
   * 初始化（批量添加文档）
   */
  async initialize(documents) {
    this.documents = documents || [];
    
    // 初始化 BM25
    this.bm25 = new BM25Engine(this.documents);
    
    // 初始化向量搜索（使用模拟嵌入）
    this.vector = new VectorSearchEngine(this.documents, {
      dimension: 384,
      useSimulated: true
    });
    
    return this;
  }

  /**
   * 添加单条记忆
   */
  addMemory(memory) {
    this.documents.push(memory);
    if (this.bm25) this.bm25.addDocument(memory);
    if (this.vector) this.vector.addDocument(memory);
    this.cache.clear();  // 使缓存失效
  }

  /**
   * 混合搜索入口
   * @param {string} query - 查询文本
   * @param {Object} options - 配置选项
   * @returns {Array} 融合后的结果
   */
  async search(query, options = {}) {
    const limit = options.limit || 10;
    const weights = options.weights || { bm25: 0.5, vector: 0.5 };
    const useCache = options.useCache !== false;
    const startTime = Date.now();

    this.stats.searches++;

    // 检查缓存
    const cacheKey = `${query}:${limit}:${JSON.stringify(weights)}`;
    if (useCache && this.cache.has(cacheKey)) {
      this.stats.cacheHits++;
      return this.cache.get(cacheKey);
    }
    this.stats.cacheMisses++;

    // 并行执行两路搜索
    const [bm25Results, vectorResults] = await Promise.all([
      Promise.resolve(this.bm25.search(query, limit * 2)),
      Promise.resolve(this.vector.search(query, limit * 2))
    ]);

    // RRF 融合
    const resultSets = [bm25Results, vectorResults];
    const weightedResultSets = resultSets; // weights 在 RRF 内部处理
    const fusedResults = this.rrf.fuse(resultSets, [weights.bm25, weights.vector]);

    // 截取 limit 条
    const finalResults = fusedResults.slice(0, limit);

    // 缓存结果
    if (useCache && this.cache.size < this.maxCacheSize) {
      this.cache.set(cacheKey, finalResults);
    }

    // 记录性能
    const latency = Date.now() - startTime;
    this.stats.avgLatency = (this.stats.avgLatency * (this.stats.searches - 1) + latency) / this.stats.searches;

    return finalResults;
  }

  /**
   * 只用 BM25 搜索
   */
  searchBM25(query, limit = 10) {
    return this.bm25.search(query, limit);
  }

  /**
   * 只用向量搜索
   */
  searchVector(query, limit = 10) {
    return this.vector.search(query, limit);
  }

  /**
   * 清除缓存
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      ...this.stats,
      cacheSize: this.cache.size,
      totalDocs: this.documents.length,
      bm25: this.bm25?.getStats(),
      vector: this.vector?.getStats(),
      rrfK: this.rrf.k
    };
  }
}

// ========== 性能基准测试 ==========

async function benchmark(searchEngine, testQueries, iterations = 5) {
  const results = [];
  
  for (const query of testQueries) {
    const latencies = [];
    
    for (let i = 0; i < iterations; i++) {
      const start = Date.now();
      await searchEngine.search(query, { limit: 10, useCache: false });
      latencies.push(Date.now() - start);
    }
    
    const avgLatency = latencies.reduce((a, b) => a + b, 0) / iterations;
    const minLatency = Math.min(...latencies);
    const maxLatency = Math.max(...latencies);
    
    results.push({
      query,
      avgLatency: avgLatency.toFixed(2),
      minLatency,
      maxLatency,
      p95: latencies.sort((a, b) => a - b)[Math.floor(latencies.length * 0.95)] || avgLatency
    });
  }
  
  return results;
}

// ========== 使用示例和测试 ==========

async function main() {
  console.log('🔍 Unified Memory 混合搜索测试\n');
  console.log('=' .repeat(60));

  // 加载测试数据
  const memoryFile = path.join(__dirname, 'memory', 'memories.json');
  let documents = [];
  
  if (fs.existsSync(memoryFile)) {
    documents = JSON.parse(fs.readFileSync(memoryFile, 'utf8'));
    console.log(`📂 加载记忆: ${documents.length} 条\n`);
  } else {
    // 使用内置测试数据
    documents = [
      { id: '1', content: '刘选权决定直接使用 unified-memory 完整版', tags: ['决策'], category: '系统决策' },
      { id: '2', content: '并行实施加快项目进度', tags: ['实施'], category: '项目规划' },
      { id: '3', content: 'BM25 算法用于文本搜索', tags: ['算法'], category: '技术' },
      { id: '4', content: '向量搜索使用嵌入模型', tags: ['向量'], category: '技术' },
      { id: '5', content: 'RRF 融合多路搜索结果', tags: ['融合'], category: '技术' }
    ];
    console.log(`📂 使用内置测试数据: ${documents.length} 条\n`);
  }

  // 初始化搜索引擎
  console.log('⚙️  初始化混合搜索引擎...\n');
  const searchEngine = new HybridSearchEngine({ rrfK: 60 });
  await searchEngine.initialize(documents);

  // 显示引擎统计
  const stats = searchEngine.getStats();
  console.log('📊 引擎统计:');
  console.log(`   文档数: ${stats.totalDocs}`);
  console.log(`   BM25 词表大小: ${stats.bm25?.vocabSize}`);
  console.log(`   向量维度: ${stats.vector?.dimension}`);
  console.log(`   RRF k 值: ${stats.rrfK}\n`);

  // 测试查询
  const testQueries = [
    '刘选权 决策',
    'unified-memory 实施',
    'BM25 算法',
    '向量搜索 嵌入',
    'RRF 融合'
  ];

  console.log('=' .repeat(60));
  console.log('🧪 搜索测试\n');

  for (const query of testQueries) {
    console.log(`查询: "${query}"`);
    
    // 混合搜索
    const results = await searchEngine.search(query, { limit: 5 });
    console.log(`  混合搜索结果 (${results.length} 条):`);
    results.slice(0, 3).forEach((r, i) => {
      const preview = (r.content || '').substring(0, 50);
      console.log(`    ${i + 1}. [${r.rrfScore?.toFixed(4)}] ${preview}...`);
    });
    
    // 单路搜索对比
    const bm25Only = searchEngine.searchBM25(query, 3);
    const vecOnly = searchEngine.searchVector(query, 3);
    console.log(`  BM25 单独: ${bm25Only.length} 条, 向量单独: ${vecOnly.length} 条`);
    console.log();
  }

  // 性能基准测试
  console.log('=' .repeat(60));
  console.log('⚡ 性能基准测试\n');

  const benchResults = await benchmark(searchEngine, testQueries, 10);
  
  console.log('查询'.padEnd(25), '平均', '最小', '最大', 'P95');
  console.log('-'.repeat(60));
  
  benchResults.forEach(r => {
    console.log(
      r.query.padEnd(25),
      `${r.avgLatency}ms`.padEnd(8),
      `${r.minLatency}ms`.padEnd(6),
      `${r.maxLatency}ms`.padEnd(6),
      `${r.p95}ms`
    );
  });

  // 最终统计
  console.log('\n' + '=' .repeat(60));
  console.log('📈 最终统计\n');
  
  const finalStats = searchEngine.getStats();
  console.log(`   总搜索次数: ${finalStats.searches}`);
  console.log(`   缓存命中: ${finalStats.cacheHits}`);
  console.log(`   缓存未命中: ${finalStats.cacheMisses}`);
  console.log(`   缓存命中率: ${finalStats.cacheHits + finalStats.cacheMisses > 0 
    ? ((finalStats.cacheHits / (finalStats.cacheHits + finalStats.cacheMisses)) * 100).toFixed(1) + '%' 
    : 'N/A'}`);
  console.log(`   平均延迟: ${finalStats.avgLatency.toFixed(2)}ms`);
  console.log(`   缓存大小: ${finalStats.cacheSize}`);

  console.log('\n✅ 混合搜索测试完成！\n');

  return searchEngine;
}

// 导出模块
export { 
  HybridSearchEngine,
  BM25Engine, 
  VectorSearchEngine, 
  RRFFusion,
  tokenize,
  removeStopwords,
  benchmark
};

// 如果直接运行，执行测试
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch(console.error);
}
