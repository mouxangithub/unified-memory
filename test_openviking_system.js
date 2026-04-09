/**
 * OpenViking 集成系统测试
 */

import { createOpenVikingSystem, VikingURI, URI_TEMPLATES, MEMORY_CATEGORIES } from './src/openviking_system.js';
import { logger } from './src/utils/logger.js';

async function testOpenVikingSystem() {
  console.log('\n' + '='.repeat(80));
  console.log('🎯 OpenViking 集成系统测试');
  console.log('='.repeat(80) + '\n');
  
  // 创建系统
  const system = createOpenVikingSystem({
    enableIntentAnalysis: true,
    enableHierarchicalRetrieval: true,
    enableRerank: true,
    enableSessionManagement: true,
    enableMemoryExtraction: true,
    enableFileSystem: true,
    enableDocumentParsing: true,
    enableRelationManagement: true,
    enableLayeredCompression: true
  });
  
  // 初始化
  await system.initialize();
  
  console.log('✅ 系统初始化完成\n');
  
  // ========== 测试 1: Viking URI ==========
  console.log('📦 测试 1: Viking URI 系统\n');
  
  const userMemoryUri = URI_TEMPLATES.USER_PREFERENCES('ou_123');
  console.log(`用户偏好 URI: ${userMemoryUri}`);
  
  const agentSkillUri = URI_TEMPLATES.AGENT_SKILL('agent_001', 'code-search');
  console.log(`Agent 技能 URI: ${agentSkillUri}`);
  
  const sessionUri = URI_TEMPLATES.SESSION_MESSAGES('chat_001');
  console.log(`Session 消息 URI: ${sessionUri}`);
  
  const uri = new VikingURI(userMemoryUri);
  console.log(`URI 解析:`);
  console.log(`  - Scope: ${uri.scope}`);
  console.log(`  - Path: ${uri.path}`);
  console.log(`  - Name: ${uri.name}`);
  console.log(`  - Is Directory: ${uri.isDirectory}\n`);
  
  // ========== 测试 2: 意图分析 ==========
  console.log('📦 测试 2: 意图分析\n');
  
  const query = '帮我创建一个 RFC 文档';
  const queryPlan = await system.intentAnalyzer.analyze(query);
  
  console.log(`查询: "${query}"`);
  console.log(`生成 ${queryPlan.typedQueries.length} 个类型化查询:\n`);
  
  for (const typedQuery of queryPlan.typedQueries) {
    console.log(`  - [${typedQuery.contextType}] ${typedQuery.query}`);
    console.log(`    意图: ${typedQuery.intent}, 优先级: ${typedQuery.priority}\n`);
  }
  
  // ========== 测试 3: Session 管理 ==========
  console.log('📦 测试 3: Session 管理\n');
  
  const sessionId = 'test_session_001';
  const session = await system.getSession(sessionId, {
    autoCreate: true,
    userId: 'ou_123',
    agentId: 'agent_001'
  });
  
  console.log(`创建 Session: ${sessionId}`);
  
  // 添加消息
  await system.addMessage(sessionId, 'user', '我偏好使用深色主题');
  await system.addMessage(sessionId, 'assistant', '好的，我会记住您的偏好。');
  
  console.log(`添加 2 条消息\n`);
  
  // 记录上下文使用
  await system.sessionManager.recordContextUsage(sessionId, [
    'viking://user/ou_123/memories/preferences/theme.md'
  ]);
  
  console.log(`记录上下文使用\n`);
  
  // 提交 Session
  const commitResult = await system.commitSession(sessionId);
  
  console.log(`提交 Session:`);
  console.log(`  - 状态: ${commitResult.status}`);
  console.log(`  - 任务 ID: ${commitResult.taskId}`);
  console.log(`  - 归档: ${commitResult.archived}\n`);
  
  // ========== 测试 4: 记忆提取 ==========
  console.log('📦 测试 4: 记忆提取\n');
  
  const testSession = await system.getSession('test_extraction', {
    autoCreate: true,
    userId: 'ou_123',
    agentId: 'agent_001'
  });
  
  await system.addMessage('test_extraction', 'user', '我叫刘选权，是 OpenClaw 的创始人');
  await system.addMessage('test_extraction', 'user', '我喜欢使用 JavaScript 和 Python');
  await system.addMessage('test_extraction', 'user', '上次我们解决了 Unified Memory 的性能问题');
  
  const memories = await system.memoryExtractor.extract(testSession);
  
  console.log(`提取到 ${memories.length} 条记忆:\n`);
  
  for (const memory of memories) {
    console.log(`  - [${memory.category}] ${memory.content.substring(0, 50)}...`);
    console.log(`    重要性: ${memory.importance.toFixed(2)}, 置信度: ${memory.confidence.toFixed(2)}\n`);
  }
  
  // ========== 测试 5: 重排序 ==========
  console.log('📦 测试 5: 重排序\n');
  
  const documents = [
    { uri: 'doc1', text: 'OpenClaw 是一个 AI 助手平台', score: 0.8 },
    { uri: 'doc2', text: 'Unified Memory 是记忆管理系统', score: 0.7 },
    { uri: 'doc3', text: 'OpenViking 是上下文数据库', score: 0.9 }
  ];
  
  const reranked = await system.reranker.rerank('OpenClaw 平台', documents);
  
  console.log(`重排序结果:\n`);
  
  for (const result of reranked) {
    console.log(`  - [${result.uri}] 分数: ${result.finalScore.toFixed(3)}`);
    console.log(`    ${result.text}\n`);
  }
  
  // ========== 测试 6: 关系管理 ==========
  console.log('📦 测试 6: 关系管理\n');
  
  await system.relations.link(
    'viking://resources/docs/api.md',
    'viking://resources/docs/auth.md',
    'related_to'
  );
  
  await system.relations.link(
    'viking://resources/docs/api.md',
    'viking://resources/examples/api-demo.md',
    'references'
  );
  
  console.log(`添加 2 个关系\n`);
  
  const relations = await system.relations.relations('viking://resources/docs/api.md');
  
  console.log(`查询关系:\n`);
  
  for (const relation of relations) {
    console.log(`  - [${relation.direction}] ${relation.type}`);
    console.log(`    ${relation.source} -> ${relation.target}\n`);
  }
  
  // ========== 测试 7: 分层压缩 ==========
  console.log('📦 测试 7: 分层压缩\n');
  
  const testMemories = [
    {
      id: 'mem_001',
      text: '刘选权是 OpenClaw 的创始人，公司位于北京。他拥有 10 年的软件开发经验，擅长 JavaScript、Python 和 Go 编程。',
      type: 'facts',
      importance: 0.9
    },
    {
      id: 'mem_002',
      text: '刘选权每天早上 7 点起床，习惯喝一杯咖啡后开始工作。他喜欢在早上处理最重要的任务。',
      type: 'patterns',
      importance: 0.7
    }
  ];
  
  const layers = system.layeredCompressor.generateAllLayers(testMemories[0]);
  
  console.log(`记忆分层:\n`);
  console.log(`  L0 (抽象): ${layers.L0.text}`);
  console.log(`  Tokens: ${layers.L0.tokens}\n`);
  console.log(`  L1 (概览): ${layers.L1.text.substring(0, 100)}...`);
  console.log(`  Tokens: ${layers.L1.tokens}\n`);
  console.log(`  L2 (详情): ${layers.L2.text.substring(0, 100)}...`);
  console.log(`  Tokens: ${layers.L2.tokens}\n`);
  
  // ========== 测试 8: 系统状态 ==========
  console.log('📦 测试 8: 系统状态\n');
  
  const status = system.getStatus();
  
  console.log(`系统状态:`);
  console.log(`  - 初始化: ${status.initialized}`);
  console.log(`  - 总搜索次数: ${status.stats.totalSearches}`);
  console.log(`  - 总 Session 数: ${status.stats.totalSessions}`);
  console.log(`  - 提取记忆数: ${status.stats.totalMemoriesExtracted}\n`);
  
  // ========== 测试 9: 健康检查 ==========
  console.log('📦 测试 9: 健康检查\n');
  
  const health = system.healthCheck();
  
  console.log(`健康状态: ${health.status}\n`);
  
  console.log(`组件状态:`);
  
  for (const [name, component] of Object.entries(health.components)) {
    console.log(`  - ${name}: ${component.status}`);
  }
  
  console.log('\n' + '='.repeat(80));
  console.log('✅ 所有测试完成！');
  console.log('='.repeat(80) + '\n');
  
  // 关闭系统
  await system.shutdown();
}

// 运行测试
testOpenVikingSystem().catch(error => {
  console.error('测试失败:', error);
  process.exit(1);
});
