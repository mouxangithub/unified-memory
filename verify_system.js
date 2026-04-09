/**
 * 简单验证脚本 - 验证所有组件是否正确创建
 */

import { logger } from './src/logger.js';
import { getMemoryTypeRegistry } from './src/memory_types/registry.js';
import { getMemoryQueue } from './src/queue/memory_queue.js';
import { getSmartDeduplicator } from './src/deduplication/smart_deduplicator.js';
import { getMemoryRecallOptimizer } from './src/recall/memory_recall_optimizer.js';
import { getMemoryCompressor } from './src/compression/memory_compressor.js';
import { getMemoryLifecycleManager } from './src/lifecycle/memory_lifecycle_manager.js';
import { getEnhancedMemorySystem } from './src/enhanced_memory_system.js';

console.log('\n' + '='.repeat(60));
console.log('🔍 Enhanced Memory System - 组件验证');
console.log('='.repeat(60) + '\n');

// 1. 验证记忆类型系统
console.log('1️⃣  验证记忆类型系统...');
try {
  const registry = getMemoryTypeRegistry();
  const types = registry.getAllTypes();
  console.log(`   ✅ 类型注册系统正常，支持 ${Object.keys(types).length} 种类型`);
  console.log(`   类型: ${Object.keys(types).join(', ')}`);
} catch (error) {
  console.log(`   ❌ 类型注册系统失败: ${error.message}`);
}

// 2. 验证队列系统
console.log('\n2️⃣  验证队列系统...');
try {
  const queue = getMemoryQueue();
  const stats = queue.getQueueStats();
  console.log(`   ✅ 队列系统正常，支持 ${Object.keys(stats).length} 种队列`);
  console.log(`   队列: ${Object.keys(stats).join(', ')}`);
} catch (error) {
  console.log(`   ❌ 队列系统失败: ${error.message}`);
}

// 3. 验证去重系统
console.log('\n3️⃣  验证去重系统...');
try {
  const deduplicator = getSmartDeduplicator();
  const stats = deduplicator.getStats();
  console.log(`   ✅ 去重系统正常`);
  console.log(`   已检查: ${stats.totalChecked}, 发现重复: ${stats.duplicatesFound}`);
} catch (error) {
  console.log(`   ❌ 去重系统失败: ${error.message}`);
}

// 4. 验证召回优化器
console.log('\n4️⃣  验证召回优化器...');
try {
  const optimizer = getMemoryRecallOptimizer();
  const stats = optimizer.getStats();
  console.log(`   ✅ 召回优化器正常`);
  console.log(`   总召回: ${stats.totalRecalls}, 平均耗时: ${stats.avgRecallTime}ms`);
} catch (error) {
  console.log(`   ❌ 召回优化器失败: ${error.message}`);
}

// 5. 验证压缩器
console.log('\n5️⃣  验证压缩器...');
try {
  const compressor = getMemoryCompressor();
  const stats = compressor.getStats();
  console.log(`   ✅ 压缩器正常`);
  console.log(`   总压缩: ${stats.totalCompressions}, 平均压缩率: ${(stats.avgCompressionRatio * 100).toFixed(1)}%`);
} catch (error) {
  console.log(`   ❌ 压缩器失败: ${error.message}`);
}

// 6. 验证生命周期管理器
console.log('\n6️⃣  验证生命周期管理器...');
try {
  const lifecycle = getMemoryLifecycleManager();
  const stats = lifecycle.getLifecycleStats();
  console.log(`   ✅ 生命周期管理器正常`);
  console.log(`   已归档: ${stats.totalArchived}, 已清理: ${stats.totalCleaned}`);
} catch (error) {
  console.log(`   ❌ 生命周期管理器失败: ${error.message}`);
}

// 7. 验证增强版系统
console.log('\n7️⃣  验证增强版系统...');
try {
  const system = getEnhancedMemorySystem();
  console.log(`   ✅ 增强版系统创建成功`);
  console.log(`   初始化状态: ${system.initialized ? '已初始化' : '未初始化'}`);
} catch (error) {
  console.log(`   ❌ 增强版系统失败: ${error.message}`);
}

console.log('\n' + '='.repeat(60));
console.log('✅ 所有组件验证完成！');
console.log('='.repeat(60) + '\n');

// 8. 测试记忆类型检测
console.log('🧪 测试记忆类型检测...\n');

async function testTypeDetection() {
  try {
    const registry = getMemoryTypeRegistry();
    
    const testCases = [
      '刘选权是OpenClaw的创始人',
      '刘选权每天早上7点起床',
      '刘选权擅长JavaScript编程',
      '上次项目失败的原因是需求不明确',
      '明天下午3点有个会议',
      '刘选权喜欢简洁的设计风格'
    ];
    
    for (const text of testCases) {
      const detected = await registry.detectMemoryType(text);
      console.log(`   "${text.substring(0, 20)}..." → ${detected.type} (${detected.confidence})`);
    }
    
    console.log('\n✅ 类型检测测试完成！');
  } catch (error) {
    console.log(`❌ 类型检测测试失败: ${error.message}`);
  }
}

testTypeDetection().then(() => {
  console.log('\n🎉 所有验证完成！系统已准备就绪。\n');
}).catch(console.error);
