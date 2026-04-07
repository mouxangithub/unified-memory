/**
 * Memory Recall Evaluation - Benchmark Suite
 * Evaluates recall@K, precision@K, MRR on memory retrieval
 * 
 * Based on LoCoMo / LongMemEval methodology
 */

import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const WORKSPACE = join(process.env.HOME || '/root', '.openclaw', 'workspace');
const MEMORY_DIR = join(WORKSPACE, 'memory');
const RESULTS_DIR = join(__dirname, 'results');

// ============ Types ============

/**
 * @typedef {Object} TestCase
 * @property {string} query
 * @property {string[]} relevant_ids  - memory IDs that should be recalled
 * @property {string} category      - test category
 */

/**
 * @typedef {Object} EvalResult
 * @property {string} query
 * @property {string[]} retrieved_ids
 * @property {string[]} relevant_ids
 * @property {number} recall@k
 * @property {number} precision@k
 * @property {number} mrr
 */

/**
 * @typedef {Object} BenchmarkReport
 * @property {string} timestamp
 * @property {number} total_queries
 * @property {number} recall@1
 * @property {number} recall@5
 * @property {number} recall@10
 * @property {number} precision@1
 * @property {number} precision@5
 * @property {number} mrr
 * @property {EvalResult[]} results
 */

// ============ Seed Dataset ============

/**
 * Seed memory dataset for benchmark
 * Format: { query: string, relevant_ids: string[], category: string }
 */
const SEED_DATASET = [
  // User preferences
  {
    query: '用户喜欢用哪个编程工具',
    relevant_ids: [],
    category: 'preference',
    description: 'Should recall tool preferences'
  },
  {
    query: '用户的工作风格是什么样的',
    relevant_ids: [],
    category: 'workstyle',
    description: 'Should recall work style preferences'
  },
  // Project context
  {
    query: '正在进行什么项目',
    relevant_ids: [],
    category: 'project',
    description: 'Should recall active projects'
  },
  {
    query: '最近的开发任务进展如何',
    relevant_ids: [],
    category: 'task',
    description: 'Should recall recent tasks'
  },
  // Identity
  {
    query: '用户的基本信息',
    relevant_ids: [],
    category: 'identity',
    description: 'Should recall user identity'
  },
  {
    query: '用户的姓名和联系方式',
    relevant_ids: [],
    category: 'identity',
    description: 'Should recall name and contact'
  },
  // Skills
  {
    query: '用户擅长什么技术',
    relevant_ids: [],
    category: 'skill',
    description: 'Should recall technical skills'
  },
  // Communication
  {
    query: '用户喜欢什么样的沟通方式',
    relevant_ids: [],
    category: 'communication',
    description: 'Should recall communication preferences'
  },
];

// ============ Data Loading ============

/**
 * Load memories from storage
 */
function loadMemories() {
  const memoriesFile = join(MEMORY_DIR, 'memories.json');
  if (!existsSync(memoriesFile)) {
    return [];
  }
  try {
    return JSON.parse(readFileSync(memoriesFile, 'utf-8'));
  } catch {
    return [];
  }
}

/**
 * Load memories from markdown files (HOT/WARM/COLD tiers)
 */
function loadMemoryFiles() {
  const memories = [];
  const tiers = ['hot', 'warm', 'cold'];
  
  for (const tier of tiers) {
    const tierDir = join(MEMORY_DIR, tier);
    if (!existsSync(tierDir)) continue;
    
    try {
      const files = require('fs').readdirSync(tierDir) || [];
      for (const file of files) {
        if (file.endsWith('.md')) {
          const content = readFileSync(join(tierDir, file), 'utf-8');
          // Parse frontmatter + content
          const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
          if (frontmatterMatch) {
            const fm = frontmatterMatch[1];
            const text = frontmatterMatch[2];
            const idMatch = fm.match(/id:\s*(.+)/);
            const scopeMatch = fm.match(/scope:\s*(.+)/);
            const categoryMatch = fm.match(/category:\s*(.+)/);
            
            memories.push({
              id: idMatch ? idMatch[1].trim() : file.replace('.md', ''),
              text: text.trim(),
              scope: scopeMatch ? scopeMatch[1].trim() : 'agent',
              category: categoryMatch ? categoryMatch[1].trim() : 'general',
            });
          }
        }
      }
    } catch {
      // Tier dir might not exist
    }
  }
  
  return memories;
}

