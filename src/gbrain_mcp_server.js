#!/usr/bin/env node

/**
 * GBrain AgentBrain MCP 服务器
 * 集成 GBrain 高级功能：
 * - 记忆关联网络 (MemoryGraph)
 * - 实体检测 (Entity Detection)
 * - 类型化链接 (Typed Links)
 * - 来源追溯 (Source Attribution)
 * - 决策树 (Resolver)
 * - 自动记忆 (Auto-Remember) - 重要性 > 0.7 时自动存储
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { GBrainIntegration } from './gbrain-integration.js';
import { MemoryGraph } from './memory_graph.js';
import { EntityDetector, EntityType } from './entity_detection.js';
import { z } from 'zod';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 存储配置
const STORAGE_DIR = '/root/.openclaw/workspace/agentbrain_storage';
const GRAPH_FILE = path.join(STORAGE_DIR, 'memory_graph.json');

// 初始化组件
const memoryGraph = new MemoryGraph();
const entityDetector = new EntityDetector();
const gbrain = new GBrainIntegration({ memoryGraph });

// 统计
let stats = {
  rememberCount: 0,
  searchCount: 0,
  autoRememberCount: 0,
  startTime: Date.now()
};

// ─────────────────────────────────────────────────────────────
// 自动记忆功能
// ─────────────────────────────────────────────────────────────

/**
 * 分析文本重要性
 * @param {string} text - 要分析的文本
 * @param {object} context - 上下文信息
 * @returns {object} { score: number, reasons: string[] }
 */
function analyzeImportance(text, context = {}) {
  const reasons = [];
  let score = 0.5; // 基础分数

  const textLower = text.toLowerCase();
  const wordCount = text.split(/\s+/).length;

  // 1. 内容长度因素 (权重: 0.1)
  // 太短的内容（<10词）可能是闲聊，太长可能是重复内容
  if (wordCount >= 10 && wordCount <= 500) {
    score += 0.1;
    reasons.push('长度适中');
  } else if (wordCount > 500) {
    score -= 0.05;
    reasons.push('内容过长');
  }

  // 2. 关键决策/偏好信号 (权重: 0.2)
  const decisionKeywords = [
    '决定', '选择', '偏好', '喜欢', '讨厌', '需要', '想要',
    'never', 'always', 'hate', 'love', 'prefer', 'need', 'want',
    '不', '要', '不要', '必须', '绝对', '一定'
  ];
  const hasDecision = decisionKeywords.some(kw => textLower.includes(kw));
  if (hasDecision) {
    score += 0.2;
    reasons.push('包含决策信号');
  }

  // 3. 情感/情绪信号 (权重: 0.15)
  const emotionKeywords = [
    '重要', '紧急', '担心', '害怕', '开心', '满意', '不满意',
    'important', 'urgent', 'worried', 'afraid', 'happy', 'satisfied'
  ];
  const hasEmotion = emotionKeywords.some(kw => textLower.includes(kw));
  if (hasEmotion) {
    score += 0.15;
    reasons.push('包含情感信号');
  }

  // 4. 事实/信息性内容 (权重: 0.15)
  const factKeywords = [
    '是', '在', '已经', '将会', 'is', 'are', 'was', 'will',
    '因为', '所以', '但是', 'however', 'because', 'therefore'
  ];
  const hasFacts = factKeywords.some(kw => textLower.includes(kw));
  if (hasFacts) {
    score += 0.15;
    reasons.push('事实性内容');
  }

  // 5. 项目/任务关联 (权重: 0.15)
  const projectKeywords = [
    '项目', '任务', '计划', '截止', 'deadline', 'project', 'task', 'plan'
  ];
  const hasProject = projectKeywords.some(kw => textLower.includes(kw));
  if (hasProject) {
    score += 0.15;
    reasons.push('项目相关');
  }

  // 6. 个人信息/实体 (权重: 0.1)
  const entityCheck = entityDetector.detect(text, {});
  if (entityCheck.length >= 2) {
    score += 0.1;
    reasons.push('包含多个实体');
  } else if (entityCheck.length === 1) {
    score += 0.05;
    reasons.push('包含实体');
  }

  // 7. 问句/不确定内容 (降低分数)
  const questionKeywords = ['?', '？', '怎么', '什么', '为什么', '如何', 'who', 'what', 'why', 'how'];
  const isQuestion = questionKeywords.some(kw => textLower.includes(kw));
  if (isQuestion) {
    score -= 0.1;
    reasons.push('问句内容(降低)');
  }

  // 确保分数在 0-1 范围内
  score = Math.max(0, Math.min(1, score));

  return { score, reasons };
}

