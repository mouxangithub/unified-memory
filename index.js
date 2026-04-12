#!/usr/bin/env node

/**
 * 记忆系统优化项目 - 主入口
 */

import SyncBridge from './sync/sync_bridge.js';
import UnifiedQueryAPI from './api/unified_query_api.js';
import CrossSystemDeduplicator from './dedup/cross_system_dedup.js';
import MemoryHealthMonitor from './monitor/health_check.js';

export {
  SyncBridge,
  UnifiedQueryAPI,
  CrossSystemDeduplicator,
  MemoryHealthMonitor
};

// CLI支持
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🧠 记忆系统优化项目');
  console.log('='.repeat(40));
  console.log('可用模块:');
  console.log('  • SyncBridge - 同步桥梁');
  console.log('  • UnifiedQueryAPI - 统一检索API');
  console.log('  • CrossSystemDeduplicator - 跨系统去重');
  console.log('  • MemoryHealthMonitor - 健康监控');
  console.log('');
  console.log('使用方法:');
  console.log('  npm run sync     - 执行同步');
  console.log('  npm run query    - 执行查询');
  console.log('  npm run dedup    - 执行去重检查');
  console.log('  npm run monitor  - 健康检查');
  console.log('  npm run crontab  - 生成crontab配置');
}
