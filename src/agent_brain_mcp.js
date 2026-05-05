#!/usr/bin/env node

/**
 * AgentBrain MCP 服务器
 * 将 AgentBrain 包装为 MCP 服务器，供 OpenClaw 调用
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { AgentBrain } from './agent_brain.js';
import { z } from 'zod';

// 创建 MCP 服务器
const server = new McpServer({
  name: 'agent-brain',
  version: '1.0.0',
  description: 'AI Agent 记忆大脑 - 自然语言记忆系统'
});

// 初始化 AgentBrain
const brain = new AgentBrain();

// 注册工具：记住信息
server.tool(
  'remember',
  '记住一段信息到 AgentBrain',
  {
    text: z.string().describe('要记住的文本内容'),
    category: z.string().optional().describe('分类标签'),
    importance: z.number().min(0).max(1).optional().describe('重要性评分 0-1')
  },
  async ({ text, category, importance }) => {
    try {
      const result = await brain.remember(text, { category, importance });
      return {
        content: [{
          type: 'text',
          text: `✅ 已记住: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"\nID: ${result.id}`
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

// 注册工具：搜索记忆
server.tool(
  'search',
  '在 AgentBrain 中搜索记忆',
  {
    query: z.string().describe('搜索查询'),
    limit: z.number().min(1).max(100).optional().describe('返回结果数量限制')
  },
  async ({ query, limit = 10 }) => {
    try {
      const results = await brain.search(query, { limit });
      
      if (results.length === 0) {
        return {
          content: [{
            type: 'text',
            text: `🔍 未找到与 "${query}" 相关的记忆`
          }]
        };
      }
      
      const formattedResults = results.map((result, index) => 
        `${index + 1}. ${result.text.substring(0, 100)}${result.text.length > 100 ? '...' : ''}\n   📅 ${new Date(result.created_at).toLocaleString()}\n   ⭐ 重要性: ${result.importance || 'N/A'}\n`
      ).join('\n');
      
      return {
        content: [{
          type: 'text',
          text: `🔍 搜索 "${query}" 找到 ${results.length} 条结果:\n\n${formattedResults}`
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

// 注册工具：获取上下文
server.tool(
  'get_context',
  '获取当前会话的上下文信息',
  {
    session_id: z.string().optional().describe('会话ID（可选）')
  },
  async ({ session_id }) => {
    try {
      const context = await brain.getContext({ sessionId: session_id });
      
      const stats = brain.getStats();
      
      return {
        content: [{
          type: 'text',
          text: `🧠 AgentBrain 上下文信息:\n\n` +
                `📊 统计:\n` +
                `   记忆数量: ${stats.rememberCount}\n` +
                `   搜索次数: ${stats.searchCount}\n` +
                `   归档次数: ${stats.archiveCount}\n` +
                `   运行时间: ${Math.floor(stats.uptime / 1000)}秒\n\n` +
                `💬 当前会话:\n` +
                `   会话ID: ${context.sessionId}\n` +
                `   对话历史: ${context.conversationHistory.length} 条\n` +
                `   最近记忆: ${context.recentMemories.length} 条`
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

// 注册工具：总结会话
server.tool(
  'summarize',
  '总结当前会话并归档重要信息',
  {},
  async () => {
    try {
      const summary = await brain.summarize();
      
      return {
        content: [{
          type: 'text',
          text: `📝 会话总结完成:\n\n` +
                `总结内容: ${summary.summary.substring(0, 200)}${summary.summary.length > 200 ? '...' : ''}\n` +
                `归档记忆: ${summary.archivedMemories.length} 条\n` +
                `提取关键点: ${summary.keyPoints.length} 个`
        }]
      };
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `❌ 总结失败: ${error.message}`
        }],
        isError: true
      };
    }
  }
);

// 注册工具：清理记忆
server.tool(
  'cleanup',
  '清理低重要性或过时的记忆',
  {
    threshold: z.number().min(0).max(1).optional().describe('重要性阈值（低于此值的记忆将被清理）'),
    max_age_days: z.number().min(1).optional().describe('最大保留天数')
  },
  async ({ threshold = 0.1, max_age_days = 30 }) => {
    try {
      const result = await brain.cleanup({ threshold, maxAgeDays: max_age_days });
      
      return {
        content: [{
          type: 'text',
          text: `🧹 记忆清理完成:\n\n` +
                `清理数量: ${result.cleanedCount} 条\n` +
                `保留数量: ${result.keptCount} 条\n` +
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

// 启动服务器
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('🧠 AgentBrain MCP 服务器已启动');
}

main().catch((error) => {
  console.error('❌ 服务器启动失败:', error);
  process.exit(1);
});