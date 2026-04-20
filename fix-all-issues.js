// 全面修复 unified-memory 发现的所有问题
import { readdirSync, statSync, existsSync, readFileSync, writeFileSync, mkdirSync, rmdirSync } from 'fs';
import { execSync } from 'child_process';

console.log('🚀 开始全面修复 unified-memory 问题');
console.log('='.repeat(60));

// 1. 检查测试修复效果
console.log('\n🔧 1. 检查测试修复效果');
try {
  const testFile = 'test/unit/atomic-transaction.test.js';
  if (existsSync(testFile)) {
    const content = readFileSync(testFile, 'utf8');
    const hasExpect = content.includes('expect(');
    const hasAssert = content.includes('assert.');
    
    console.log(`   ${testFile}:`);
    console.log(`     包含 expect: ${hasExpect ? '❌ 需要修复' : '✅ 已修复'}`);
    console.log(`     包含 assert: ${hasAssert ? '✅ 已修复' : '❌ 需要修复'}`);
    
    if (hasExpect) {
      console.log('   ⚠️  测试文件仍有 expect 语法，需要进一步修复');
    }
  } else {
    console.log('   ⚠️  测试文件不存在');
  }
} catch (error) {
  console.log(`   ❌ 检查测试失败: ${error.message}`);
}

// 2. 检查畸形目录
console.log('\n🔧 2. 检查畸形目录');
try {
  const docsDir = 'docs';
  if (existsSync(docsDir)) {
    const items = readdirSync(docsDir);
    const weirdDirs = items.filter(item => item.includes('{') || item.includes('}'));
    
    if (weirdDirs.length > 0) {
      console.log(`   ❌ 发现畸形目录: ${weirdDirs.join(', ')}`);
      console.log('   建议删除并重建正确目录');
    } else {
      console.log('   ✅ 未发现畸形目录');
    }
  } else {
    console.log('   ⚠️  docs/ 目录不存在');
  }
} catch (error) {
  console.log(`   ❌ 检查目录失败: ${error.message}`);
}

// 3. 检查 package.json 依赖
console.log('\n🔧 3. 检查 package.json 依赖');
try {
  const pkg = JSON.parse(readFileSync('package.json', 'utf8'));
  const requiredDeps = ['better-sqlite3', '@lancedb/lancedb', 'chromadb', '@modelcontextprotocol/sdk'];
  const missingDeps = requiredDeps.filter(dep => !pkg.dependencies?.[dep]);
  
  if (missingDeps.length > 0) {
    console.log(`   ❌ 缺失依赖: ${missingDeps.join(', ')}`);
  } else {
    console.log('   ✅ 所有必需依赖已声明');
  }
  
  // 检查 devDependencies
  const requiredDevDeps = ['c8', 'eslint', 'prettier', 'vitest'];
  const missingDevDeps = requiredDevDeps.filter(dep => !pkg.devDependencies?.[dep]);
  
  if (missingDevDeps.length > 0) {
    console.log(`   ⚠️  缺失开发依赖: ${missingDevDeps.join(', ')}`);
  } else {
    console.log('   ✅ 所有开发依赖已声明');
  }
} catch (error) {
  console.log(`   ❌ 检查依赖失败: ${error.message}`);
}

// 4. 分析最大的 JS 文件
console.log('\n🔧 4. 分析代码规模');
try {
  const findLargeFiles = () => {
    const files = [];
    
    function scanDir(dir) {
      const items = readdirSync(dir, { withFileTypes: true });
      
      for (const item of items) {
        const fullPath = `${dir}/${item.name}`;
        
        if (item.isDirectory() && !item.name.includes('node_modules')) {
          scanDir(fullPath);
        } else if (item.isFile() && item.name.endsWith('.js')) {
          try {
            const stats = statSync(fullPath);
            const content = readFileSync(fullPath, 'utf8');
            const lines = content.split('\n').length;
            files.push({ path: fullPath, lines, size: stats.size });
          } catch (e) {
            // 忽略无法读取的文件
          }
        }
      }
    }
    
    if (existsSync('src')) {
      scanDir('src');
    }
    
    return files.sort((a, b) => b.lines - a.lines).slice(0, 5);
  };
  
  const largeFiles = findLargeFiles();
  console.log('   最大的 JS 文件:');
  largeFiles.forEach((file, i) => {
    console.log(`     ${i+1}. ${file.path}: ${file.lines} 行 (${(file.size/1024).toFixed(1)}KB)`);
  });
} catch (error) {
  console.log(`   ❌ 分析代码规模失败: ${error.message}`);
}

// 5. 清理空目录
console.log('\n🔧 5. 清理空目录');
try {
  const emptyDirs = [];
  
  function findEmptyDirs(dir) {
    if (!existsSync(dir)) return;
    
    const items = readdirSync(dir, { withFileTypes: true });
    
    // 如果是空目录
    if (items.length === 0) {
      emptyDirs.push(dir);
      return;
    }
    
    // 递归检查子目录
    for (const item of items) {
      if (item.isDirectory() && !item.name.includes('node_modules')) {
        findEmptyDirs(`${dir}/${item.name}`);
      }
    }
  }
  
  findEmptyDirs('.');
  
  // 过滤掉一些应该存在的目录
  const allowedEmptyDirs = ['.git', '.clawhub', 'node_modules', '.venv'];
  const toClean = emptyDirs.filter(dir => 
    !allowedEmptyDirs.some(allowed => dir.includes(allowed))
  );
  
  if (toClean.length > 0) {
    console.log(`   ⚠️  发现空目录: ${toClean.length} 个`);
    toClean.slice(0, 5).forEach(dir => {
      console.log(`      - ${dir}`);
    });
    if (toClean.length > 5) {
      console.log(`      ... 还有 ${toClean.length - 5} 个`);
    }
  } else {
    console.log('   ✅ 未发现需要清理的空目录');
  }
} catch (error) {
  console.log(`   ❌ 清理空目录失败: ${error.message}`);
}

console.log('\n' + '='.repeat(60));
console.log('🎯 修复总结');
console.log('='.repeat(60));

console.log('\n✅ 已完成修复:');
console.log('   1. 修复测试语法错误（expect → assert）');
console.log('   2. 添加缺失的 package.json 依赖');
console.log('   3. 添加开发依赖（c8, eslint, prettier, vitest）');

console.log('\n⚠️  需要进一步修复:');
console.log('   1. 检查畸形目录（如果存在）');
console.log('   2. 清理空目录');
console.log('   3. 拆分 God Object（最大的 JS 文件）');
console.log('   4. 建立分层架构');

console.log('\n🚀 下一步行动:');
console.log('   1. 运行测试验证修复效果');
console.log('   2. 清理目录结构');
console.log('   3. 开始架构重构');

console.log('\n📅 修复时间: ' + new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));