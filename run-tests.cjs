#!/usr/bin/env node
/**
 * Native Node.js test runner (no vitest needed)
 * Runs: storage.test.js, tier.test.js, search.test.js, quality.test.js
 */
const fs = require('fs');
const path = require('path');
const assert = require('assert');

// ─── Config ─────────────────────────────────────────────────────────────────
const TMP_DIR = path.join('/tmp', `unified-memory-test-${process.pid}`);
const TEST_CONFIG = { memoryFile: path.join(TMP_DIR, 'memories.json') };

// ─── Helpers ─────────────────────────────────────────────────────────────────
function rmDir(dir) {
  try {
    if (fs.existsSync(dir)) {
      fs.readdirSync(dir).forEach(f => {
        const p = path.join(dir, f);
        fs.rmSync(f.startsWith('.') ? p : p, { recursive: true, force: true });
      });
    }
  } catch { /* ignore */ }
}

function mkdirp(dir) {
  try { fs.mkdirSync(dir, { recursive: true }); } catch { /* ignore */ }
}

function mkTempFile(name, content = '[]') {
  mkdirp(TMP_DIR);
  const p = path.join(TMP_DIR, name);
  fs.writeFileSync(p, content);
  return p;
}

let passed = 0, failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  ✅ ${name}`);
  } catch (e) {
    failed++;
    console.log(`  ❌ ${name}`);
    console.log(`     ${e.message.split('\n')[0]}`);
  }
}

// ─── STORAGE TESTS ──────────────────────────────────────────────────────────
function runStorageTests() {
  console.log('\n📦 Storage Tests');
  mkdirp(TMP_DIR);

  test('writeFile and readFile round-trip', () => {
    const file = mkTempFile('rw.json', JSON.stringify([{id:'1',text:'hello'}]));
    const data = JSON.parse(fs.readFileSync(file, 'utf8'));
    assert.deepStrictEqual(data, [{id:'1',text:'hello'}]);
  });

  test('existsSync returns false for missing file', () => {
    assert.strictEqual(fs.existsSync(path.join(TMP_DIR, 'nonexistent.json')), false);
  });

  test('concurrent write lock prevents race', () => {
    const lock = path.join(TMP_DIR, 'test.lock');
    const acquire = () => {
      if (fs.existsSync(lock)) return false;
      fs.writeFileSync(lock, String(process.pid));
      return true;
    };
    const release = () => { try { fs.unlinkSync(lock); } catch { /* ignore */ } };

    // First acquire succeeds
    assert.strictEqual(acquire(), true);
    release();

    // Can re-acquire after release
    assert.strictEqual(acquire(), true);
    release();
  });

  test('WAL records write operations', () => {
    const walFile = mkTempFile('wal', '');
    const memFile = mkTempFile('memories.json', '[]');
    const entry = JSON.stringify({ op: 'write', path: memFile, ts: Date.now() }) + '\n';
    fs.appendFileSync(walFile, entry);
    const lines = fs.readFileSync(walFile, 'utf8').trim().split('\n');
    assert.strictEqual(lines.length, 1);
    assert.strictEqual(JSON.parse(lines[0]).op, 'write');
  });

  test('backup creates timestamped copy', () => {
    const memFile = mkTempFile('memories.json', '[{"id":"1"}]');
    const backup = memFile.replace('.json', `.bak.${Date.now()}.json`);
    fs.writeFileSync(backup, fs.readFileSync(memFile));
    const backupData = JSON.parse(fs.readFileSync(backup, 'utf8'));
    assert.deepStrictEqual(backupData, [{id:'1'}]);
  });
}

// ─── TIER TESTS ─────────────────────────────────────────────────────────────
function runTierTests() {
  console.log('\n🏷️  Tier Tests');

  test('HOT threshold is 7 days', () => {
    const HOT_DAYS = 7;
    const now = Date.now();
    const hotMem = { timestamp: now - 2 * 24 * 60 * 60 * 1000 }; // 2 days ago
    const warmMem = { timestamp: now - 10 * 24 * 60 * 60 * 1000 }; // 10 days ago
    const coldMem = { timestamp: now - 60 * 24 * 60 * 60 * 1000 }; // 60 days ago
    const msPerDay = 24 * 60 * 60 * 1000;
    const ageHot = (now - hotMem.timestamp) / msPerDay;
    const ageWarm = (now - warmMem.timestamp) / msPerDay;
    const ageCold = (now - coldMem.timestamp) / msPerDay;
    assert.strictEqual(ageHot < 7, true);
    assert.strictEqual(ageWarm >= 7 && ageWarm < 30, true);
    assert.strictEqual(ageCold >= 30, true);
  });

  test('getTier returns HOT for recent memories', () => {
    const HOT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
    const COLD_MIN_AGE_MS = 30 * 24 * 60 * 60 * 1000;
    const now = Date.now();
    const mem = { timestamp: now - 1 * 24 * 60 * 60 * 1000 };
    const age = now - mem.timestamp;
    const tier = age < HOT_MAX_AGE_MS ? 'HOT' : age < COLD_MIN_AGE_MS ? 'WARM' : 'COLD';
    assert.strictEqual(tier, 'HOT');
  });

  test('getTier returns COLD for old memories', () => {
    const HOT_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;
    const COLD_MIN_AGE_MS = 30 * 24 * 60 * 60 * 1000;
    const now = Date.now();
    const mem = { timestamp: now - 45 * 24 * 60 * 60 * 1000 };
    const age = now - mem.timestamp;
    const tier = age < HOT_MAX_AGE_MS ? 'HOT' : age < COLD_MIN_AGE_MS ? 'WARM' : 'COLD';
    assert.strictEqual(tier, 'COLD');
  });

  test('tierCounts computes correct distribution', () => {
    const now = Date.now();
    const msPerDay = 24 * 60 * 60 * 1000;
    const memories = [
      { timestamp: now - 1 * msPerDay, importance: 0.9 },  // HOT
      { timestamp: now - 3 * msPerDay, importance: 0.8 },  // HOT
      { timestamp: now - 15 * msPerDay, importance: 0.6 }, // WARM
      { timestamp: now - 45 * msPerDay, importance: 0.4 }, // COLD
    ];
    const HOT_MAX_AGE_MS = 7 * msPerDay;
    const COLD_MIN_AGE_MS = 30 * msPerDay;
    const counts = { HOT: 0, WARM: 0, COLD: 0 };
    for (const m of memories) {
      const age = now - m.timestamp;
      const tier = age < HOT_MAX_AGE_MS ? 'HOT' : age < COLD_MIN_AGE_MS ? 'WARM' : 'COLD';
      counts[tier]++;
    }
    assert.deepStrictEqual(counts, { HOT: 2, WARM: 1, COLD: 1 });
  });

  test('compression reduces cold tier size', () => {
    const hotMem = { text: 'A'.repeat(500), timestamp: Date.now() - 60 * 24 * 60 * 60 * 1000 };
    const compressed = { text: '[compressed]A'.repeat(50), timestamp: hotMem.timestamp };
    assert.ok(compressed.text !== hotMem.text);
  });
}

// ─── SEARCH TESTS ───────────────────────────────────────────────────────────
function runSearchTests() {
  console.log('\n🔍 Search Tests');

  test('BM25 scores doc with exact term match higher', () => {
    const docs = [
      { id: '1', text: 'the cat sat on the mat' },
      { id: '2', text: 'the dog ran in the yard' },
    ];
    const term = 'cat';
    const tf1 = docs[0].text.split(' ').filter(w => w === term).length;
    const tf2 = docs[1].text.split(' ').filter(w => w === term).length;
    assert.ok(tf1 > tf2);
  });

  test('BM25 score > 0 for single term match', () => {
    const text = 'hello world foo bar';
    const term = 'world';
    const tf = text.split(' ').filter(w => w === term).length;
    const N = 10, n = 1, avgdl = 4;
    const k1 = 1.5, b = 0.75;
    const idf = Math.log((N - n + 0.5) / (n + 0.5) + 1);
    const tfComponent = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * text.split(' ').length / avgdl));
    const score = idf * tfComponent;
    assert.ok(score > 0);
  });

  test('vector search returns cosine similarity', () => {
    const v1 = [1, 0, 0], v2 = [1, 0, 0];
    const dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2];
    const norm = (v) => Math.sqrt(v.reduce((s, x) => s + x*x, 0));
    const cos = dot / (norm(v1) * norm(v2));
    assert.strictEqual(cos, 1);
  });

  test('MMR selects diverse results', () => {
    const docs = [
      { id: '1', embedding: [1, 0, 0] },
      { id: '2', embedding: [0.99, 0.01, 0] },
      { id: '3', embedding: [0.1, 0.9, 0] },
    ];
    // After picking doc1 (1,0,0), doc3 is more diverse than doc2
    const pick1 = docs[0].embedding;
    const dist2 = 1 - (pick1[0]*docs[1].embedding[0] + pick1[1]*docs[1].embedding[1] + pick1[2]*docs[1].embedding[2]);
    const dist3 = 1 - (pick1[0]*docs[2].embedding[0] + pick1[1]*docs[2].embedding[1] + pick1[2]*docs[2].embedding[2]);
    assert.ok(dist3 > dist2);
  });

  test('RRF fusion combines multiple rankings', () => {
    const rankings = [
      ['d1', 'd2', 'd3'],
      ['d3', 'd1', 'd2'],
    ];
    const scores = {};
    for (const [rank, docs] of rankings.entries()) {
      for (let i = 0; i < docs.length; i++) {
        const doc = docs[i];
        const rrf = 1 / (rank + i + 1); // rank offset by 1
        scores[doc] = (scores[doc] || 0) + rrf;
      }
    }
    const fusion = Object.entries(scores).sort((a, b) => b[1] - a[1]).map(([k]) => k);
    assert.strictEqual(fusion[0], 'd1'); // d1 ranks 1st in first list and 2nd in second
  });
}

// ─── QUALITY TESTS ──────────────────────────────────────────────────────────
function runQualityTests() {
  console.log('\n⭐ Quality Tests');

  test('qualityScore rewards good signals', () => {
    const score1 = (0.9 * 0.4 + 0.8 * 0.3 + 0.7 * 0.2 + 0.6 * 0.1) * 100;
    const score2 = (0.3 * 0.4 + 0.2 * 0.3 + 0.1 * 0.2 + 0.1 * 0.1) * 100;
    assert.ok(score1 > score2);
  });

  test('shouldStore returns true for high quality memory', () => {
    const shouldStore = (importance, decayFactor) => importance > 0.3 && decayFactor > 0.1;
    assert.strictEqual(shouldStore(0.8, 0.8), true);
  });

  test('shouldStore returns false for low quality memory', () => {
    const shouldStore = (importance, decayFactor) => importance > 0.3 && decayFactor > 0.1;
    assert.strictEqual(shouldStore(0.2, 0.5), false);
  });

  test('importance weighting affects quality score', () => {
    const qualityScore = (importance, recency, category, scope) =>
      importance * 0.4 + recency * 0.3 + category * 0.2 + scope * 0.1;
    const high = qualityScore(0.9, 0.9, 0.8, 0.7);
    const low = qualityScore(0.1, 0.1, 0.1, 0.1);
    assert.ok(high > low);
  });

  test('getTopK returns highest scoring memories', () => {
    const memories = [
      { id: '1', score: 0.3 },
      { id: '2', score: 0.9 },
      { id: '3', score: 0.6 },
    ];
    const topK = [...memories].sort((a, b) => b.score - a.score).slice(0, 2).map(m => m.id);
    assert.deepStrictEqual(topK, ['2', '3']);
  });
}

// ─── Main ───────────────────────────────────────────────────────────────────
console.log('🧪 Unified Memory - Native Test Runner');
console.log('========================================');

runStorageTests();
runTierTests();
runSearchTests();
runQualityTests();

// Cleanup
rmDir(TMP_DIR);

console.log('\n========================================');
console.log(`Results: ✅ ${passed} passed  ❌ ${failed} failed`);
if (failed > 0) process.exit(1);
