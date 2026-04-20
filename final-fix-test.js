// 最终修复测试文件
const fs = require('fs');
const path = require('path');

const testFile = path.join(__dirname, 'test/unit/atomic-transaction.test.js');

console.log('🔧 最终修复测试文件');
console.log(`文件: ${testFile}`);

if (!fs.existsSync(testFile)) {
  console.error('❌ 测试文件不存在');
  process.exit(1);
}

// 读取文件内容
let content = fs.readFileSync(testFile, 'utf8');

// 修复所有剩余的 expect 调用
const fixes = [
  // 第106行: expect(fileExists).toBe(false);
  [/\s*expect\(fileExists\)\.toBe\(false\);\s*/, '      assert.strictEqual(fileExists, false);'],
  
  // 第123行: expect(error.message).toBe('模拟提交失败');
  [/\s*expect\(error\.message\)\.toBe\('模拟提交失败'\);\s*/, '      assert.strictEqual(error.message, \'模拟提交失败\');'],
  
  // 第128行: expect(status).toBeNull(); // 事务应该已被清理
  [/\s*expect\(status\)\.toBeNull\(\);\s*\/\/ 事务应该已被清理/, '      assert.strictEqual(status, null); // 事务应该已被清理'],
  
  // 第132行: expect(fileExists).toBe(false);
  [/\s*expect\(fileExists\)\.toBe\(false\);\s*/, '      assert.strictEqual(fileExists, false);'],
  
  // 第138行: await expect(txManager.prepareJsonWrite('nonexistent_tx', testMemory))
  [/\s*await expect\(txManager\.prepareJsonWrite\('nonexistent_tx', testMemory\)\)/, '      await assert.rejects(async () => { await txManager.prepareJsonWrite(\'nonexistent_tx\', testMemory); })'],
  
  // 第141行: await expect(txManager.commitTransaction('nonexistent_tx'))
  [/\s*await expect\(txManager\.commitTransaction\('nonexistent_tx'\)\)/, '      await assert.rejects(async () => { await txManager.commitTransaction(\'nonexistent_tx\'); })'],
  
  // 第148行: await expect(txManager.commitTransaction(txId))
  [/\s*await expect\(txManager\.commitTransaction\(txId\)\)/, '      await assert.rejects(async () => { await txManager.commitTransaction(txId); })'],
  
  // 第170行: expect(recoveryResult.recovered).toBeGreaterThan(0);
  [/\s*expect\(recoveryResult\.recovered\)\.toBeGreaterThan\(0\);\s*/, '      assert.ok(recoveryResult.recovered > 0);'],
  
  // 第171行: expect(recoveryResult.errors).toBe(0);
  [/\s*expect\(recoveryResult\.errors\)\.toBe\(0\);\s*/, '      assert.strictEqual(recoveryResult.errors, 0);'],
  
  // 第177行: expect(status1).toBeNull();
  [/\s*expect\(status1\)\.toBeNull\(\);\s*/, '      assert.strictEqual(status1, null);'],
  
  // 第178行: expect(status2).toBeNull();
  [/\s*expect\(status2\)\.toBeNull\(\);\s*/, '      assert.strictEqual(status2, null);'],
  
  // 第188行: expect(recoveryResult.recovered).toBe(0);
  [/\s*expect\(recoveryResult\.recovered\)\.toBe\(0\);\s*/, '      assert.strictEqual(recoveryResult.recovered, 0);'],
  
  // 第189行: expect(recoveryResult.errors).toBe(0); // 应该优雅处理错误
  [/\s*expect\(recoveryResult\.errors\)\.toBe\(0\);\s*\/\/ 应该优雅处理错误/, '      assert.strictEqual(recoveryResult.errors, 0); // 应该优雅处理错误'],
  
  // 第210行: expect(txIds.length).toBe(10);
  [/\s*expect\(txIds\.length\)\.toBe\(10\);\s*/, '      assert.strictEqual(txIds.length, 10);'],
  
  // 第216行: expect(status.state).toBe('preparing');
  [/\s*expect\(status\.state\)\.toBe\('preparing'\);\s*/, '      assert.strictEqual(status.state, \'preparing\');'],
];

// 应用所有修复
let fixedCount = 0;
for (const [pattern, replacement] of fixes) {
  if (content.match(pattern)) {
    content = content.replace(pattern, replacement);
    fixedCount++;
  }
}

// 写入修复后的内容
fs.writeFileSync(testFile, content);

// 验证修复结果
const expectCount = (content.match(/expect\(/g) || []).length;
const assertCount = (content.match(/assert\./g) || []).length;

console.log(`修复结果: ${expectCount} 个 expect, ${assertCount} 个 assert`);
console.log(`修复了 ${fixedCount} 处`);

if (expectCount === 0) {
  console.log('✅ 所有 expect 调用已完全修复！');
} else {
  console.log(`⚠️  仍有 ${expectCount} 个 expect 调用`);
  
  // 显示剩余的 expect 调用
  const lines = content.split('\n');
  lines.forEach((line, index) => {
    if (line.includes('expect(')) {
      console.log(`   第 ${index + 1} 行: ${line.trim()}`);
    }
  });
}

console.log('\n🎯 测试文件修复完成！');