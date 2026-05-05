/**
 * GBrain Integration Demo - GBrain 整合演示
 * 
 * 演示如何将 GBrain 的核心优势整合到 Unified Memory v5
 */

import { Resolver, DirectoryType } from './resolver.js';
import { TwoLayerFormat } from './memory_two_layer.js';
import { TypedLinks, TypedLinkType } from './typed_links.js';
import { Source, SourceManager, SourceType } from './source_attribution.js';
import { EntityDetector, EntityType } from './entity_detection.js';

/**
 * 演示：Resolver 决策树
 */
export function demoResolver() {
  console.log('=== Resolver 决策树演示 ===\n');
  
  const resolver = new Resolver();
  
  // 示例 1: 人物
  const personText = '张三加入了 Acme Corp，担任工程总监';
  const personResult = resolver.decide(personText);
  console.log('示例 1 - 人物:');
  console.log(`  文本：${personText}`);
  console.log(`  建议目录：${personResult.directory}`);
  console.log(`  置信度：${(personResult.confidence * 100).toFixed(0)}%`);
  console.log(`  理由：${personResult.reasoning}\n`);
  
  // 示例 2: 公司
  const companyText = 'Acme Corp 完成了 Series A 融资，2000 万美元';
  const companyResult = resolver.decide(companyText);
  console.log('示例 2 - 公司:');
  console.log(`  文本：${companyText}`);
  console.log(`  建议目录：${companyResult.directory}`);
  console.log(`  置信度：${(companyResult.confidence * 100).toFixed(0)}%`);
  console.log(`  理由：${companyResult.reasoning}\n`);
  
  // 示例 3: 原创
  const originalText = '我觉得 ambition-to-lifespan ratio has never been more broken';
  const originalResult = resolver.decide(originalText);
  console.log('示例 3 - 原创:');
  console.log(`  文本：${originalText}`);
  console.log(`  建议目录：${originalResult.directory}`);
  console.log(`  置信度：${(originalResult.confidence * 100).toFixed(0)}%`);
  console.log(`  理由：${originalResult.reasoning}\n`);
}

/**
 * 演示：两层页面格式
 */
export function demoTwoLayerFormat() {
  console.log('=== 两层页面格式演示 ===\n');
  
  // 创建页面
  const page = TwoLayerFormat.create({
    type: 'person',
    slug: 'zhang-san',
    tags: ['engineering', 'manager'],
    executiveSummary: '张三，工程总监，负责后端团队。通过李四介绍认识，有 5 年技术管理经验。',
    state: {
      '职位': '工程总监 @ Acme Corp',
      '团队': '20 人后端团队',
      '技术栈': 'Node.js, Go, Kubernetes',
      '汇报对象': 'CTO',
    },
    assessment: '技术扎实，管理能力优秀。团队稳定性高，代码质量口碑好。',
    openThreads: [
      { text: '讨论晋升路径', priority: 'medium' },
      { text: '跟进项目进度', priority: 'high', due: '2026-05-10' },
    ],
    timeline: [
      {
        date: '2026-05-04',
        summary: '飞书聊天，讨论项目延期',
        source: 'User, 飞书, 2026-05-04 14:30',
      },
      {
        date: '2026-04-28',
        summary: '第一次会议，介绍背景',
        source: 'User, 飞书会议, 2026-04-28 10:00',
      },
    ],
  });
  
  console.log('生成的页面:');
  console.log(page);
  console.log('\n');
  
  // 解析页面
  const parsed = TwoLayerFormat.parse(page);
  console.log('解析结果:');
  console.log(`  类型：${parsed.type}`);
  console.log(`  名称：${parsed.slug}`);
  console.log(`  标签：${parsed.tags.join(', ')}`);
  console.log(`  摘要：${parsed.executiveSummary}`);
  console.log(`  状态：${Object.keys(parsed.state).length} 个字段`);
  console.log(`  评估：${parsed.assessment ? '有' : '无'}`);
  console.log(`  开放线程：${parsed.openThreads.length} 个`);
  console.log(`  时间线：${parsed.timeline.length} 条记录`);
  console.log('\n');
  
  // 添加时间线条目
  const updatedPage = TwoLayerFormat.addTimelineEntry(page, {
    date: '2026-05-05',
    summary: '讨论季度目标',
    source: 'User, 飞书, 2026-05-05 16:00',
  });
  
  console.log('添加新时间线条目后:');
  console.log(updatedPage.split('## Timeline')[1].trim());
  console.log('\n');
}

/**
 * 演示：Typed Links
 */
