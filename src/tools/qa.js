/**
 * memory_qa - 记忆智能问答
 * 基于相关记忆回答用户问题
 */

import { getAllMemories } from '../storage.js';
import { hybridSearch } from '../fusion.js';
import { log } from '../config.js';

const OLLAMA_URL = process.env.OLLAMA_HOST || 'http://localhost:11434';
const LLM_MODEL = process.env.OLLAMA_LLM_MODEL || 'deepseek-v3.2:cloud';

async function ollamaChat(prompt) {
  try {
    const response = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: LLM_MODEL,
        messages: [{ role: 'user', content: prompt }],
        stream: false
      })
    });
    const data = await response.json();
    return data.message?.content || '抱歉，生成答案失败';
  } catch (err) {
    log('ERROR', `LLM call failed: ${err.message}`);
    return '抱歉，暂时无法连接 LLM 服务';
  }
}

export async function askQuestion({ question }) {
  if (!question) {
    return { content: [{ type: 'text', text: '请提供问题，例如: memory_qa ask --question "我的项目进展如何？"' }] };
  }
  
  log('INFO', `QA: ${question}`);
  
  // Search relevant memories
  const results = await hybridSearch(question, 5, 'hybrid');
  
  if (results.length === 0) {
    return {
      content: [{ type: 'text', text: '抱歉，我没有找到相关的记忆来回答您的问题。' }],
      isError: false
    };
  }
  
  // Build context
  const context = results.map((r, i) => 
    `[${i + 1}] [${r.memory.category}] ${r.memory.text}`
  ).join('\n');
  
  const prompt = `基于以下记忆内容回答用户问题。如果记忆中没有相关信息，请直接说明你不清楚。

用户问题: ${question}

相关记忆：
${context}

请用简洁的语言回答，引用相关记忆的编号。`;
  
  const answer = await ollamaChat(prompt);
  
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        question,
        answer,
        sources: results.map(r => ({
          id: r.memory.id,
          text: r.memory.text.slice(0, 100),
          relevance: Math.round(r.fusionScore * 100) / 100
        }))
      }, null, 2)
    }]
  };
}
