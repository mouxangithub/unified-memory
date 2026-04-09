/**
 * 分层压缩使用示例 - 借鉴 OpenViking 的三层信息模型
 */

import { getLayeredCompressor } from '../src/compression/layered_compressor.js';

// 示例记忆数据
const sampleMemories = [
  {
    id: 'mem_001',
    text: '张明是某科技公司的创始人，公司位于北京。他拥有10年的软件开发经验，擅长JavaScript、Python和Go编程。公司主要产品是AI助手平台，已经服务了超过10000名用户。',
    type: 'facts',
    importance: 0.9,
    timestamp: Date.now()
  },
  {
    id: 'mem_002',
    text: '张明每天早上7点起床，习惯喝一杯咖啡后开始工作。他喜欢在早上处理最重要的任务，下午通常用于会议和沟通。晚上会花时间学习新技术或阅读技术博客。',
    type: 'patterns',
    importance: 0.7,
    timestamp: Date.now() - 86400000
  },
  {
    id: 'mem_003',
    text: '上次Unified Memory项目成功上线，主要经验教训包括：1) 提前做好技术选型和架构设计；2) 分阶段实施，先核心功能后扩展功能；3) 重视测试和文档；4) 及时与用户沟通反馈。这些经验对后续项目很有参考价值。',
    type: 'cases',
    importance: 0.8,
    timestamp: Date.now() - 172800000
  }
];

async function demonstrateLayeredCompression() {
  console.log('\n' + '='.repeat(80));
  console.log('🎯 分层压缩示例 - 借鉴 OpenViking 的三层信息模型');
  console.log('='.repeat(80) + '\n');
  
  // 创建分层压缩器
  const compressor = getLayeredCompressor({
    l0TokenLimit: 100,   // L0: ~100 tokens
    l1TokenLimit: 2000,  // L1: ~2k tokens
    l2TokenLimit: null   // L2: 无限制
  });
  
  // ========== 示例1：为单个记忆生成所有层 ==========
  console.log('📦 示例1：为单个记忆生成所有层\n');
  
  const memory = sampleMemories[0];
  const layers = compressor.generateAllLayers(memory);
  
  console.log(`原始记忆: "${memory.text.substring(0, 50)}..."`);
  console.log(`原始 tokens: ${compressor.estimateTokens(memory.text)}\n`);
  
  console.log('L0 抽象层 (~100 tokens):');
  console.log(`  文本: "${layers.L0.text}"`);
  console.log(`  Tokens: ${layers.L0.tokens}`);
  console.log(`  类型: ${layers.L0.type}\n`);
  
  console.log('L1 概览层 (~2k tokens):');
  console.log(`  文本: "${layers.L1.text.substring(0, 100)}..."`);
  console.log(`  Tokens: ${layers.L1.tokens}`);
  console.log(`  类型: ${layers.L1.type}\n`);
  
  console.log('L2 详情层 (无限制):');
  console.log(`  文本: "${layers.L2.text.substring(0, 100)}..."`);
  console.log(`  Tokens: ${layers.L2.tokens}`);
  console.log(`  类型: ${layers.L2.type}\n`);
  
  // ========== 示例2：批量生成分层内容 ==========
  console.log('📦 示例2：批量生成分层内容\n');
  
  const allLayers = compressor.generateLayersBatch(sampleMemories);
  
  console.log(`处理了 ${allLayers.length} 条记忆:\n`);
  
  allLayers.forEach((item, i) => {
    console.log(`记忆 ${i + 1}:`);
    console.log(`  L0: ${item.L0.tokens} tokens`);
    console.log(`  L1: ${item.L1.tokens} tokens`);
    console.log(`  L2: ${item.L2.tokens} tokens`);
    console.log(`  节省: ${item.L2.tokens - item.L0.tokens} tokens (${((1 - item.L0.tokens / item.L2.tokens) * 100).toFixed(1)}%)\n`);
  });
  
  // ========== 示例3：智能分层加载策略 ==========
  console.log('📦 示例3：智能分层加载策略\n');
  
  // 策略1：只使用 L0
  console.log('策略1：只使用 L0 层（快速过滤）');
  const l0Result = compressor.selectLayer(sampleMemories, '查询', {
    maxTokens: 4000,
    strategy: 'L0'
  });
  console.log(`  使用 ${l0Result.memories.length} 条记忆`);
  console.log(`  总 tokens: ${l0Result.totalTokens}`);
  console.log(`  平均 tokens: ${l0Result.stats.avgTokens}\n`);
  
  // 策略2：只使用 L1
  console.log('策略2：只使用 L1 层（内容导航）');
  const l1Result = compressor.selectLayer(sampleMemories, '查询', {
    maxTokens: 4000,
    strategy: 'L1'
  });
  console.log(`  使用 ${l1Result.memories.length} 条记忆`);
  console.log(`  总 tokens: ${l1Result.totalTokens}`);
  console.log(`  平均 tokens: ${l1Result.stats.avgTokens}\n`);
  
  // 策略3：自适应策略（推荐）
  console.log('策略3：自适应策略（推荐）');
  const adaptiveResult = compressor.selectLayer(sampleMemories, '查询', {
    maxTokens: 4000,
    strategy: 'adaptive'
  });
  console.log(`  L0 过滤: ${adaptiveResult.stats.l0Filtered} 条`);
  console.log(`  L1 使用: ${adaptiveResult.stats.l1Used} 条`);
  console.log(`  总 tokens: ${adaptiveResult.totalTokens}`);
  console.log(`  平均 tokens: ${adaptiveResult.stats.avgTokens}\n`);
  
  // ========== 示例4：按需加载 L2 详情 ==========
  console.log('📦 示例4：按需加载 L2 详情\n');
  
  const memoryId = 'mem_001';
  const detail = compressor.loadL2Detail(memoryId, sampleMemories);
  
  if (detail) {
    console.log(`加载记忆 ${memoryId} 的 L2 详情:`);
    console.log(`  完整文本: "${detail.text.substring(0, 100)}..."`);
    console.log(`  Tokens: ${detail.tokens}\n`);
  }
  
  // ========== 示例5：统计信息 ==========
  console.log('📦 示例5：统计信息\n');
  
  const stats = compressor.getStats();
  
  console.log('分层压缩统计:');
  console.log(`  L0 生成次数: ${stats.totalL0Generated}`);
  console.log(`  L1 生成次数: ${stats.totalL1Generated}`);
  console.log(`  L2 生成次数: ${stats.totalL2Generated}`);
  console.log(`  平均 L0 tokens: ${stats.avgL0Tokens}`);
  console.log(`  平均 L1 tokens: ${stats.avgL1Tokens}`);
  console.log(`  总节省 tokens: ${stats.totalTokensSaved}`);
  console.log(`  压缩率: ${(stats.compressionRatio * 100).toFixed(1)}%\n`);
  
  // ========== 示例6：与 OpenViking 对比 ==========
  console.log('📊 与 OpenViking 对比\n');
  
  console.log('OpenViking 实验数据:');
  console.log('  输入 token 减少: 83%');
  console.log('  任务完成率提升: 46%\n');
  
  console.log('我们的实现:');
  console.log('  ✅ L0/L1/L2 三层信息模型');
  console.log('  ✅ 自适应加载策略');
  console.log('  ✅ Token 预算控制');
  console.log('  ✅ 按需加载详情');
  console.log('  ✅ 额外优势：去重、生命周期管理、类型系统\n');
  
  console.log('='.repeat(80));
  console.log('✅ 示例完成！');
  console.log('='.repeat(80) + '\n');
}

// 运行示例
demonstrateLayeredCompression().catch(console.error);