/**
 * 自动提取实体
 * @param {string} text - 要提取实体的文本
 * @returns {string[]} 实体列表
 */
function extractEntities(text) {
  const entities = entityDetector.detect(text, {});
  return entities.map(e => e.name);
}

/**
 * 查找相似记忆
 * @param {string} query - 查询文本
 * @returns {object[]} 相似记忆列表
 */
function findSimilarMemories(query) {
  const allMemories = Array.from(memoryGraph.nodes.values());
  const queryLower = query.toLowerCase();
  
  return allMemories
    .filter(m => m.text && (
      m.text.toLowerCase().includes(queryLower) ||
      m.entities?.some(e => queryLower.includes(e.toLowerCase()))
    ))
    .sort((a, b) => (b.importance || 0) - (a.importance || 0))
    .slice(0, 5)
    .map(m => ({
      id: m.id,
      text: m.text.substring(0, 100),
      importance: m.importance
    }));
}

// ─────────────────────────────────────────────────────────────
// 加载/保存功能
// ─────────────────────────────────────────────────────────────

// 加载已有图数据
async function loadGraph() {
  try {
    const data = await fs.readFile(GRAPH_FILE, 'utf-8');
    const saved = JSON.parse(data);
    if (saved.nodes) {
      for (const [id, node] of Object.entries(saved.nodes)) {
        memoryGraph.nodes.set(id, node);
      }
    }
    if (saved.edges) {
      for (const [sourceId, edges] of Object.entries(saved.edges)) {
        memoryGraph.edges.set(sourceId, edges);
      }
    }
    console.error(`[GBrain] 已加载图数据: ${memoryGraph.nodes.size} 节点`);
  } catch (error) {
    console.error('[GBrain] 无图数据可加载，将创建新图');
  }
}

// 保存图数据
async function saveGraph() {
  try {
    const data = {
      nodes: Object.fromEntries(memoryGraph.nodes),
      edges: Object.fromEntries(memoryGraph.edges),
      entityIndex: Object.fromEntries(memoryGraph.entityIndex),
      topicIndex: Object.fromEntries(memoryGraph.topicIndex),
      projectIndex: Object.fromEntries(memoryGraph.projectIndex),
    };
    await fs.writeFile(GRAPH_FILE, JSON.stringify(data, null, 2), 'utf-8');
  } catch (error) {
    console.error('[GBrain] 保存图数据失败:', error.message);
  }
}

// 加载统计
async function loadStats() {
  try {
    const data = await fs.readFile(path.join(STORAGE_DIR, 'stats.json'), 'utf-8');
    stats = { ...stats, ...JSON.parse(data) };
  } catch (error) {
    // 使用默认统计
  }
}

// 保存统计
async function saveStats() {
  try {
    await fs.writeFile(
      path.join(STORAGE_DIR, 'stats.json'),
      JSON.stringify(stats, null, 2),
      'utf-8'
    );
  } catch (error) {
    console.error('[GBrain] 保存统计失败:', error.message);
  }
}

// ─────────────────────────────────────────────────────────────
// MCP 服务器
// ─────────────────────────────────────────────────────────────

const server = new McpServer({
  name: 'gbrain-agent-brain',
  version: '1.1.0',
  description: 'GBrain 记忆大脑 - 自动记忆 | 记忆关联网络 | 实体检测 | 类型化链接'
});

