// 务实记忆系统 - 最简单可用版本
const fs = require('fs');
const path = require('path');

const MEMORY_FILE = path.join(__dirname, 'practical-memories.json');

// 确保文件存在
if (!fs.existsSync(MEMORY_FILE)) {
  fs.writeFileSync(MEMORY_FILE, '[]');
}

// 加载所有记忆
function load() {
  try {
    return JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
  } catch {
    return [];
  }
}

// 保存记忆
function save(memories) {
  fs.writeFileSync(MEMORY_FILE, JSON.stringify(memories, null, 2));
}

// 添加记忆
function add(content, tags = []) {
  const memories = load();
  const memory = {
    id: `mem_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
    content,
    tags: Array.isArray(tags) ? tags : [tags],
    timestamp: Date.now(),
    date: new Date().toISOString()
  };
  memories.push(memory);
  save(memories);
  return memory;
}

// 搜索记忆
function search(query) {
  const memories = load();
  const queryLower = query.toLowerCase();
  return memories
    .filter(m => m.content.toLowerCase().includes(queryLower))
    .sort((a, b) => b.timestamp - a.timestamp);
}

// 按标签搜索
function searchByTag(tag) {
  const memories = load();
  return memories
    .filter(m => m.tags.includes(tag))
    .sort((a, b) => b.timestamp - a.timestamp);
}

// 获取统计
function stats() {
  const memories = load();
  const allTags = new Set();
  memories.forEach(m => m.tags.forEach(t => allTags.add(t)));
  
  return {
    total: memories.length,
    tags: allTags.size,
    latest: memories.length > 0 ? 
      new Date(memories[memories.length-1].timestamp).toLocaleString('zh-CN') : '无'
  };
}

// 导出
module.exports = { add, search, searchByTag, stats, MEMORY_FILE };