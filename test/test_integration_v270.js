#!/usr/bin/env node
import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const skillDir = join(__dirname);

async function testAll() {
  console.log('=== Unified Memory v2.7.0 集成测试 ===\n');
  
  let passed = 0;
  let total = 0;
  
  // 1. 检查文件是否存在
  console.log('1. 文件完整性检查');
  const requiredFiles = [
    'src/tier_tools.js',
    'src/tools/version_tools.js', 
    'src/tools/identity_tools.js',
    'src/webui/dashboard.js',
    'package.json',
    'SKILL.md'
  ];
  
  for (const file of requiredFiles) {
    total++;
    const path = join(skillDir, file);
    if (existsSync(path)) {
      console.log(`  ✅ ${file}`);
      passed++;
    } else {
      console.log(`  ❌ ${file} (缺失)`);
    }
  }
  
  // 2. 检查版本号
  console.log('\n2. 版本号一致性检查');
  total++;
  const pkg = JSON.parse(readFileSync(join(skillDir, 'package.json'), 'utf-8'));
  const skillMd = readFileSync(join(skillDir, 'SKILL.md'), 'utf-8');
  
  if (pkg.version === '2.7.0' && skillMd.includes('# 🧠 Unified Memory v2.7')) {
    console.log(`  ✅ 版本号一致: v${pkg.version}`);
    passed++;
  } else {
    console.log(`  ❌ 版本号不一致: package.json=${pkg.version}, SKILL.md=${skillMd.match(/v2\.\d+/)?.[0]}`);
  }
  
  // 3. 检查工具注册
  console.log('\n3. 工具注册检查');
  total++;
  const indexJs = readFileSync(join(skillDir, 'src/index.js'), 'utf-8');
  const newTools = [
    'memory_tier_status',
    'memory_tier_migrate', 
    'memory_tier_compress',
    'memory_version_list',
    'memory_version_diff',
    'memory_version_restore',
    'memory_identity_extract',
    'memory_identity_update',
    'memory_identity_get'
  ];
  
  const missingTools = newTools.filter(tool => !indexJs.includes(tool));
  if (missingTools.length === 0) {
    console.log(`  ✅ 所有 ${newTools.length} 个新工具已注册`);
    passed++;
  } else {
    console.log(`  ❌ 缺失工具: ${missingTools.join(', ')}`);
  }
  
  // 4. 检查 dashboard 脚本
  console.log('\n4. Dashboard 脚本检查');
  total++;
  if (pkg.scripts && pkg.scripts.dashboard) {
    console.log(`  ✅ dashboard 脚本: ${pkg.scripts.dashboard}`);
    passed++;
  } else {
    console.log('  ❌ dashboard 脚本缺失');
  }
  
  // 总结
  console.log('\n=== 测试结果 ===');
  console.log(`通过: ${passed}/${total} (${Math.round(passed/total*100)}%)`);
  
  if (passed === total) {
    console.log('✅ 所有测试通过！v2.7.0 集成完成');
    return true;
  } else {
    console.log('❌ 集成测试失败');
    return false;
  }
}

testAll().catch(e => {
  console.error('测试失败:', e.message);
  process.exit(1);
});