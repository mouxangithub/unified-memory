/**
 * Complete Workflow - 完整工作流示例
 * 模拟一个完整的对话 → 记忆 → 回忆 → 应用流程
 */

import { getEnhancedMemorySystem } from '../src/enhanced_memory_system.js';

// 模拟对话历史
const conversationHistory = [
  { role: 'user', content: '我叫刘选权，是一名全栈工程师，目前在创业公司工作' },
  { role: 'assistant', content: '很高兴认识您！作为全栈工程师，您擅长哪些技术栈？' },
  { role: 'user', content: '我主要用 JavaScript 和 Python，也用 Go 做后端服务' },
  { role: 'assistant', content: '技术选型很合理！您平时用什么框架？' },
  { role: 'user', content: '前端用 React 和 Next.js，后端用 FastAPI 和 Gin' },
  { role: 'user', content: '我的公司最近在做一个 AI 助手平台，用户增长很快' },
  { role: 'assistant', content: '听起来很有前景！您目前日活有多少？' },
  { role: 'user', content: '大约 5000 用户，主要痛点是用户留存和个性化体验' },
];

// 模拟后续查询
const futureQueries = [
  '刘选权的技术背景是什么？',
  '他公司的产品有什么痛点？',
  '他用什么技术栈做开发？',
];

async function runCompleteWorkflow() {
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║  Unified Memory - 完整工作流演示                         ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  // ========== 第一阶段：初始化系统 ==========
  console.log('【阶段 1】初始化记忆系统');
  console.log('-'.repeat(60));
  
  const system = getEnhancedMemorySystem({
    enablePipeline: true,
    enableQueue: true,
    enableDedup: true,
    enableTypeSystem: true,
    enableCompression: true,
    enableLifecycle: true
  });
  
  await system.initialize();
  console.log('✅ 系统初始化完成\n');

  // ========== 第二阶段：处理对话历史 ==========
  console.log('【阶段 2】处理对话历史 → 提取记忆');
  console.log('-'.repeat(60));
  
  const memoriesStored = [];
  
  for (const msg of conversationHistory) {
    if (msg.role === 'user') {
      // 存储用户话语作为记忆
      const result = await system.remember(msg.content, {
        userId: 'user_001',
        source: 'conversation',
        metadata: { role: msg.role }
      });
      
      if (result.status === 'stored') {
        memoriesStored.push(result.memory.id);
        console.log(`📝 存储: "${msg.content.substring(0, 40)}..."`);
      } else if (result.status === 'duplicate') {
        console.log(`🔄 跳过重复: "${msg.content.substring(0, 40)}..."`);
      }
    }
  }
  
  console.log(`\n共存储 ${memoriesStored.length} 条新记忆\n`);

  // ========== 第三阶段：查看系统状态 ==========
  console.log('【阶段 3】查看记忆系统状态');
  console.log('-'.repeat(60));
  
  const status = system.getStatus();
  console.log(`记忆总数: ${status.stats.totalMemories}`);
  console.log(`去重节省: ${status.stats.duplicatesAvoided} 次`);
  console.log(`队列待处理: ${status.stats.queuePending}`);
  console.log(`内存占用: ${(status.stats.memoryUsageBytes / 1024).toFixed(2)} KB\n`);

  // ========== 第四阶段：按类型分类记忆 ==========
  console.log('【阶段 4】记忆类型分布');
  console.log('-'.repeat(60));
  
  const typeRegistry = system['typeRegistry'];
  if (typeRegistry) {
    console.log('已检测的记忆类型:');
    console.log('  - facts: 事实型记忆（姓名、技能等）');
    console.log('  - patterns: 模式型记忆（习惯、偏好等）');
    console.log('  - skills: 技能型记忆');
    console.log('  - cases: 案例型记忆');
    console.log('  - events: 事件型记忆');
    console.log('  - preferences: 偏好型记忆\n');
  }

  // ========== 第五阶段：模拟未来查询 ==========
  console.log('【阶段 5】模拟未来 AI 查询');
  console.log('-'.repeat(60));
  
  for (const query of futureQueries) {
    console.log(`\n🔍 查询: "${query}"`);
    
    const results = await system.recall(query, {
      limit: 3,
      optimizeRecall: true,
      compress: true
    });
    
    if (results.results.length > 0) {
      console.log(`   找到 ${results.results.length} 条相关记忆:`);
      results.results.forEach((mem, i) => {
        const preview = mem.text.length > 60 
          ? mem.text.substring(0, 60) + '...' 
          : mem.text;
        console.log(`   ${i + 1}. ${preview}`);
      });
      
      if (results.compressedText) {
        console.log(`   📦 压缩后上下文 (${results.stats.compressedTokens} tokens):`);
        console.log(`      ${results.compressedText.substring(0, 100)}...`);
      }
    } else {
      console.log('   未找到相关记忆');
    }
  }

  // ========== 第六阶段：生成用户画像摘要 ==========
  console.log('\n【阶段 6】用户画像摘要');
  console.log('-'.repeat(60));
  
  const allMemories = await system.recall('', { limit: 100 });
  console.log(`基于 ${allMemories.results.length} 条记忆，生成用户画像:\n`);
  
  // 简单分类汇总
  const summary = {
    identity: [],
    skills: [],
    preferences: [],
    business: []
  };
  
  for (const mem of allMemories.results) {
    const text = mem.text.toLowerCase();
    if (text.includes('叫') || text.includes('是') || text.includes('公司')) {
      summary.identity.push(mem.text);
    }
    if (text.includes('擅长') || text.includes('技术') || text.includes('框架')) {
      summary.skills.push(mem.text);
    }
    if (text.includes('喜欢') || text.includes('痛点')) {
      summary.preferences.push(mem.text);
    }
    if (text.includes('公司') || text.includes('产品') || text.includes('用户')) {
      summary.business.push(mem.text);
    }
  }
  
  console.log('身份:', summary.identity.slice(0, 2).join('; '));
  console.log('技能:', summary.skills.slice(0, 2).join('; '));
  console.log('偏好:', summary.preferences.slice(0, 2).join('; '));
  console.log('业务:', summary.business.slice(0, 2).join('; '));

  // ========== 第七阶段：关闭系统 ==========
  console.log('\n【阶段 7】清理资源');
  console.log('-'.repeat(60));
  
  await system.shutdown();
  
  const finalStatus = system.getStatus();
  console.log(`最终状态: ${finalStatus.status}`);
  console.log(`总处理记忆: ${finalStatus.stats.totalMemories}`);
  console.log('\n✅ 工作流演示完成！');

  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║  这个例子展示了 unified-memory 的完整流程:                  ║');
  console.log('║  1. 对话 → 自动记忆提取                                    ║');
  console.log('║  2. 智能去重（避免重复存储）                               ║');
  console.log('║  3. 类型检测（自动分类）                                  ║');
  console.log('║  4. 高效检索（向量+文本混合）                             ║');
  console.log('║  5. 记忆压缩（节省 token）                                ║');
  console.log('║  6. 用户画像（自动汇总）                                  ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
}

// 运行工作流
runCompleteWorkflow().catch(console.error);
