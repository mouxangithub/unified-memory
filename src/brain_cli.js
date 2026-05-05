#!/usr/bin/env node
/**
 * AgentBrain CLI - 命令行测试工具
 * 
 * 简单测试 AgentBrain 的自然语言接口
 * 
 * @example
 * node brain_cli.js remember "用户喜欢单引号"
 * node brain_cli.js search "Python"
 * node brain_cli.js archive
 */

import { AgentBrain } from './agent_brain.js';

const brain = new AgentBrain();

const args = process.argv.slice(2);
const command = args[0];
const text = args.slice(1).join(' ');

async function main() {
  console.log(`\n🧠 AgentBrain CLI`);
  console.log(`Command: ${command}`);
  console.log(`Text: "${text}"`);
  console.log(`---\n`);

  try {
    switch (command) {
      case 'remember':
        if (!text) {
          console.error('❌ 请提供要记住的内容');
          process.exit(1);
        }
        const rememberResult = await brain.remember(text);
        console.log('✅ 记住成功:', JSON.stringify(rememberResult, null, 2));
        break;

      case 'forget':
        if (!text) {
          console.error('❌ 请提供要忘记的内容');
          process.exit(1);
        }
        const forgetResult = await brain.forget(text);
        console.log('✅ 忘记成功:', JSON.stringify(forgetResult, null, 2));
        break;

      case 'search':
        if (!text) {
          console.error('❌ 请提供搜索查询');
          process.exit(1);
        }
        const searchResults = await brain.search(text);
        console.log(`✅ 搜索到 ${searchResults.length} 条结果:`);
        searchResults.forEach((r, i) => {
          const content = r.content || r.text || JSON.stringify(r);
          console.log(`  ${i + 1}. ${content.substring(0, 100)}...`);
        });
        break;

      case 'context':
        const context = await brain.getContext({ level: text || 'working' });
        console.log('📋 上下文:');
        console.log(JSON.stringify(context, null, 2));
        break;

      case 'archive':
        const archiveResult = await brain.archive({
          summary: text || 'CLI 归档',
        });
        console.log('✅ 归档成功:', JSON.stringify(archiveResult, null, 2));
        break;

      case 'summarize':
        const summary = await brain.summarize();
        console.log('📝 总结:', summary);
        break;

      case 'stats':
        const stats = brain.getStats();
        console.log('📊 统计:', JSON.stringify(stats, null, 2));
        break;

      case 'cleanup':
        const cleanupResult = brain.cleanup({ level: text || 'working' });
        console.log('🧹 清理完成:', JSON.stringify(cleanupResult, null, 2));
        break;

      case 'add':
        // 添加对话消息
        if (!text) {
          console.error('❌ 请提供消息内容');
          process.exit(1);
        }
        brain.addMessage(text);
        console.log('💬 消息已添加');
        break;

      case 'help':
        console.log(`
🧠 AgentBrain CLI 帮助

用法: node brain_cli.js <command> [text]

命令:
  remember <text>   记住内容
  forget <text>      忘记内容
  search <text>      搜索内容
  context [level]    获取上下文 (working/session/all)
  archive [summary]  归档当前对话
  summarize          总结当前对话
  stats              获取统计信息
  cleanup [level]    清理 (working/session/all)
  add <text>         添加对话消息
  help               显示帮助

示例:
  node brain_cli.js remember "用户喜欢单引号"
  node brain_cli.js search "Python 异步"
  node brain_cli.js archive "讨论了 React 性能"
        `);
        break;

      default:
        console.error(`❌ 未知命令: ${command}`);
        console.log('运行 "node brain_cli.js help" 查看帮助');
        process.exit(1);
    }
  } catch (error) {
    console.error('❌ 错误:', error.message);
    console.error(error.stack);
    process.exit(1);
  }

  console.log('\n');
}

main();