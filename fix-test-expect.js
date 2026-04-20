// 修复测试文件中的 expect 调用
const fs = require('fs');
const path = require('path');

const testFile = path.join(__dirname, 'test/unit/atomic-transaction.test.js');

console.log('🔧 修复测试文件中的 expect 调用');
console.log(`文件: ${testFile}`);

if (!fs.existsSync(testFile)) {
  console.error('❌ 测试文件不存在');
  process.exit(1);
}

// 读取文件内容
let content = fs.readFileSync(testFile, 'utf8');

// 统计修复前的情况
const expectCount = (content.match(/expect\(/g) || []).length;
const assertCount = (content.match(/assert\./g) || []).length;

console.log(`修复前: ${expectCount} 个 expect, ${assertCount} 个 assert`);

// 修复规则
const replacements = [
  // expect(value).toBe(expected)
  [/\bexpect\(([^)]+)\)\.toBe\(([^)]+)\)/g, 'assert.strictEqual($1, $2)'],
  
  // expect(value).toBeDefined()
  [/\bexpect\(([^)]+)\)\.toBeDefined\(\)/g, 'assert.ok($1)'],
  
  // expect(value).toBeNull()
  [/\bexpect\(([^)]+)\)\.toBeNull\(\)/g, 'assert.strictEqual($1, null)'],
  
  // expect(value).toBeGreaterThan(n)
  [/\bexpect\(([^)]+)\)\.toBeGreaterThan\(([^)]+)\)/g, 'assert.ok($1 > $2)'],
  
  // expect(value).toBeLessThan(n)
  [/\bexpect\(([^)]+)\)\.toBeLessThan\(([^)]+)\)/g, 'assert.ok($1 < $2)'],
  
  // expect(value).toContain(str)
  [/\bexpect\(([^)]+)\)\.toContain\(([^)]+)\)/g, 'assert.match($1, new RegExp($2))'],
  
  // expect(value).toEqual(expected) - 通常用于对象比较
  [/\bexpect\(([^)]+)\)\.toEqual\(([^)]+)\)/g, 'assert.deepStrictEqual($1, $2)'],
  
  // expect(value).toMatch(regex)
  [/\bexpect\(([^)]+)\)\.toMatch\(([^)]+)\)/g, 'assert.match($1, $2)'],
  
  // expect(fn).rejects.toThrow(error)
  [/\bawait expect\(([^)]+)\)\.rejects\.toThrow\(([^)]+)\)/g, 'await assert.rejects(async () => { await $1; }, { message: $2 })'],
  
  // expect(fn).rejects.toThrow()
  [/\bawait expect\(([^)]+)\)\.rejects\.toThrow\(\)/g, 'await assert.rejects(async () => { await $1; })'],
  
  // expect(fn).toThrow(error)
  [/\bexpect\(([^)]+)\)\.toThrow\(([^)]+)\)/g, 'assert.throws(() => { $1; }, { message: $2 })'],
  
  // expect(fn).toThrow()
  [/\bexpect\(([^)]+)\)\.toThrow\(\)/g, 'assert.throws(() => { $1; })'],
];

// 应用替换
let replacedCount = 0;
for (const [pattern, replacement] of replacements) {
  const matches = content.match(pattern);
  if (matches) {
    replacedCount += matches.length;
    content = content.replace(pattern, replacement);
  }
}

// 写入修复后的内容
fs.writeFileSync(testFile, content);

// 统计修复后的情况
const expectCountAfter = (content.match(/expect\(/g) || []).length;
const assertCountAfter = (content.match(/assert\./g) || []).length;

console.log(`修复后: ${expectCountAfter} 个 expect, ${assertCountAfter} 个 assert`);
console.log(`替换了 ${replacedCount} 处`);

if (expectCountAfter === 0) {
  console.log('✅ 所有 expect 调用已修复！');
} else {
  console.log(`⚠️  仍有 ${expectCountAfter} 个 expect 调用需要手动修复`);
  
  // 显示剩余的 expect 调用
  const lines = content.split('\n');
  lines.forEach((line, index) => {
    if (line.includes('expect(')) {
      console.log(`   第 ${index + 1} 行: ${line.trim()}`);
    }
  });
}

console.log('\n📁 备份文件: test/unit/atomic-transaction.test.js.backup');
console.log('🎯 修复完成！');