export function demoTypedLinks() {
  console.log('=== Typed Links 演示 ===\n');
  
  const typedLinks = new TypedLinks();
  
  // 添加关系
  typedLinks.add('zhang-san', 'acme-corp', TypedLinkType.WORKS_AT, {
    role: 'Engineering Manager',
    started: '2025-01-01',
  });
  
  typedLinks.add('zhang-san', 'li-si', TypedLinkType.COLLEAGUE_OF, {
    department: 'Engineering',
  });
  
  typedLinks.add('zhang-san', 'li-si', TypedLinkType.REPORTS_TO, {
    since: '2025-06-01',
  });
  
  typedLinks.add('acme-corp', 'api-migration', TypedLinkType.HAS_PROJECT, {
    status: 'in-progress',
  });
  
  console.log('添加的关系:');
  console.log(`  张三 works_at Acme Corp`);
  console.log(`  张三 colleague_of 李四`);
  console.log(`  张三 reports_to 李四`);
  console.log(`  Acme Corp has_project API Migration\n`);
  
  // 查询关系
  const zhangRelations = typedLinks.getOutgoing('zhang-san');
  console.log('张三的所有关系:');
  for (const relation of zhangRelations) {
    const description = relation.type.replace(/_/g, ' ');
    console.log(`  - ${description}: ${relation.targetId}`);
  }
  console.log('\n');
  
  // 统计
  const stats = typedLinks.getStats();
  console.log('关系统计:');
  console.log(`  总关系数：${stats.totalRelations}`);
  console.log(`  按类型分布:`);
  for (const [type, count] of Object.entries(stats.byType)) {
    console.log(`    - ${type}: ${count}`);
  }
  console.log('\n');
}

/**
 * 演示：Source Attribution
 */
export function demoSourceAttribution() {
  console.log('=== Source Attribution 演示 ===\n');
  
  const sourceManager = new SourceManager();
  
  // 创建来源
  const source1 = new Source({
    type: SourceType.FEISHU,
    channel: 'direct message',
    timestamp: new Date('2026-05-04T14:30:00'),
    author: '刘选权',
  });
  
  const source2 = new Source({
    type: SourceType.MEETING,
    channel: 'team sync',
    timestamp: new Date('2026-05-03T10:00:00'),
    author: '张三',
  });
  
  // 添加来源
  sourceManager.add('mem_123', source1);
  sourceManager.add('mem_123', source2);
  
  // 格式化
  console.log('来源字符串:');
  console.log(`  ${sourceManager.format('mem_123')}\n`);
  
  // 验证
  const validation = sourceManager.validate('mem_123');
  console.log('验证结果:');
  console.log(`  有效：${validation.valid}`);
  console.log(`  原因：${validation.reason}\n`);
  
  // 解析来源字符串
  const sourceStr = '[Source: Feishu, direct message, 刘选权, 2026-05-04 14:30]';
  const parsedSource = Source.parse(sourceStr);
  console.log('解析来源字符串:');
  console.log(`  类型：${parsedSource.type}`);
  console.log(`  渠道：${parsedSource.channel}`);
  console.log(`  作者：${parsedSource.author}`);
  console.log(`  时间：${parsedSource.timestamp.toISOString()}`);
  console.log('\n');
}

/**
 * 演示：Entity Detection
 */
export function demoEntityDetection() {
  console.log('=== Entity Detection 演示 ===\n');
  
  const detector = new EntityDetector();
  
  const text = '张三加入了 Acme Corp，担任工程总监。Acme Corp 完成了 Series A 融资，2000 万美元。我觉得 ambition-to-lifespan ratio has never been more broken。';
  
  console.log('检测文本:');
  console.log(`  ${text}\n`);
  
  const entities = detector.detect(text);
  
  console.log('检测到的实体:');
  for (const entity of entities) {
    console.log(`  - ${entity.type}: ${entity.name} (${entity.confidence})`);
    console.log(`    目录：${entity.getDirectoryPath()}`);
    console.log(`    上下文：${entity.context}\n`);
  }
  
  // 异步检测
  console.log('异步检测:');
  detector.detectAsync(text);
  console.log('  已加入队列，将在后台处理\n');
}

/**
 * 主演示
 */
export function runDemo() {
  console.log('========================================');
  console.log('  GBrain Integration Demo');
  console.log('  Unified Memory v5 + GBrain 整合演示');
  console.log('========================================\n');
  
  demoResolver();
  demoTwoLayerFormat();
  demoTypedLinks();
  demoSourceAttribution();
  demoEntityDetection();
  
  console.log('========================================');
  console.log('  演示完成！');
  console.log('========================================');
}

// 运行演示
if (import.meta.url === `file://${process.argv[1]}`) {
  runDemo();
}
