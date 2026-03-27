#!/usr/bin/env node
/**
 * Simple Test Runner - Uses Node.js built-in test runner
 * 
 * This runner provides basic test functionality similar to vitest.
 * Tests are designed for vitest but can also run with this runner.
 * 
 * Usage:
 *   node run-tests.js              # Run all tests
 *   node run-tests.js storage     # Run only storage tests
 *   node run-tests.js --help      # Show help
 */

import { spawn } from 'child_process';
import { readdirSync, statSync } from 'fs';
import { join, basename } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const TEST_DIR = join(__dirname, 'tests', 'unit');

// Colors for output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(color, msg) {
  console.log(`${colors[color]}%s${colors.reset}`, msg);
}

function getTestFiles(filter) {
  const files = readdirSync(TEST_DIR).filter(f => f.endsWith('.test.js'));
  if (filter) {
    return files.filter(f => f.toLowerCase().includes(filter.toLowerCase()));
  }
  return files;
}

async function runTestFile(file) {
  return new Promise((resolve) => {
    const testPath = join(TEST_DIR, file);
    const child = spawn('node', ['--test', testPath], {
      cwd: __dirname,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    
    let stdout = '';
    let stderr = '';
    
    child.stdout.on('data', (d) => { stdout += d; });
    child.stderr.on('data', (d) => { stderr += d; });
    
    child.on('close', (code) => {
      resolve({ 
        file, 
        passed: code === 0, 
        output: stdout + stderr 
      });
    });
    
    child.on('error', (err) => {
      resolve({ 
        file, 
        passed: false, 
        output: err.message 
      });
    });
    
    // Timeout after 30 seconds
    setTimeout(() => {
      child.kill();
      resolve({ file, passed: false, output: 'Test timed out' });
    }, 30000);
  });
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
Simple Test Runner for unified-memory

Usage:
  node run-tests.js              Run all tests
  node run-tests.js <filter>    Run tests matching filter
  node run-tests.js --vitest    Run with vitest (if installed)
  node run-tests.js --help       Show this help

Examples:
  node run-tests.js storage      Run storage tests
  node run-tests.js tier         Run tier tests
  node run-tests.js              Run all tests
    `.trim());
    return;
  }
  
  if (args.includes('--vitest')) {
    // Try to run with vitest
    const vitestPath = join(__dirname, 'node_modules', '.bin', 'vitest');
    const child = spawn('npx', ['vitest', 'run', ...args.slice(1)], {
      cwd: __dirname,
      stdio: 'inherit',
    });
    child.on('close', (code) => process.exit(code));
    return;
  }

  const filter = args[0] || null;
  const files = getTestFiles(filter);
  
  if (files.length === 0) {
    log('yellow', 'No test files found');
    return;
  }
  
  log('cyan', `\n🧪 Running ${files.length} test file(s)...\n`);
  
  const results = [];
  for (const file of files) {
    log('blue', `  Running ${file}...`);
    const result = await runTestFile(file);
    results.push(result);
    if (result.passed) {
      log('green', `    ✓ ${file} PASSED`);
    } else {
      log('red', `    ✗ ${file} FAILED`);
      if (result.output) {
        console.log(result.output.slice(0, 500));
      }
    }
  }
  
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  
  console.log('\n' + '='.repeat(50));
  log(failed > 0 ? 'red' : 'green', 
    `\n📊 Results: ${passed} passed, ${failed} failed\n`);
  
  process.exit(failed > 0 ? 1 : 0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