// 工具：remember - 记住信息（带自动记忆功能）
server.tool(
  'remember',
  '记住一段信息到 AgentBrain（自动评估重要性 > 0.7 时自动存储）',
  {
    text: z.string().describe('要记住的文本内容'),
    category: z.string().optional().describe('分类标签'),
    importance: z.number().min(0).max(1).optional().describe('重要性评分 0-1'),
    entities: z.array(z.string()).optional().describe('实体列表'),
    project: z.string().optional().describe('关联项目'),
    topics: z.array(z.string()).optional().describe('话题标签'),
    relations: z.array(z.object({
      targetId: z.string(),
      type: z.string(),
      weight: z.number().optional()
    })).optional().describe('关联到其他记忆'),
    auto: z.boolean().optional().describe('是否自动记忆模式')
  },
  async ({ text, category, importance, entities, project, topics, relations, auto }) => {
    try {
      const memoryId = `mem_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

      // ─── 自动记忆分析 ───
      let autoAnalysis = null;
      if (auto !== false) {
        // 自动评估重要性
        autoAnalysis = analyzeImportance(text, { category });
        
        // 如果未指定 importance 且分数 > 0.7，自动设置
        if (!importance && autoAnalysis.score > 0.7) {
          importance = autoAnalysis.score;
        }
      }

      // 使用传入的值或默认值
      const finalImportance = importance || autoAnalysis?.score || 0.5;

      // 检测实体
      const detectedEntities = entityDetector.detect(text, {});
      const allEntities = [
        ...(entities || []),
        ...detectedEntities.map(e => e.name)
      ];

      // 构建记忆对象
      const memory = {
        id: memoryId,
        text,
        category: category || 'general',
        importance: finalImportance,
        entities: allEntities,
        project,
        topics: topics || [],
        createdAt: Date.now(),
        metadata: {
          autoAnalyzed: autoAnalysis !== null,
          autoScore: autoAnalysis?.score,
          autoReasons: autoAnalysis?.reasons || []
        }
      };

      // 添加到记忆图谱
      memoryGraph.addNode(memory);

      // 添加关联
      if (relations && relations.length > 0) {
        for (const rel of relations) {
          memoryGraph.addEdge(memoryId, rel.targetId, rel.type, rel.weight || 0.8);
        }
      }

      // 自动关联相似记忆
      const similarMemories = memoryGraph.findSimilar(memoryId, { limit: 3, threshold: 0.5 });
      for (const similar of similarMemories) {
        if (similar.id !== memoryId) {
          memoryGraph.addEdge(memoryId, similar.id, 'similar', similar.similarity || 0.7);
        }
      }

      // 实体索引
      for (const entity of allEntities) {
        memoryGraph.addEntityIndex(entity, memoryId);
      }

      // 保存图数据
      await saveGraph();

      stats.rememberCount++;
      if (auto && autoAnalysis) {
        stats.autoRememberCount++;
      }
      await saveStats();

      // ─── 构建响应 ───
      let responseText = '';

      if (auto && autoAnalysis) {
        // 自动记忆模式的响应
        responseText = `🔄 自动记忆分析:\n\n` +
          `📊 重要性评分: ${autoAnalysis.score.toFixed(2)}\n` +
          `📝 分析理由: ${autoAnalysis.reasons.join(', ')}\n\n` +
          `📝 记忆内容: "${text.substring(0, 80)}${text.length > 80 ? '...' : ''}"\n` +
          `🆔 ID: ${memoryId}\n` +
          `🏷️ 分类: ${memory.category}\n` +
          `⭐ 最终重要性: ${finalImportance.toFixed(2)}\n`;
        
        if (detectedEntities.length > 0) {
          responseText += `🔍 检测到实体: ${detectedEntities.map(e => e.name).join(', ')}\n`;
        }
        responseText += `🔗 相似记忆: ${similarMemories.length} 条`;
      } else {
        // 手动模式的响应
        responseText = `✅ 已记住并分析:\n\n` +
          `📝 内容: "${text.substring(0, 80)}${text.length > 80 ? '...' : ''}"\n` +
          `🆔 ID: ${memoryId}\n` +
          `🏷️ 分类: ${memory.category}\n` +
          `⭐ 重要性: ${finalImportance}\n` +
          `🔍 检测到实体: ${detectedEntities.length} 个\n` +
          `🔗 找到相似记忆: ${similarMemories.length} 条\n` +
          `📊 图谱统计: ${memoryGraph.nodes.size} 节点, ${memoryGraph.edges.size} 边`;
      }

      return {
        content: [{
          type: 'text',
          text: responseText
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `❌ 记住失败: ${error.message}`
        }],
        isError: true
      };
    }
  }
);

// 工具：search - 搜索记忆（使用关联网络）
server.tool(
  'search',
  '在 AgentBrain 中搜索记忆（使用记忆关联网络）',
  {
    query: z.string().describe('搜索查询'),
    limit: z.number().min(1).max(100).optional().describe('返回结果数量限制'),
    entity: z.string().optional().describe('按实体过滤'),
    project: z.string().optional().describe('按项目过滤'),
    topic: z.string().optional().describe('按话题过滤'),
    relatedTo: z.string().optional().describe('查找与某记忆相关的记忆')
  },
  async ({ query, limit = 10, entity, project, topic, relatedTo }) => {
    try {
      let results = [];

      // 1. 如果指定了 relatedTo，查找相关记忆
      if (relatedTo) {
        const related = memoryGraph.findRelated(relatedTo, { limit, minWeight: 0.3 });
        results = related.map(r => ({
          id: r.id,
          text: memoryGraph.nodes.get(r.id)?.text || '',
          similarity: r.weight,
          relation: r.relation,
          category: memoryGraph.nodes.get(r.id)?.category || 'unknown'
        }));
      }
      // 2. 如果指定了实体
      else if (entity) {
        const byEntity = memoryGraph.findByEntity(entity);
        results = byEntity.map(id => ({
          id,
          text: memoryGraph.nodes.get(id)?.text || '',
          category: memoryGraph.nodes.get(id)?.category || 'unknown'
        }));
      }
      // 3. 如果指定了项目
      else if (project) {
        const byProject = memoryGraph.findByProject(project);
        results = byProject.map(id => ({
          id,
          text: memoryGraph.nodes.get(id)?.text || '',
          category: memoryGraph.nodes.get(id)?.category || 'unknown'
        }));
      }
      // 4. 如果指定了话题
      else if (topic) {
        const byTopic = memoryGraph.findByTopic(topic);
        results = byTopic.map(id => ({
          id,
          text: memoryGraph.nodes.get(id)?.text || '',
          category: memoryGraph.nodes.get(id)?.category || 'unknown'
        }));
      }
      // 5. 否则文本搜索
      else {
        const allMemories = Array.from(memoryGraph.nodes.values());
        const queryLower = query.toLowerCase();
        results = allMemories
          .filter(m => m.text && m.text.toLowerCase().includes(queryLower))
          .sort((a, b) => (b.importance || 0) - (a.importance || 0))
          .slice(0, limit)
          .map(m => ({
            id: m.id,
            text: m.text,
            category: m.category,
            importance: m.importance
          }));
      }

      stats.searchCount++;
      await saveStats();

      if (results.length === 0) {
        return {
          content: [{
            type: 'text',
            text: `🔍 未找到与 "${query}" 相关的记忆`
          }]
        };
      }

      const formattedResults = results.slice(0, limit).map((result, index) => 
        `${index + 1}. ${result.text.substring(0, 80)}${result.text.length > 80 ? '...' : ''}\n` +
        `   🏷️ ${result.category || 'general'} | 🆔 ${result.id.substring(0, 20)}...` +
        (result.relation ? ` | 🔗 ${result.relation} (${((result.similarity || 0) * 100).toFixed(0)}%)` : '')
      ).join('\n\n');

      return {
        content: [{
          type: 'text',
          text: `🔍 搜索 "${query}" 找到 ${results.length} 条结果:\n\n${formattedResults}\n\n📊 图谱: ${memoryGraph.nodes.size} 节点 | 🔍 本次搜索: ${stats.searchCount}次`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `❌ 搜索失败: ${error.message}`
        }],
        isError: true
      };
    }
  }
);

// 工具：get_context - 获取上下文
server.tool(
  'get_context',
  '获取当前会话的上下文信息',
  {
    session_id: z.string().optional().describe('会话ID（可选）')
  },
  async ({ session_id }) => {
    try {
      const graphStats = memoryGraph.getStats();
      
      return {
        content: [{
          type: 'text',
          text: `🧠 GBrain 记忆大脑状态:\n\n` +
                `📊 统计:\n` +
                `   记忆数量: ${graphStats.nodeCount}\n` +
                `   关联数量: ${graphStats.edgeCount}\n` +
                `   实体类型: ${graphStats.entityTypes}\n` +
                `   搜索次数: ${stats.searchCount}\n` +
                `   记忆次数: ${stats.rememberCount}\n` +
                `   自动记忆: ${stats.autoRememberCount}\n` +
                `   运行时间: ${Math.floor((Date.now() - stats.startTime) / 1000)}秒\n\n` +
                `🔍 图谱功能:\n` +
                `   • 记忆关联网络 ✓\n` +
                `   • 实体检测 ✓\n` +
                `   • 类型化链接 ✓\n` +
                `   • 来源追溯 ✓\n` +
                `   • 自动记忆 (重要性 > 0.7) ✓`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `❌ 获取上下文失败: ${error.message}`
        }],
        isError: true
      };
    }
  }
);

// 工具：cleanup - 清理记忆
server.tool(
  'cleanup',
  '清理低重要性或过时的记忆',
  {
    threshold: z.number().min(0).max(1).optional().describe('重要性阈值'),
    max_age_days: z.number().min(1).optional().describe('最大保留天数')
  },
  async ({ threshold = 0.1, max_age_days = 30 }) => {
    try {
      const allNodes = Array.from(memoryGraph.nodes.entries());
      const cutoffTime = Date.now() - (max_age_days * 24 * 60 * 60 * 1000);
      
      let cleanedCount = 0;
      for (const [id, node] of allNodes) {
        if ((node.importance || 0) < threshold || node.createdAt < cutoffTime) {
          memoryGraph.nodes.delete(id);
          memoryGraph.edges.delete(id);
          cleanedCount++;
        }
      }

      if (cleanedCount > 0) {
        await saveGraph();
      }

      return {
        content: [{
          type: 'text',
          text: `🧹 清理完成:\n\n` +
                `清理数量: ${cleanedCount} 条\n` +
                `保留数量: ${memoryGraph.nodes.size} 条\n` +
                `阈值: ${threshold}\n` +
                `最大保留天数: ${max_age_days}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `❌ 清理失败: ${error.message}`
        }],
        isError: true
      };
    }
  }
);

