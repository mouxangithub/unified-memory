#!/usr/bin/env node
// Test runner script
import { spawn } from 'child_process';

const args = process.argv.slice(2);
const testFile = args[0] || 'test/unit/atomic-transaction.test.js';

console.log(`Running: ${testFile}`);

const proc = spawn('node', ['--test', testFile], { 
  cwd: '/root/.openclaw/skills/unified-memory'
});

proc.stdout.pipe(process.stdout);
proc.stderr.pipe(process.stderr);

proc.on('close', (code) => {
  process.exit(code);
});