// ============ Retrieval (Simplified BM25 fallback) ============

/**
 * Simple BM25-like retrieval for benchmark
 * In production, this would call the actual hybrid search
 */
function retrieveMemories(query, memories, limit = 10) {
  const queryTerms = query.toLowerCase().split(/\s+/);
  
  const scored = memories.map(m => {
    const text = (m.text || '').toLowerCase();
    let score = 0;
    
    for (const term of queryTerms) {
      if (text.includes(term)) {
        score += 1;
        // Boost exact matches
        if (text.includes(query.toLowerCase())) {
          score += 2;
        }
      }
    }
    
    return { id: m.id, score, text: m.text };
  });
  
  return scored
    .filter(m => m.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(m => m.id);
}

// ============ Metrics ============

/**
 * Calculate Recall@K
 */
function recallAtK(retrieved, relevant, k) {
  const retrievedK = retrieved.slice(0, k);
  const relevantSet = new Set(relevant);
  const intersection = retrievedK.filter(id => relevantSet.has(id));
  return relevant.length > 0 ? intersection.length / relevant.length : 0;
}

/**
 * Calculate Precision@K
 */
function precisionAtK(retrieved, relevant, k) {
  const retrievedK = retrieved.slice(0, k);
  const relevantSet = new Set(relevant);
  const intersection = retrievedK.filter(id => relevantSet.has(id));
  return retrievedK.length > 0 ? intersection.length / k : 0;
}

/**
 * Calculate MRR (Mean Reciprocal Rank)
 */
function meanReciprocalRank(retrieved, relevant) {
  const relevantSet = new Set(relevant);
  for (let i = 0; i < retrieved.length; i++) {
    if (relevantSet.has(retrieved[i])) {
      return 1 / (i + 1);
    }
  }
  return 0;
}

// ============ Build Dynamic Test Set ============

/**
 * Build test cases from actual memories
 * Uses memory categories to auto-generate relevant_ids
 */
function buildTestCases(memories) {
  const testCases = [];
  
  // Group by category
  const byCategory = {};
  for (const m of memories) {
    const cat = m.category || 'general';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(m.id);
  }
  
  // Generate test cases for each category
  for (const [category, ids] of Object.entries(byCategory)) {
    testCases.push({
      query: `${category}相关的记忆`,
      relevant_ids: ids,
      category,
      description: `Recall memories in category: ${category}`
    });
  }
  
  // Add generic test cases
  if (memories.length > 0) {
    testCases.push({
      query: '重要的事情',
      relevant_ids: memories.filter(m => (m.importance || 0) > 0.7).map(m => m.id),
      category: 'importance',
      description: 'High importance memories'
    });
    
    testCases.push({
      query: '最近的记忆',
      relevant_ids: memories.slice(-10).map(m => m.id),
      category: 'recency',
      description: 'Recent memories'
    });
  }
  
  return testCases;
}

// ============ Main Evaluation ============

/**
 * Run full benchmark evaluation
 */
export function runRecallBenchmark() {
  console.log('🧠 Unified Memory Recall Benchmark\n');
  console.log('='.repeat(50));
  
  // Load memories
  const memories = loadMemoryFiles();
  const memoriesJson = loadMemories();
  
  // Merge both sources
  const allMemories = [...memoriesJson];
  for (const m of memories) {
    if (!allMemories.find(existing => existing.id === m.id)) {
      allMemories.push(m);
    }
  }
  
  console.log(`📦 Dataset: ${allMemories.length} memories loaded\n`);
  
  // Build test cases
  const testCases = buildTestCases(allMemories);
  console.log(`📋 Test cases: ${testCases.length} queries\n`);
  
  // Run evaluation
  const results = [];
  
  for (const tc of testCases) {
    const retrieved = retrieveMemories(tc.query, allMemories, 10);
    
    const result = {
      query: tc.query,
      category: tc.category,
      retrieved_ids: retrieved,
      relevant_ids: tc.relevant_ids,
      'recall@1': recallAtK(retrieved, tc.relevant_ids, 1),
      'recall@5': recallAtK(retrieved, tc.relevant_ids, 5),
      'recall@10': recallAtK(retrieved, tc.relevant_ids, 10),
      'precision@1': precisionAtK(retrieved, tc.relevant_ids, 1),
      'precision@5': precisionAtK(retrieved, tc.relevant_ids, 5),
      mrr: meanReciprocalRank(retrieved, tc.relevant_ids),
    };
    
    results.push(result);
    
    // Log result
    const recallIcon = result['recall@5'] >= 0.8 ? '✅' : result['recall@5'] >= 0.5 ? '🟡' : '❌';
    console.log(`${recallIcon} ${tc.query}`);
    console.log(`   recall@5: ${(result['recall@5'] * 100).toFixed(1)}%  |  precision@5: ${(result['precision@5'] * 100).toFixed(1)}%  |  MRR: ${result.mrr.toFixed(3)}`);
    console.log(`   Retrieved: ${retrieved.length}  |  Relevant: ${tc.relevant_ids.length}`);
    console.log();
  }
  
  // Aggregate metrics
  const avgRecall1 = results.reduce((sum, r) => sum + r['recall@1'], 0) / results.length;
  const avgRecall5 = results.reduce((sum, r) => sum + r['recall@5'], 0) / results.length;
  const avgRecall10 = results.reduce((sum, r) => sum + r['recall@10'], 0) / results.length;
  const avgPrecision1 = results.reduce((sum, r) => sum + r['precision@1'], 0) / results.length;
  const avgPrecision5 = results.reduce((sum, r) => sum + r['precision@5'], 0) / results.length;
  const avgMrr = results.reduce((sum, r) => sum + r.mrr, 0) / results.length;
  
  console.log('='.repeat(50));
  console.log('\n📊 Aggregate Results\n');
  console.log(`   Recall@1:    ${(avgRecall1 * 100).toFixed(1)}%`);
  console.log(`   Recall@5:    ${(avgRecall5 * 100).toFixed(1)}%`);
  console.log(`   Recall@10:   ${(avgRecall10 * 100).toFixed(1)}%`);
  console.log(`   Precision@1: ${(avgPrecision1 * 100).toFixed(1)}%`);
  console.log(`   Precision@5: ${(avgPrecision5 * 100).toFixed(1)}%`);
  console.log(`   MRR:         ${(avgMrr * 100).toFixed(1)}%`);
  
  // Build report
  const report = {
    timestamp: new Date().toISOString(),
    dataset_size: allMemories.length,
    total_queries: results.length,
    metrics: {
      'recall@1': avgRecall1,
      'recall@5': avgRecall5,
      'recall@10': avgRecall10,
      'precision@1': avgPrecision1,
      'precision@5': avgPrecision5,
      mrr: avgMrr,
    },
    results,
  };
  
  // Save report
  if (!existsSync(RESULTS_DIR)) {
    mkdirSync(RESULTS_DIR, { recursive: true });
  }
  const reportFile = join(RESULTS_DIR, `recall_benchmark_${Date.now()}.json`);
  writeFileSync(reportFile, JSON.stringify(report, null, 2), 'utf-8');
  console.log(`\n💾 Report saved: ${reportFile}`);
  
  return report;
}

// CLI
if (typeof process !== "undefined" && import.meta.url === "file://" + process.argv[1]) {
  runRecallBenchmark();
}

export default runRecallBenchmark;