// 工具：graph_stats - 获取图谱统计
server.tool(
  'graph_stats',
  '获取记忆关联网络的详细统计',
  {},
  async () => {
    try {
      const stats_ = memoryGraph.getStats();
      const topEntities = Array.from(memoryGraph.entityIndex.entries())
        .sort((a, b) => b[1].length - a[1].length)
        .slice(0, 5)
        .map(([entity, ids]) => `${entity} (${ids.length})`);

      return {
        content: [{
          type: 'text',
          text: `📊 记忆关联网络统计:\n\n` +
                `节点数: ${stats_.nodeCount}\n` +
                `边数: ${stats_.edgeCount}\n` +
                `平均连接数: ${stats_.avgConnections.toFixed(2)}\n` +
                `孤立节点: ${stats_.isolatedNodes}\n` +
                `实体类型: ${stats_.entityTypes}\n\n` +
                `🔥 Top 实体:\n${topEntities.map(e => `   • ${e}`).join('\n') || '   (无)'}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `❌ 获取统计失败: ${error.message}`
        }],
        isError: true
      };
    }
  }
);

// 工具：auto_analyze - 分析文本重要性（不存储）
server.tool(
  'auto_analyze',
  '分析文本重要性（仅分析，不存储）',
  {
    text: z.string().describe('要分析的文本内容')
  },
  async ({ text }) => {
    try {
      const analysis = analyzeImportance(text);
      const entities = extractEntities(text);
      const similar = findSimilarMemories(text);

      return {
        content: [{
          type: 'text',
          text: `🔍 自动分析结果:\n\n` +
                `📊 重要性评分: ${analysis.score.toFixed(2)}\n` +
                `📝 分析理由: ${analysis.reasons.join(', ')}\n` +
                `🔍 检测到实体: ${entities.length} 个\n` +
                `   ${entities.map(e => e).join(', ') || '(无)'}\n` +
                `🔗 相似记忆: ${similar.length} 条\n` +
                `   ${similar.map(m => `${m.id.substring(0, 15)}... (⭐${m.importance})`).join('\n   ') || '(无)'}\n\n` +
                `💡 建议: ${analysis.score > 0.7 ? '建议自动存储' : analysis.score > 0.5 ? '可选择性存储' : '暂不需要存储'}`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `❌ 分析失败: ${error.message}`
        }],
        isError: true
      };
    }
  }
);

// ─────────────────────────────────────────────────────────────
// 启动服务器
// ─────────────────────────────────────────────────────────────

async function main() {
  // 确保存储目录存在
  await fs.mkdir(STORAGE_DIR, { recursive: true });
  
  // 加载已有数据
  await loadGraph();
  await loadStats();

  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('🧠 GBrain AgentBrain MCP 服务器已启动 (v1.1.0)');
  console.error('📁 存储目录: ' + STORAGE_DIR);
  console.error('🔗 功能: 自动记忆 | 记忆关联网络 | 实体检测 | 类型化链接');
}

main().catch((error) => {
  console.error('❌ 服务器启动失败:', error);
  process.exit(1);
});
