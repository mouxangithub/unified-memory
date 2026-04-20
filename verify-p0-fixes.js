#!/usr/bin/env node
/**
 * P0 Fix Verification Script
 * Verifies all 4 P0 fixes have been applied correctly
 */

import { readFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

console.log('='.repeat(60));
console.log('🔍 P0 Fix Verification Report');
console.log('='.repeat(60));
console.log('');

// Track results
const results = {
  passed: [],
  failed: [],
  warnings: []
};

function pass(msg) {
  console.log(`✅ PASS: ${msg}`);
  results.passed.push(msg);
}

function fail(msg) {
  console.log(`❌ FAIL: ${msg}`);
  results.failed.push(msg);
}

function warn(msg) {
  console.log(`⚠️  WARN: ${msg}`);
  results.warnings.push(msg);
}

// Change to project directory
process.chdir('/root/.openclaw/skills/unified-memory');

// ===== FIX 1: Test Files Using Assert =====
console.log('📋 FIX 1: Testing test files for proper assert usage...');
console.log('-'.repeat(40));

const testFiles = [
  'test/unit/atomic-transaction.test.js',
  'test/integration/atomic-write.test.js'
];

for (const file of testFiles) {
  if (!existsSync(file)) {
    fail(`Test file not found: ${file}`);
    continue;
  }
  
  const content = readFileSync(file, 'utf8');
  
  // Check for improper expect() usage
  const expectMatches = content.match(/expect\s*\(/g);
  if (expectMatches) {
    fail(`${file}: Found ${expectMatches.length} expect() calls (should use assert)`);
  } else {
    pass(`${file}: No expect() calls found`);
  }
  
  // Check for proper assert usage
  const assertMatches = content.match(/assert\.(ok|strictEqual|rejects|deepStrictEqual)\s*\(/g);
  if (assertMatches) {
    pass(`${file}: Found ${assertMatches.length} proper assert calls`);
  }
}

console.log('');

// ===== FIX 2: Dependencies in package.json =====
console.log('📋 FIX 2: Checking dependencies in package.json...');
console.log('-'.repeat(40));

const requiredDeps = [
  'better-sqlite3',
  '@lancedb/lancedb',
  'chromadb',
  '@modelcontextprotocol/sdk'
];

const packageJson = JSON.parse(readFileSync('package.json', 'utf8'));
const deps = { ...packageJson.dependencies, ...packageJson.peerDependencies };

for (const dep of requiredDeps) {
  if (deps[dep]) {
    pass(`${dep}@${deps[dep]}`);
  } else {
    fail(`${dep} not found in package.json`);
  }
}

console.log('');

// ===== FIX 3: Documentation Structure =====
console.log('📋 FIX 3: Checking documentation structure...');
console.log('-'.repeat(40));

const requiredDocs = [
  'docs/README.md',
  'docs/en/api/README.md',
  'docs/zh/api/README.md'
];

for (const doc of requiredDocs) {
  if (existsSync(doc)) {
    const stats = statSync(doc);
    pass(`${doc} (${stats.size} bytes)`);
  } else {
    fail(`${doc} not found`);
  }
}

// Check for getting started guide
if (existsSync('docs/en/getting-started/quickstart.md')) {
  pass('docs/en/getting-started/quickstart.md exists');
} else {
  warn('docs/en/getting-started/quickstart.md not found');
}

if (existsSync('docs/zh/getting-started/quickstart.md')) {
  pass('docs/zh/getting-started/quickstart.md exists');
} else {
  warn('docs/zh/getting-started/quickstart.md not found');
}

console.log('');

// ===== FIX 4: CI/CD Workflows =====
console.log('📋 FIX 4: Checking CI/CD workflows...');
console.log('-'.repeat(40));

const requiredWorkflows = [
  '.github/workflows/test.yml',
  '.github/workflows/release.yml'
];

for (const workflow of requiredWorkflows) {
  if (existsSync(workflow)) {
    const stats = statSync(workflow);
    pass(`${workflow} (${stats.size} bytes)`);
    
    // Validate YAML syntax
    const content = readFileSync(workflow, 'utf8');
    if (content.includes('name:') && content.includes('on:')) {
      pass(`${workflow} has valid structure`);
    } else {
      fail(`${workflow} may have invalid structure`);
    }
  } else {
    fail(`${workflow} not found`);
  }
}

console.log('');
console.log('='.repeat(60));
console.log('📊 Summary');
console.log('='.repeat(60));
console.log(`✅ Passed: ${results.passed.length}`);
console.log(`❌ Failed: ${results.failed.length}`);
console.log(`⚠️  Warnings: ${results.warnings.length}`);
console.log('');

if (results.failed.length > 0) {
  console.log('Failed checks:');
  results.failed.forEach(f => console.log(`  - ${f}`));
}

if (results.warnings.length > 0) {
  console.log('\nWarnings:');
  results.warnings.forEach(w => console.log(`  - ${w}`));
}

console.log('');
process.exit(results.failed.length > 0 ? 1 : 0);
