#!/usr/bin/env node

/**
 * Unified Memory Hook Builder
 * 
 * 自动构建并启用 OpenClaw Hook
 * 在 npm install 或 clawhub install 时自动执行
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 颜色输出
const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(color, message) {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// 检测 OpenClaw 安装路径
function detectOpenClawPath() {
  const possiblePaths = [
    process.env.OPENCLAW_HOME,
    process.env.HOME + '/.openclaw',
    '/root/.openclaw',
    path.resolve(__dirname, '../../..')
  ];

  for (const p of possiblePaths) {
    if (p && fs.existsSync(p)) {
      return p;
    }
  }

  return null;
}

// 构建 Hook
function buildHook() {
  log('blue', '🧠 Building Unified Memory Hook...');

  const openclawPath = detectOpenClawPath();
  
  if (!openclawPath) {
    log('yellow', '⚠️  OpenClaw installation not found, skipping hook build');
    log('yellow', '   Set OPENCLAW_HOME environment variable to specify custom path');
    return false;
  }

  log('green', `✅ Found OpenClaw at: ${openclawPath}`);

  // Hook 目录
  const hooksDir = path.join(openclawPath, 'hooks');
  const hookDir = path.join(hooksDir, 'unified-memory');
  const hookDisabledDir = path.join(hooksDir, 'unified-memory.disabled');

  // 如果已存在禁用的 Hook，启用它
  if (fs.existsSync(hookDisabledDir)) {
    log('blue', '📦 Enabling existing Hook...');
    
    if (fs.existsSync(hookDir)) {
      log('yellow', '⚠️  Hook directory already exists, removing...');
      fs.rmSync(hookDir, { recursive: true, force: true });
    }
    
    fs.renameSync(hookDisabledDir, hookDir);
    log('green', '✅ Hook enabled successfully!');
    return true;
  }

  // 如果已存在启用的 Hook，更新它
  if (fs.existsSync(hookDir)) {
    log('blue', '📦 Updating existing Hook...');
    
    // 检查 HOOK.md 和 handler.js 是否存在
    const hookMd = path.join(hookDir, 'HOOK.md');
    const handlerJs = path.join(hookDir, 'handler.js');
    
    if (fs.existsSync(hookMd) && fs.existsSync(handlerJs)) {
      log('green', '✅ Hook already installed and enabled!');
      return true;
    }
  }

  // 创建新的 Hook
  log('blue', '📦 Creating new Hook...');
  
  // 确保 hooks 目录存在
  if (!fs.existsSync(hooksDir)) {
    fs.mkdirSync(hooksDir, { recursive: true });
  }

  // 创建 Hook 目录
  if (!fs.existsSync(hookDir)) {
    fs.mkdirSync(hookDir, { recursive: true });
  }

  // 源文件路径（从 skill 目录复制）
  const skillDir = path.resolve(__dirname, '..');
  const sourceHookMd = path.join(skillDir, 'HOOK.md');
  const sourceHandlerJs = path.join(skillDir, 'hooks', 'handler.js');

  // 如果源文件不存在，尝试从 hooks 目录复制
  const altSourceHookMd = path.join(skillDir, 'hooks', 'HOOK.md');

  // 复制 HOOK.md
  if (fs.existsSync(sourceHookMd)) {
    fs.copyFileSync(sourceHookMd, path.join(hookDir, 'HOOK.md'));
    log('green', '✅ Copied HOOK.md');
  } else if (fs.existsSync(altSourceHookMd)) {
    fs.copyFileSync(altSourceHookMd, path.join(hookDir, 'HOOK.md'));
    log('green', '✅ Copied HOOK.md from hooks directory');
  } else {
    log('yellow', '⚠️  HOOK.md not found, creating default...');
    createDefaultHookMd(hookDir);
  }

  // 复制 handler.js
  if (fs.existsSync(sourceHandlerJs)) {
    fs.copyFileSync(sourceHandlerJs, path.join(hookDir, 'handler.js'));
    log('green', '✅ Copied handler.js');
  } else {
    log('yellow', '⚠️  handler.js not found, creating default...');
    createDefaultHandler(hookDir);
  }

  log('green', '✅ Hook created and enabled successfully!');
  return true;
}

// 创建默认的 HOOK.md
function createDefaultHookMd(hookDir) {
  const content = `---
name: unified-memory
description: "Unified Memory v4.0 — 自动记忆抽取、注入与重排"
homepage: https://github.com/mouxangithub/unified-memory
openclaw:
  emoji: "🧠"
  events:
    - "agent_loop:before_prompt_build"
    - "agent_loop:agent_end"
  hooks:
    allowPromptInjection: true
  requires:
    bins: ["node"]
    config: ["workspace.dir"]
---

# Unified Memory Hook v4.0

自动注入相关记忆，自动抽取关键信息。

## 功能

- **before_prompt_build**: 注入相关记忆到 prompt
- **agent_end**: 自动抽取关键信息存入记忆

## 文档

- [English](../workspace/skills/unified-memory/docs/en/README.md)
- [中文](../workspace/skills/unified-memory/docs/zh/README.md)
`;

  fs.writeFileSync(path.join(hookDir, 'HOOK.md'), content);
}

// 创建默认的 handler.js
function createDefaultHandler(hookDir) {
  const content = `#!/usr/bin/env node

/**
 * Unified Memory Hook Handler
 * 
 * 处理 before_prompt_build 和 agent_end 事件
 */

