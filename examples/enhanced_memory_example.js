/**
 * Enhanced Memory System - 使用示例
 * 展示如何使用 OpenViking 风格的增强版记忆系统
 */

import { getEnhancedMemorySystem } from '../src/enhanced_memory_system.js';
import { getMemoryTypeRegistry } from '../src/memory_types/registry.js';
import { getMemoryQueue } from '../src/queue/memory_queue.js';
import { getSmartDeduplicator } from '../src/deduplication/smart_deduplicator.js';

async function main() {
  console.log('=== Enhanced Memory System 示例 ===\n');

  // 1. 初始化系统
  console.log('1. 初始化增强版记忆系统...');
  const system = getEnhancedMemorySystem({
    enablePipeline: true,
    enableQueue: true,
    enableDedup: true,
    enableTypeSystem: true,
    asyncProcessing: true
  });

  await system.initialize();
  console.log('✅ 系统初始化完成\n');

  // 2. 记忆类型检测和处理
  console.log('2. 记忆类型检测和处理...');
  const typeRegistry = getMemoryTypeRegistry();

  const testTexts = [
    '我每天早上7点起床，然后跑步30分钟',
    '刘选权是OpenClaw的创始人，公司位于北京',
    '我擅长JavaScript和Python编程',
    '上次项目失败的原因是需求不明确',
    '明天下午3点有个重要会议',
    '我喜欢简洁的设计风格，不喜欢太复杂的界面'
  ];

  for (const text of testTexts) {
    const detected = await typeRegistry.detectMemoryType(text);
    console.log(`\n文本: "${text}"`);
    console.log(`类型: ${detected.type} (置信度: ${detected.confidence})`);
    
    const processed = await typeRegistry.processMemory(text, detected.type, {
      userId: 'user_001',
      source: 'example'
    });
    
    console.log(`处理结果:`, {
      id: processed.id,
      type: processed.type,
      importance: processed.importance
    });
  }

  // 3. 存储记忆
  console.log('\n\n3. 存储记忆...');
  
  const memory1 = await system.remember(
    '刘选权每天早上7点起床，习惯喝一杯咖啡后开始工作',
    { userId: 'user_001', source: 'conversation' }
  );
  console.log('记忆1已存储:', memory1.memory.id);

  const memory2 = await system.remember(
    '刘选权擅长JavaScript、Python和Go编程',
    { userId: 'user_001', source: 'profile' }
  );
  console.log('记忆2已存储:', memory2.memory.id);

  const memory3 = await system.remember(
    '刘选权喜欢简洁的设计风格，不喜欢复杂的界面',
    { userId: 'user_001', source: 'preference' }
  );
  console.log('记忆3已存储:', memory3.memory.id);

  // 4. 去重测试
  console.log('\n\n4. 测试去重功能...');
  const deduplicator = getSmartDeduplicator();

  const duplicateText = '刘选权每天早上7点起床';
  const dupCheck = await system.remember(
    duplicateText,
    { userId: 'user_001', source: 'conversation' }
  );
  
  console.log('重复记忆检测结果:', dupCheck.status);
  if (dupCheck.duplicateOf) {
    console.log('重复于:', dupCheck.duplicateOf);
  }

  // 5. 回忆记忆
  console.log('\n\n5. 回忆记忆...');
  
  const recall1 = await system.recall('刘选权的习惯', { limit: 5 });
  console.log(`\n查询: "刘选权的习惯"`);
  console.log(`找到 ${recall1.results.length} 条记忆:`);
  recall1.results.forEach((mem, i) => {
    console.log(`  ${i + 1}. ${mem.text.substring(0, 50)}... (来源: ${mem.source})`);
  });

  const recall2 = await system.recall('编程技能', { limit: 5 });
  console.log(`\n查询: "编程技能"`);
  console.log(`找到 ${recall2.results.length} 条记忆:`);
  recall2.results.forEach((mem, i) => {
    console.log(`  ${i + 1}. ${mem.text.substring(0, 50)}... (来源: ${mem.source})`);
  });

  // 6. 队列状态
  console.log('\n\n6. 队列状态...');
  const queue = getMemoryQueue();
  const queueStats = queue.getQueueStats();
  
  console.log('队列统计:');
  for (const [name, stats] of Object.entries(queueStats)) {
    console.log(`  ${name}:`);
    console.log(`    - 待处理: ${stats.pending}`);
    console.log(`    - 处理中: ${stats.inProgress}`);
    console.log(`    - 已处理: ${stats.processed}`);
    console.log(`    - 失败: ${stats.failed}`);
  }

  // 7. 系统状态
  console.log('\n\n7. 系统状态...');
  const status = system.getStatus();
  console.log('系统状态:', JSON.stringify(status, null, 2));

  const health = system.healthCheck();
  console.log('\n健康检查:', JSON.stringify(health, null, 2));

  // 8. 去重统计
  console.log('\n\n8. 去重统计...');
  const dedupStats = deduplicator.getStats();
  console.log('去重统计:', dedupStats);

  // 9. 关闭系统
  console.log('\n\n9. 关闭系统...');
  await system.shutdown();
  console.log('✅ 系统已关闭');

  console.log('\n=== 示例完成 ===');
}

// 运行示例
main().catch(console.error);
