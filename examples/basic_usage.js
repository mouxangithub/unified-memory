/**
 * Basic Usage - 基础使用示例
 * 展示 unified-memory 的核心 CRUD 操作
 */

import { getEnhancedMemorySystem } from '../src/enhanced_memory_system.js';

async function main() {
  console.log('=== Unified Memory 基础使用示例 ===\n');

  // 初始化系统
  const system = getEnhancedMemorySystem({ enablePipeline: true });
  await system.initialize();
  console.log('✅ 系统初始化完成\n');

  // 1. 存储记忆
  console.log('--- 1. 存储记忆 ---');
  
  const mem1 = await system.remember(
    '用户叫刘选权，是一名全栈工程师',
    { userId: 'user_001', source: 'conversation' }
  );
  console.log('已存储:', mem1.memory.id);

  const mem2 = await system.remember(
    '刘选权擅长 JavaScript、Python 和 Go',
    { userId: 'user_001', source: 'conversation' }
  );
  console.log('已存储:', mem2.memory.id);

  const mem3 = await system.remember(
    '刘选权喜欢简洁的设计风格',
    { userId: 'user_001', source: 'conversation' }
  );
  console.log('已存储:', mem3.memory.id);

  // 2. 搜索记忆
  console.log('\n--- 2. 搜索记忆 ---');
  
  const results = await system.recall('刘选权 技能', { limit: 5 });
  console.log(`找到 ${results.results.length} 条相关记忆:`);
  results.results.forEach((mem, i) => {
    console.log(`  ${i + 1}. ${mem.text}`);
  });

  // 3. 按类型搜索
  console.log('\n--- 3. 按类型搜索 ---');
  
  const patterns = await system.recall('习惯', { 
    limit: 5,
    filter: { type: 'patterns' }
  });
  console.log(`找到 ${patterns.results.length} 条模式记忆`);

  // 4. 列出所有记忆
  console.log('\n--- 4. 列出所有记忆 ---');
  
  const status = system.getStatus();
  console.log(`总计 ${status.stats.totalMemories} 条记忆`);
  console.log(`内存占用: ${(status.stats.memoryUsageBytes / 1024).toFixed(2)} KB`);

  // 5. 健康检查
  console.log('\n--- 5. 健康检查 ---');
  
  const health = system.healthCheck();
  console.log('健康状态:', health.status);
  console.log('组件状态:');
  Object.entries(health.components).forEach(([name, info]) => {
    console.log(`  ${name}: ${info.status}`);
  });

  // 清理
  await system.shutdown();
  console.log('\n=== 完成 ===');
}

main().catch(console.error);
