// 最简单的记忆系统 - 立即可用
const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'simple-memories.json');

// 确保文件存在
if (!fs.existsSync(filePath)) {
  fs.writeFileSync(filePath, '[]');
}

// 加载记忆
function loadMemories() {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return [];
  }
}

// 保存记忆
function saveMemories(memories) {
  fs.writeFileSync(filePath, JSON.stringify(memories, null, 2));
}

// 添加记忆
function addMemory(content, tags = []) {
  const memories = loadMemories();
  const memory = {
    id: `m_${Date.now()}`,
    content,
    tags: Array.isArray(tags) ? tags : [tags],
    timestamp: Date.now(),
    date: new Date().toISOString()
  };
  
  memories.push(memory);
  saveMemories(memories);
  return memory;
}

// 搜索记忆
function searchMemories(query) {
  const memories = loadMemories();
  const queryLower = query.toLowerCase();
  
  return memories
    .filter(m => m.content.toLowerCase().includes(queryLower))
    .sort((a, b) => b.timestamp - a.timestamp);
}

// 获取统计
function getStats() {
  const memories = loadMemories();
  const tags = new Set();
  memories.forEach(m => m.tags.forEach(t => tags.add(t)));
  
  return {
    total: memories.length,
    tags: tags.size,
    latest: memories.length > 0 ? new Date(memories[memories.length - 1].timestamp).toLocaleString() : '无'
  };
}

// 立即记录当前会话
addMemory('刘选权询问 unified-memory vs memory-core-plus 对比分析', ['咨询', '对比', '刘选权']);
addMemory('决定并行进行：使用现有系统 + 学习优化', ['决策', '并行', '优化']);
addMemory('创建简单记忆系统，绕过复杂依赖', ['简化', '解决方案', '实践']);

// 导出
module.exports = {
  add: addMemory,
  search: searchMemories,
  stats: getStats,
  filePath
};