export async function before_prompt_build(context) {
  // 注入相关记忆
  const memories = await context.tools.memory_search({
    query: context.message.text,
    scope: 'USER',
    limit: 5
  });

  if (memories && memories.results && memories.results.length > 0) {
    const memoryContext = memories.results
      .map(m => \`- [\${m.category}] \${m.text}\`)
      .join('\\n');

    return {
      prependContext: \`[Relevant memories]
\${memoryContext}
[/Relevant memories]\`
    };
  }

  return {};
}

export async function agent_end(context) {
  // 自动抽取关键信息
  const message = context.message.text;
  
  if (message.length < 30) return {};
  
  // 检测偏好、决策、事实等
  const patterns = {
    preference: /(?:我喜欢|I like|我讨厌|I hate|习惯)/,
    decision: /(?:决定|decided|选择|chose|要|want)/,
    fact: /(?:完成了|finished|部署了|deployed|安装了|installed)/
  };

  for (const [category, pattern] of Object.entries(patterns)) {
    if (pattern.test(message)) {
      await context.tools.memory_store({
        text: message,
        category: category,
        scope: 'USER',
        importance: 0.7
      });
      break;
    }
  }

  return {};
}
`;

  fs.writeFileSync(path.join(hookDir, 'handler.js'), content);
}

// 主函数
function main() {
  log('blue', '═'.repeat(60));
  log('blue', '  Unified Memory Hook Builder');
  log('blue', '═'.repeat(60));

  // 检查 Node.js 版本
  const nodeVersion = process.version.match(/^v(\d+)/)[1];
  if (nodeVersion < 22) {
    log('red', '⚠️  Node.js 22+ required, current ' + process.version);
    process.exit(1);
  }
  log('green', '✅ Node.js ' + process.version);

  // 构建 Hook
  const success = buildHook();

  if (success) {
    log('green', '');
    log('green', '═'.repeat(60));
    log('green', '  Hook installed successfully! 🎉');
    log('green', '═'.repeat(60));
    log('blue', '');
    log('blue', 'Next steps:');
    log('blue', '  1. Restart OpenClaw gateway: openclaw gateway restart');
    log('blue', '  2. Verify Hook status: openclaw hooks list');
    log('blue', '');
  } else {
    log('yellow', '');
    log('yellow', 'Hook installation skipped. You can manually install later.');
  }
}

main();
