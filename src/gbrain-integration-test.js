/**
 * GBrain Integration Test - GBrain 集成测试
 * 
 * 测试 GBrain 功能与 Unified Memory 的集成
 */

import { GBrainIntegration, createGBrainIntegration } from './gbrain-integration.js';
import { MemoryGraph } from './memory_graph.js';
import { DirectoryType } from './resolver.js';

/**
 * 测试：基本集成
 */
export function testBasicIntegration() {
  console.log('=== 测试：基本集成 ===\n');
  
  const memoryGraph = new MemoryGraph();
  const integration = createGBrainIntegration({
    memoryGraph,
    enableTwoLayer: true,
    enableTypedLinks: true,
    enableSourceAttribution: true,
    enableEntityDetection: true,
    enableResolver: true,
  });
  
  // 创建测试内存
  const memory = {
    id: 'mem_123',
    text: '张三加入了 Acme Corp，担任工程总监。Acme Corp 完成了 Series A 融资，2000 万美元。',
    type: 'fact',
    category: 'business',
    timestamp: new Date(),
  };
  
  // 保存内存
  const result = integration.saveMemory(memory, {
    sourceType: 'feishu',
    channel: 'direct message',
    author: '刘选权',
    timestamp: new Date(),
  });
  
  console.log('内存 ID:', result.memory.id);
  console.log('目录:', result.gbrain.directory);
  console.log('两层格式:', result.gbrain.twoLayer ? '有' : '无');
  console.log('来源:', result.gbrain.source ? result.gbrain.source.format() : '无');
  console.log('实体数量:', result.gbrain.entities.length);
  console.log('关系数量:', result.gbrain.typedLinks.length);
  console.log('\n');
}

/**
 * 测试：两层页面格式
 */
export function testTwoLayerFormat() {
  console.log('=== 测试：两层页面格式 ===\n');
  
  const integration = createGBrainIntegration();
  
  const memory = {
    id: 'mem_456',
    text: '张三，工程总监，负责后端团队。',
    type: 'person',
    slug: 'zhang-san',
    tags: ['engineering', 'manager'],
  };
  
  const context = {
    entities: [
      { type: 'person', name: '张三', slug: 'zhang-san' },
      { type: 'company', name: 'Acme Corp', slug: 'acme-corp' },
    ],
    timeline: [
      {
        date: '2026-05-04',
        summary: '飞书聊天，讨论项目延期',
        source: 'User, 飞书, 2026-05-04 14:30',
      },
    ],
  };
  
  const twoLayer = integration.createTwoLayerPage(memory, context);
  
  console.log('生成的两层页面:');
  console.log(twoLayer);
  console.log('\n');
}

/**
 * 测试：Source Attribution
 */
export function testSourceAttribution() {
  console.log('=== 测试：Source Attribution ===\n');
  
  const integration = createGBrainIntegration();
  
  const memory = {
    id: 'mem_789',
    text: '测试内存',
  };
  
  const result = integration.saveMemory(memory, {
    sourceType: 'feishu',
    channel: 'direct message',
    author: '刘选权',
    timestamp: new Date('2026-05-04T14:30:00'),
  });
  
  console.log('来源字符串:');
  console.log(result.gbrain.source.format());
  console.log('\n');
}

/**
 * 测试：Entity Detection
 */
export function testEntityDetection() {
  console.log('=== 测试：Entity Detection ===\n');
  
  const integration = createGBrainIntegration();
  
  const memory = {
    id: 'mem_abc',
    text: '张三加入了 Acme Corp，担任工程总监。Acme Corp 完成了 Series A 融资，2000 万美元。',
  };
  
  const result = integration.saveMemory(memory, {});
  
  console.log('检测到的实体:');
  for (const entity of result.gbrain.entities) {
    console.log(`  - ${entity.type}: ${entity.name} (${entity.confidence})`);
    console.log(`    目录：${entity.getDirectoryPath()}`);
  }
  console.log('\n');
}

/**
 * 测试：Resolver 决策树
 */
export function testResolver() {
  console.log('=== 测试：Resolver 决策树 ===\n');
  
  const integration = createGBrainIntegration();
  
  const testCases = [
    {
      text: '张三加入了 Acme Corp，担任工程总监',
      expected: DirectoryType.PEOPLE,
    },
    {
      text: 'Acme Corp 完成了 Series A 融资，2000 万美元',
      expected: DirectoryType.COMPANIES,
    },
    {
      text: '我觉得 ambition-to-lifespan ratio has never been more broken',
      expected: DirectoryType.ORIGINALS,
    },
  ];
  
  for (const testCase of testCases) {
    const memory = {
      id: `mem_${Math.random().toString(36).substring(7)}`,
      text: testCase.text,
    };
    
    const result = integration.saveMemory(memory, {});
    
    console.log(`文本：${testCase.text}`);
    console.log(`  建议目录：${result.gbrain.directory}`);
    console.log(`  预期目录：${testCase.expected}`);
    console.log(`  匹配：${result.gbrain.directory === testCase.expected ? '✅' : '❌'}`);
    console.log('\n');
  }
}

/**
 * 测试：Typed Links
 */
export function testTypedLinks() {
  console.log('=== 测试：Typed Links ===\n');
  
  const integration = createGBrainIntegration();
  
  const memory = {
    id: 'mem_def',
    text: '张三在 Acme Corp 工作，汇报给李四。',
  };
  
  const result = integration.saveMemory(memory, {
    relations: [
      {
        sourceId: 'zhang-san',
        targetId: 'acme-corp',
        type: 'works_at',
        metadata: { role: 'Engineering Manager' },
      },
      {
        sourceId: 'zhang-san',
        targetId: 'li-si',
        type: 'reports_to',
        metadata: { since: '2025-01-01' },
      },
    ],
  });
  
  console.log('添加的关系:');
  for (const relation of result.gbrain.typedLinks) {
    console.log(`  - ${relation.sourceId} ${relation.type} ${relation.targetId}`);
  }
  console.log('\n');
}

/**
 * 主演示
 */
export function runTests() {
  console.log('========================================');
  console.log('  GBrain Integration Tests');
  console.log('  Unified Memory v5 + GBrain 集成测试');
  console.log('========================================\n');
  
  testBasicIntegration();
  testTwoLayerFormat();
  testSourceAttribution();
  testEntityDetection();
  testResolver();
  testTypedLinks();
  
  console.log('========================================');
  console.log('  所有测试完成！');
  console.log('========================================');
}

// 运行测试
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests();
}
