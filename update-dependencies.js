// 更新 package.json 依赖
import { readFileSync, writeFileSync } from 'fs';

const pkg = JSON.parse(readFileSync('package.json', 'utf8'));

// 添加缺失的依赖
const missingDeps = {
  'better-sqlite3': '^11.0.0',
  '@lancedb/lancedb': '^0.12.0',
  'chromadb': '^1.8.0',
  '@modelcontextprotocol/sdk': '^1.0.0'
};

// 添加到 dependencies
pkg.dependencies = pkg.dependencies || {};
Object.assign(pkg.dependencies, missingDeps);

// 添加 devDependencies
pkg.devDependencies = pkg.devDependencies || {};
Object.assign(pkg.devDependencies, {
  'c8': '^10.0.0',
  'eslint': '^9.0.0',
  'prettier': '^3.0.0',
  'vitest': '^2.0.0'
});

writeFileSync('package.json', JSON.stringify(pkg, null, 2));
console.log('✅ package.json 依赖更新完成');
console.log('新增依赖:', Object.keys(missingDeps).join(', '));
console.log('新增开发依赖: c8, eslint, prettier, vitest');