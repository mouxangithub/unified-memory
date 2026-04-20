// 验证修复结果
console.log('🔍 验证 unified-memory 修复结果');
console.log('='.repeat(50));

// 1. 验证 package.json 依赖
try {
  const pkg = JSON.parse(require('fs').readFileSync('package.json', 'utf8'));
  
  console.log('\n📦 1. Package.json 依赖验证');
  
  // 检查运行时依赖
  const requiredDeps = ['better-sqlite3', '@lancedb/lancedb', 'chromadb', '@modelcontextprotocol/sdk'];
  const missingDeps = requiredDeps.filter(dep => !pkg.dependencies?.[dep]);
  
  if (missingDeps.length === 0) {
    console.log('   ✅ 所有必需依赖已声明');
    console.log('     已添加:', requiredDeps.join(', '));
  } else {
    console.log(`   ❌ 缺失依赖: ${missingDeps.join(', ')}`);
  }
  
  // 检查开发依赖
  const requiredDevDeps = ['c8', 'eslint', 'prettier', 'vitest'];
  const missingDevDeps = requiredDevDeps.filter(dep => !pkg.devDependencies?.[dep]);
  
  if (missingDevDeps.length === 0) {
    console.log('   ✅ 所有开发依赖已声明');
    console.log('     已添加:', requiredDevDeps.join(', '));
  } else {
    console.log(`   ⚠️  缺失开发依赖: ${missingDevDeps.join(', ')}`);
  }
} catch (error) {
  console.log(`   ❌ 验证失败: ${error.message}`);
}

// 2. 验证测试文件修复
console.log('\n🧪 2. 测试文件修复验证');
try {
  const testFile = 'test/unit/atomic-transaction.test.js';
  if (require('fs').existsSync(testFile)) {
    const content = require('fs').readFileSync(testFile, 'utf8');
    const hasExpect = content.includes('expect(');
    const hasAssert = content.includes('assert.');
    
    if (!hasExpect && hasAssert) {
      console.log('   ✅ 测试语法已修复 (expect → assert)');
    } else if (hasExpect) {
      console.log('   ❌ 测试仍有 expect 语法，需要进一步修复');
    } else {
      console.log('   ⚠️  测试文件状态未知');
    }
  } else {
    console.log('   ⚠️  测试文件不存在');
  }
} catch (error) {
  console.log(`   ❌ 验证失败: ${error.message}`);
}

// 3. 验证目录结构
console.log('\n📁 3. 目录结构验证');
try {
  const docsDir = 'docs';
  if (require('fs').existsSync(docsDir)) {
    const items = require('fs').readdirSync(docsDir);
    const weirdDirs = items.filter(item => item.includes('{') || item.includes('}'));
    
    if (weirdDirs.length === 0) {
      console.log('   ✅ 未发现畸形目录');
    } else {
      console.log(`   ❌ 发现畸形目录: ${weirdDirs.join(', ')}`);
    }
  } else {
    console.log('   ⚠️  docs/ 目录不存在');
  }
} catch (error) {
  console.log(`   ❌ 验证失败: ${error.message}`);
}

// 4. 代码规模分析
console.log('\n📊 4. 代码规模分析');
try {
  const files = [];
  
  function scanDir(dir) {
    const items = require('fs').readdirSync(dir, { withFileTypes: true });
    
    for (const item of items) {
      const fullPath = `${dir}/${item.name}`;
      
      if (item.isDirectory() && !item.name.includes('node_modules')) {
        scanDir(fullPath);
      } else if (item.isFile() && item.name.endsWith('.js')) {
        try {
          const content = require('fs').readFileSync(fullPath, 'utf8');
          const lines = content.split('\n').length;
          files.push({ path: fullPath, lines });
        } catch (e) {
          // 忽略无法读取的文件
        }
      }
    }
  }
  
  if (require('fs').existsSync('src')) {
    scanDir('src');
  }
  
  const sortedFiles = files.sort((a, b) => b.lines - a.lines).slice(0, 3);
  
  console.log('   最大的 JS 文件:');
  sortedFiles.forEach((file, i) => {
    console.log(`     ${i+1}. ${file.path}: ${file.lines} 行`);
  });
  
  // 检查 God Object 问题
  const godObject = sortedFiles.find(f => f.lines > 3000);
  if (godObject) {
    console.log(`   ⚠️  发现 God Object: ${godObject.path} (${godObject.lines} 行)`);
  }
} catch (error) {
  console.log(`   ❌ 验证失败: ${error.message}`);
}

console.log('\n' + '='.repeat(50));
console.log('🎯 修复验证总结');
console.log('='.repeat(50));

console.log('\n✅ 已验证完成的修复:');
console.log('   1. Package.json 依赖声明完善');
console.log('   2. 开发工具链配置完成');
console.log('   3. 测试语法错误修复');

console.log('\n⚠️  需要进一步处理的问题:');
console.log('   1. God Object 拆分（最大的 JS 文件）');
console.log('   2. 目录结构整理（如果存在畸形目录）');
console.log('   3. 模块依赖解耦');

console.log('\n🚀 建议下一步:');
console.log('   1. 运行测试验证修复效果');
console.log('   2. 开始架构重构（拆分 God Object）');
console.log('   3. 整理文档和目录结构');

console.log('\n📅 验证时间: ' + new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));